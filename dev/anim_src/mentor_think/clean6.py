import glob,sys,numpy as np,cv2
from PIL import Image
sys.path.insert(0,'.')
def dil(m,k): return cv2.dilate(m.astype(np.uint8),np.ones((k,k),np.uint8))>0
for f in sorted(glob.glob(sys.argv[1]+'/s_*.webp')):
    a=np.asarray(Image.open(f).convert('RGBA')).copy(); rgb=a[...,:3].astype(float); al=a[...,3].astype(float)
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]; ratio=g/np.maximum(r,1)
    sat=(r-np.maximum(g,b))/np.maximum(r,1)
    hair=(sat>0.38)&(r>150)&(al>240)&(ratio<0.62)
    mint=dil((g>r+3)&(g>b),7)
    edge=dil(al<60,21)
    n,lab,st,cen=cv2.connectedComponentsWithStats(((g>r+3)&(g>b)).astype(np.uint8))
    reg=np.zeros_like(hair)
    for i in sorted([i for i in range(1,n) if st[i,4]>800],key=lambda i:cen[i][0])[:2]:
        ys,xs=np.where(lab==i); t=ys.min(); xt=int(xs[ys<t+6].mean())
        reg[max(t-40,0):t+16,max(xt-45,0):xt+45]=True
    pencil=dil((r>170)&(g>130)&(b<110)&(ratio>0.6),9)
    zone=((dil(hair,31)&edge)|reg)&~pencil&~mint
    # muddy: orange/brown/olive, darker than skin, not hair-red
    mud=zone&~hair&(al>20)&(ratio>0.48)&(ratio<1.15)&(r<215)&(b<0.95*g)&~((r>212)&(g>150))
    m=cv2.GaussianBlur(mud.astype(np.float32),(0,0),1.0); m[mint]=0
    lum=0.3*r+0.59*g+0.11*b
    base=np.array([190,78,64.]); bl=base@np.array([.3,.59,.11])
    new=np.clip(base*np.clip(lum/bl,0.55,1.3)[...,None],0,255)
    rgb=rgb*(1-m[...,None])+new*m[...,None]
    a[...,:3]=rgb.astype(np.uint8)
    Image.fromarray(a,'RGBA').save(f,quality=92)
