import glob,sys,os,numpy as np,cv2
from PIL import Image
src,dst=sys.argv[1],sys.argv[2]; os.makedirs(dst,exist_ok=True)
for f in sorted(glob.glob(src+'/f_*.png')):
    a=np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
    ab=cv2.GaussianBlur(a,(0,0),0.6)
    d=(255-ab).max(2)
    near=(d<16).astype(np.uint8)
    n,lab=cv2.connectedComponents(near)
    border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]))-{0}
    st=np.bincount(lab.ravel())
    keep=[i for i in range(1,n) if i in border or st[i]>25]
    bg=np.isin(lab,keep)
    bg=cv2.morphologyEx(bg.astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))>0
    fg=~bg
    din=cv2.distanceTransform(fg.astype(np.uint8),cv2.DIST_L2,3)
    band=(din<=3)
    soft=np.clip((d-12)/45,0,1)
    al=np.where(band,soft,1.0)
    al=np.where(bg,np.clip((d-12)/45,0,1)*(cv2.distanceTransform(bg.astype(np.uint8),cv2.DIST_L2,3)<2),al)
    al=cv2.GaussianBlur(al.astype(np.float32),(0,0),0.5)
    ac=np.clip(al,0.2,1)[...,None]
    rgb=np.clip((a-(1-ac)*255)/ac,0,255)
    o=np.dstack([rgb,al*255]).astype(np.uint8)
    Image.fromarray(o,'RGBA').save(dst+'/'+os.path.basename(f).replace('f_','s_').replace('.png','.webp'),quality=92)
