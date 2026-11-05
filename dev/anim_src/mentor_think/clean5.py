import glob,sys,numpy as np,cv2
from PIL import Image
def dil(m,k): return cv2.dilate(m.astype(np.uint8),np.ones((k,k),np.uint8))>0
def mask(a):
    rgb=a[...,:3].astype(float); al=a[...,3].astype(float)
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    sat=(r-np.maximum(g,b))/np.maximum(r,1); ratio=g/np.maximum(r,1)
    hair=(sat>0.38)&(r>150)&(al>240)&(ratio<0.62)
    mint=(g>r+3)&(g>b)
    mintd=dil(mint,5)
    edge=dil(al<60,15)
    n,lab,st,cen=cv2.connectedComponentsWithStats(mint.astype(np.uint8))
    big=[i for i in range(1,n) if st[i,4]>800]
    reg=np.zeros_like(mint)
    if big:
        L=min(big,key=lambda i:cen[i][0]); ys,xs=np.where(lab==L); t=ys.min(); xt=int(xs[ys<t+6].mean())
        reg[max(t-35,0):t+14, max(xt-40,0):xt+40]=True
    pencil=dil((r>170)&(g>130)&(b<110)&(ratio>0.6),9)
    near=((dil(hair,25)&edge)|reg)&~pencil
    olive=(r<185)&(ratio>0.56)&(ratio<1.1)&(b<0.82*g)&(al>40)
    dirty=near&olive&~mintd&~hair
    dirty=dil(dirty,3)&~mintd&~hair&(al>40)&(r<215)&(ratio>0.5)&(ratio<1.1)&(b<0.9*g)
    tint=(reg|(dil(hair,25)&edge))&~pencil&~mintd&~hair&(al>40)&(r<212)&(ratio>0.5)&(ratio<1.1)&(b<0.92*g)
    return dirty,tint
if __name__=='__main__':
  for f in sorted(glob.glob(sys.argv[1]+'/s_*.webp')):
    a=np.asarray(Image.open(f).convert('RGBA')).copy()
    m,t=mask(a)
    bgr=cv2.cvtColor(a[...,:3],cv2.COLOR_RGB2BGR)
    out=cv2.inpaint(bgr,(m*255).astype(np.uint8),5,cv2.INPAINT_TELEA)
    rgb=cv2.cvtColor(out,cv2.COLOR_BGR2RGB).astype(float)
    lum=rgb@np.array([.3,.59,.11]); base=np.array([192,84,72.]); bl=base@np.array([.3,.59,.11])
    new=np.clip(base*np.clip(lum/bl,0.6,1.3)[...,None],0,255)
    tm=cv2.GaussianBlur(t.astype(np.float32),(0,0),0.8)*0.85
    tm[dil((a[...,1].astype(int)>a[...,0].astype(int)+3),5)]=0
    rgb=rgb*(1-tm[...,None])+new*tm[...,None]
    a[...,:3]=rgb.astype(np.uint8)
    Image.fromarray(a,'RGBA').save(f,quality=92)
