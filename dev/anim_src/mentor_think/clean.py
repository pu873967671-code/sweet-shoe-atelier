import glob,sys,numpy as np
from PIL import Image, ImageFilter
d=sys.argv[1]
for f in sorted(glob.glob(d+'/s_*.webp')):
    im=Image.open(f).convert('RGBA'); a=np.asarray(im).astype(float)
    rgb=a[...,:3]; al=a[...,3]
    A=Image.fromarray(al.astype(np.uint8))
    near=np.asarray(A.filter(ImageFilter.MinFilter(25)))<200   # within ~12px of edge
    med=np.asarray(Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.MedianFilter(11))).astype(float)
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    redctx=(med[...,0]-np.maximum(med[...,1],med[...,2]))>35
    dirty=near&redctx&(al>0)&((np.maximum(g,b)>r-35)|(b>g+8))
    dirty=np.asarray(Image.fromarray((dirty*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)))>0
    dirty&=near&redctx
    rgb[dirty]=med[dirty]
    # second pass: low-alpha bluish/greenish haze anywhere → drop
    haze=(al<160)&((b>r+5)|(g>r+5))&redctx
    al=np.where(haze,0,al)
    Image.fromarray(np.dstack([rgb,al]).astype(np.uint8),'RGBA').save(f,quality=92)
    print(f.split('/')[-1],int(dirty.sum()),int(haze.sum()))
# pass 2: bluish/greyish tips at hair edges -> nearest hair colour
def box(x,k=2):
    p=np.pad(x,[(k,k),(k,k)]+[(0,0)]*(x.ndim-2),mode='edge'); c=p.cumsum(0).cumsum(1)
    c=np.pad(c,[(1,0),(1,0)]+[(0,0)]*(x.ndim-2)); n=2*k+1
    return (c[n:,n:]-c[:-n,n:]-c[n:,:-n]+c[:-n,:-n])/(n*n)
for f in sorted(glob.glob(d+'/s_*.webp')):
    a=np.asarray(Image.open(f).convert('RGBA')).astype(float); rgb=a[...,:3]; al=a[...,3]
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    hair=((r-np.maximum(g,b))>45)&(al>240)
    zone=np.asarray(Image.fromarray((hair*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(21)))>0
    edge=np.asarray(Image.fromarray(al.astype(np.uint8)).filter(ImageFilter.MinFilter(15)))<128
    bad=zone&edge&(al>0)&(~hair)&((b>g-2)|((r-np.maximum(g,b))<25))&~((r>215)&(g>195))
    c=rgb*hair[...,None]; w=hair.astype(float)
    for _ in range(10):
        C=box(c);W=box(w);fill=(w<0.5)&(W>1e-3); c[fill]=C[fill]/W[fill,None]; w=np.where(fill,1.0,w)
    ok=bad&(w>0); rgb[ok]=c[ok]
    Image.fromarray(np.dstack([rgb,al]).astype(np.uint8),'RGBA').save(f,quality=92)
