import glob,sys,os,numpy as np,cv2
from PIL import Image
# "back-plate" pass: patch over-keyed see-through spots inside the hair by painting a solid layer behind the frame
src,dst=sys.argv[1],sys.argv[2]; os.makedirs(dst,exist_ok=True)
for f in sorted(glob.glob(src+'/s_*.webp')):
    o=np.asarray(Image.open(f).convert('RGBA')).astype(np.float32)
    rgb,A=o[...,:3],o[...,3]/255
    solid=(A>0.55).astype(np.uint8)
    n,lab,st,_c=cv2.connectedComponentsWithStats(1-solid,connectivity=4)
    top=np.where(solid.any(1))[0].min()
    border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]))
    r_,g_,b_=rgb[...,0],rgb[...,1],rgb[...,2]
    skin=(r_-g_>20)&(r_-g_<75)&(g_-b_>5)&(g_>120)
    fill=np.zeros_like(solid,bool)
    for i in range(1,n):
        if i in border or st[i,4]>1500: continue
        m=lab==i; ring=(cv2.dilate(m.astype(np.uint8),np.ones((7,7),np.uint8))>0)&~m&(solid>0)
        # real see-through gaps (finger/chin) are skin-ringed and sizeable; every other enclosed hole is over-keying
        cy=_c[i][1]
        # keep only the finger/chin gap (upper body); waist/arm slivers below get filled
        if cy<top+330 and st[i,4]>=60 and ring.sum() and skin[ring].mean()>=0.5: continue
        fill|=m
    # narrow notches open to the outside (e.g. sliver between tape measure and waist): close them
    notch=(cv2.morphologyEx(solid,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))>0)&(solid==0)
    yy=np.arange(solid.shape[0])[:,None]
    fill|=notch&(yy>top+330)   # body only; keep hair tips / face silhouette untouched
    # also semi-transparent pixels in hair interior (not on outer silhouette)
    S=(solid>0)|fill
    S=cv2.morphologyEx(S.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    din=cv2.distanceTransform(S,cv2.DIST_L2,3)
    back=(din>2.5)|fill
    # backplate colour: inpaint from solid neighbours
    src8=np.clip(rgb,0,255).astype(np.uint8)
    holes=((A<0.9)&back).astype(np.uint8)
    bp=cv2.inpaint(src8,holes,5,cv2.INPAINT_TELEA).astype(np.float32)
    bA=back.astype(np.float32); bA=cv2.GaussianBlur(bA,(0,0),0.7)*back.astype(np.float32)+ back*0
    bA=np.maximum(bA,back*1.0)
    # composite frame over backplate
    outA=A+bA*(1-A)
    outC=(rgb*A[...,None]+bp*bA[...,None]*(1-A[...,None]))/np.maximum(outA,1e-4)[...,None]
    out=np.dstack([np.clip(outC,0,255),np.clip(outA*255,0,255)]).astype(np.uint8)
    Image.fromarray(out,'RGBA').save(dst+'/'+os.path.basename(f),quality=92)
