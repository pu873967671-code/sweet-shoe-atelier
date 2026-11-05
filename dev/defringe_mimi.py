import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
def fix(src,dst,band_px=4,sigma=3.0,mix=0.9):
    im=np.array(Image.open(src).convert('RGBA')).astype(np.float32)
    a=im[...,3]
    core=ndi.binary_erosion(a>=250,iterations=2).astype(np.float32)
    w=ndi.gaussian_filter(core,sigma)+1e-6
    fill=np.stack([ndi.gaussian_filter(im[...,c]*core,sigma)/w for c in range(3)],-1)
    inside=ndi.binary_erosion(a>=128,iterations=band_px)
    band=((a>0)&~inside&(w>0.02))[...,None]
    # protect legitimately bright cream/white highlight? keep mix <1 so detail survives
    out=im.copy()
    out[...,:3]=np.where(band,im[...,:3]*(1-mix)+fill*mix,im[...,:3])
    Image.fromarray(np.clip(out,0,255).astype(np.uint8),'RGBA').save(dst,'WEBP',quality=95,method=6)
if __name__=='__main__':
    for s in sys.argv[1:]: fix(s,s)

def fix2(src,dst):
    """pass 1 band fill, then recolour residual yellow-green strand pixels near the silhouette edge from nearby non-green core colour"""
    fix(src,dst)
    im=np.array(Image.open(dst).convert('RGBA')).astype(np.float32)
    r,g,b,a=[im[...,i] for i in range(4)]
    edge=(a>0)&~ndi.binary_erosion(a>=128,iterations=6)
    green=edge&(g>r+8)&(g>b+45)&(a>0)
    green=ndi.binary_dilation(green,iterations=1)&(a>0)
    ok=((a>=250)&~green&ndi.binary_erosion(a>=250,iterations=1)).astype(np.float32)
    w=ndi.gaussian_filter(ok,5)+1e-6
    fill=np.stack([ndi.gaussian_filter(im[...,c]*ok,5)/w for c in range(3)],-1)
    m=(green&(w>0.01))[...,None]
    im[...,:3]=np.where(m,fill,im[...,:3])
    Image.fromarray(np.clip(im,0,255).astype(np.uint8),'RGBA').save(dst,'WEBP',quality=95,method=6)
