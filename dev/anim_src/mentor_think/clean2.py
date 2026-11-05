import glob,sys,numpy as np
from PIL import Image, ImageFilter
d=sys.argv[1]
def box(x,k=2):
    p=np.pad(x,[(k,k),(k,k)]+[(0,0)]*(x.ndim-2),mode='edge'); c=p.cumsum(0).cumsum(1)
    c=np.pad(c,[(1,0),(1,0)]+[(0,0)]*(x.ndim-2)); n=2*k+1
    return (c[n:,n:]-c[:-n,n:]-c[n:,:-n]+c[:-n,:-n])/(n*n)
for f in sorted(glob.glob(d+'/s_*.webp')):
    a=np.asarray(Image.open(f).convert('RGBA')).astype(float); rgb=a[...,:3]; al=a[...,3]
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    sat=(r-np.maximum(g,b))/np.maximum(r,1)
    hair=(sat>0.38)&(r>150)&(al>240)
    zone=np.asarray(Image.fromarray((hair*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(21)))>0
    edge=np.asarray(Image.fromarray(al.astype(np.uint8)).filter(ImageFilter.MinFilter(25)))<128
    skin=(r>200)&(g>140)&(g<200)&(b>110)&(sat<0.38)&(sat>0.12)   # face/ear skin keep
    cream=(r>205)&(g>190)
    bad=zone&edge&(al>0)&(~hair)&(~cream)&(~skin)
    c=rgb*hair[...,None]; w=hair.astype(float)
    for _ in range(14):
        C=box(c);W=box(w);fill=(w<0.5)&(W>1e-3); c[fill]=C[fill]/W[fill,None]; w=np.where(fill,1.0,w)
    ok=bad&(w>0)
    # keep shading: scale bled colour by luminance ratio (clamped)
    lum=lambda x:(0.3*x[...,0]+0.59*x[...,1]+0.11*x[...,2])
    k=np.clip(lum(rgb)/np.maximum(lum(c),1),0.75,1.1)[...,None]
    rgb=np.where(ok[...,None],np.clip(c*k,0,255),rgb)
    # tighten hair rim by ~1.5px to drop leftover dirty fringe
    hz=zone&edge
    alE=np.asarray(Image.fromarray(al.astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))).astype(float)
    al=np.where(hz,np.minimum(al,alE),al)
    r2,g2,b2=rgb[...,0],rgb[...,1],rgb[...,2]
    blu=(b2>g2+5)&(b2>r2)&(al<235)
    blu=np.asarray(Image.fromarray((blu*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)))>0
    al=np.where(blu&(al<250),0,al)
    olive=zone&edge&(np.abs(r2-g2)<40)&(r2<190)&(al<250)&(~hair)
    al=np.where(olive,al*0.3,al)
    Image.fromarray(np.dstack([rgb,al]).astype(np.uint8),'RGBA').save(f,quality=92)
