import glob,sys,numpy as np
from PIL import Image, ImageFilter
src,dst=sys.argv[1],sys.argv[2]; out=[]
bg=np.array([0,60,255.])
def box(x,k=1):
    p=np.pad(x,[(k,k),(k,k)]+[(0,0)]*(x.ndim-2),mode='edge'); c=p.cumsum(0).cumsum(1)
    c=np.pad(c,[(1,0),(1,0)]+[(0,0)]*(x.ndim-2)); n=2*k+1
    return (c[n:,n:]-c[:-n,n:]-c[n:,:-n]+c[:-n,:-n])/(n*n)
for f in sorted(glob.glob(src+'/f_*.png')):
    a=np.asarray(Image.open(f).convert('RGB')).astype(float)
    # denoise compression: light median on chroma via slight blur for key only
    ab=np.asarray(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(float)
    m=ab[...,2]-np.maximum(ab[...,0],ab[...,1])
    al=np.clip(1-(m-25)/120,0,1)
    A=Image.fromarray((al*255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.9))
    al=np.asarray(A).astype(float)/255
    alc=np.clip(al,0.15,1)[...,None]
    fg=np.clip((a-(1-alc)*bg)/alc,0,255)
    lim=np.maximum(fg[...,0],fg[...,1]); fg[...,2]=np.minimum(fg[...,2],lim)
    core=(np.asarray(Image.fromarray((al*255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)))>250).astype(float)
    c=a*core[...,None]; w=core.copy()
    for _ in range(6):
        C=box(c,1); Wt=box(w,1); fill=(w<0.5)&(Wt>1e-3)
        c[fill]=C[fill]/Wt[fill,None]; w=np.where(fill,1.0,w)
    band=(core<1)&(w>0)
    fg=np.where(band[...,None],c,a)
    o=Image.fromarray(np.dstack([fg.astype(np.uint8),(al*255).astype(np.uint8)]),'RGBA')
    n=f.split('/')[-1].replace('f_','s_').replace('.png','.webp'); o.save(dst+'/'+n,quality=92); out.append(o)
fr=[]
for o in out:
    c=Image.new('RGBA',o.size,(250,240,235,255));c.alpha_composite(o);fr.append(c.convert('RGB'))
fr[0].save(dst+'/preview.webp',save_all=True,append_images=fr[1:],duration=125,loop=0,quality=90)
W,H=out[0].size
for n,col in [('light',(250,240,235)),('dark',(60,60,70))]:
    c=Image.new('RGBA',out[3].size,col+(255,));c.alpha_composite(out[3]);c.crop((int(W*.15),0,int(W*.7),int(H*.55))).save(dst+'/check_'+n+'.png')
