import glob,sys,os,numpy as np,cv2
from PIL import Image
# black-screen key: flood-fill near-black from border, soft alpha in edge band, un-premultiply against black
src,dst=sys.argv[1],sys.argv[2]; os.makedirs(dst,exist_ok=True)
files=sorted(glob.glob(src+'/f_*.png'))
def irismask(p):
    a=np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
    fgr=np.where((a.max(2)>14).any(1))[0]; top=fgr.min()
    yy=np.arange(a.shape[0])[:,None]
    return (a[...,1]>a[...,0]+30)&(a[...,1]>a[...,2]+5)&(yy<top+230)&(yy>top+60)
IR=[irismask(p) for p in files]; cnt=[m.sum() for m in IR]
good=[j for j,c in enumerate(cnt) if c>80]
for fi,f in enumerate(files):
    a=np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
    ab=cv2.GaussianBlur(a,(0,0),0.6)
    d=ab.max(2)                      # distance from black
    near=(d<14).astype(np.uint8)
    n,lab=cv2.connectedComponents(near)
    border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]))-{0}
    st=np.bincount(lab.ravel())
    keep=[i for i in range(1,n) if i in border]
    bg=np.isin(lab,keep)
    # enclosed holes (between legs, chin/finger, hair gaps): interior near-black blobs away from the eyes
    # blink frames have no visible iris: borrow eye position from the nearest frames that do
    near=sorted(good,key=lambda j:abs(j-fi))[:2] if cnt[fi]<=80 else [fi]
    iris=np.zeros_like(IR[fi])
    for j in near: iris|=IR[j]
    eyes=cv2.dilate(iris.astype(np.uint8),np.ones((61,61),np.uint8))>0
    # thick dark blobs inside the eye zone that touch the background are leftover bg, not lashes (lashes are thin)
    thick=cv2.morphologyEx(((d<40)&eyes).astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n3,lab3=cv2.connectedComponents(thick)
    bgd=cv2.dilate(bg.astype(np.uint8),np.ones((5,5),np.uint8))>0
    for i in range(1,n3):
        m=lab3==i
        if bgd[m].any(): bg|=cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&(d<60)
    n2,lab2,st2,_=cv2.connectedComponentsWithStats((d<26).astype(np.uint8))
    for i in range(1,n2):
        if st2[i,4]<12 or bg[lab2==i].mean()>0.5: continue
        m=lab2==i
        if eyes[m].any(): continue
        bg|=m
    bg=cv2.morphologyEx(bg.astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))>0
    fg=~bg
    din=cv2.distanceTransform(fg.astype(np.uint8),cv2.DIST_L2,3)
    dout=cv2.distanceTransform(bg.astype(np.uint8),cv2.DIST_L2,3)
    # over-black matting in the edge band: C = alpha*F, F = interior colour propagated outward
    core=(din>6)&(d>70)
    w=cv2.GaussianBlur(core.astype(np.float32),(0,0),5)+1e-4
    F=np.dstack([cv2.GaussianBlur(a[...,c]*core,(0,0),5) for c in range(3)])/w[...,None]
    for _ in range(3):  # widen where the 5px kernel had no support
        w2=cv2.GaussianBlur((w>0.02).astype(np.float32),(0,0),9)+1e-4
        F2=np.dstack([cv2.GaussianBlur(F[...,c]*(w>0.02),(0,0),9) for c in range(3)])/w2[...,None]
        F=np.where((w>0.02)[...,None],F,F2); w=np.maximum(w,w2*(w2>0.02))
    am=np.clip((a*F).sum(2)/np.maximum((F*F).sum(2),1),0,1)
    dark=am<0.85
    soft=np.where(dark,np.minimum(np.clip((d-22)/60,0,1),np.clip((am-0.3)/0.55,0,1)**1.5),np.clip((d-22)/60,0,1))
    band=(din<=8)|((d<80)&~eyes)|((din<=16)&(d<120)&~eyes)   # also near-black slivers between strands that aren't border-connected
    al=np.where(band,soft,1.0)
    al=np.where(bg,soft*(dout<2),al)
    al=cv2.erode(al.astype(np.float32),np.ones((2,2),np.uint8)); al=cv2.GaussianBlur(al,(0,0),0.6)
    ac=np.clip(al,0.15,1)[...,None]
    rgb=np.where((band&dark)[...,None],np.clip(F,0,255),np.clip(a/ac,0,255))
    o=np.dstack([rgb,al*255]).astype(np.uint8)
    Image.fromarray(o,'RGBA').save(dst+'/'+os.path.basename(f).replace('f_','s_').replace('.png','.webp'),quality=92)
