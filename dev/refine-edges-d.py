#!/usr/bin/env python3
"""Pinned, painting-derived edge repair for edges-d; no geometry resampling."""
import io,json,subprocess,hashlib,sys
from pathlib import Path
from PIL import Image,ImageFilter,ImageChops
from importlib import import_module
components=import_module('clean-maryjane-specks').components
ROOT=Path(__file__).resolve().parents[1]
BASELINE='60f3eb4c1bed0a4f47a98286acb2deaa392d3b5f'
OUT=ROOT/'dev/qa-out/edges-d'
BASES={'ballet':(560,840),'slingback':(590,830),'bowsling':(585,835),'crystalsandal':(550,850)}
REGISTRATION={'ballet_frill':-1,'crystalsandal_frill':2,'crystalsandal_lace':2}
def original(path):return subprocess.check_output(['git','show',f'{BASELINE}:{path}'],cwd=ROOT)
def band(a,r=9):
 s=a.point(lambda v:255 if v>=128 else 0)
 return ImageChops.subtract(s.filter(ImageFilter.MaxFilter(2*r+1)),s.filter(ImageFilter.MinFilter(2*r+1)))
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for base,(y0,y1) in BASES.items():
  for variant in ['', '_frill','_lace']:
   name=base+variant;painting=Image.open(ROOT/f'assets/worn/{name}.webp').convert('RGBA');w,h=painting.size;src=list(painting.getdata())
   legs=Image.open(ROOT/f'assets/worn/{base}_legs.webp').getchannel('A');aligned=Image.new('L',(w,h));aligned.paste(legs,(REGISTRATION.get(name,0),0))
   solid=aligned.point(lambda v:255 if v>=128 else 0);solid=Image.frombytes('L',(w,h),bytes(components(solid.tobytes(),w,h)))
   contact=solid.filter(ImageFilter.MaxFilter(13)).tobytes()
   # Dye changes are additionally restricted to three pixels from the
   # original mask contour, protecting the interiors of narrow straps.
   # Warm material only at this painting's anatomical boundary. Never select
   # neutral satin/bows/counter highlights just because they are near an edge.
   trim=bytes(255 if contact[i] and r-b>=8 and r-g>=2 and pa>=64 and y0<=i//w<=y1 else 0 for i,(r,g,b,pa) in enumerate(src))
   trimim=Image.frombytes('L',(w,h),trim);trimnear=trimim.filter(ImageFilter.MaxFilter(7)).tobytes()
   warm=Image.frombytes('L',(w,h),bytes(round(255*max(0,min(1,(r-b-4)/6))) if contact[i] else 0 for i,(r,g,b,a) in enumerate(src))).filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(.4)).tobytes()
   trimim.save(OUT/f'{name}-true-trim.png')
   for kind in ['mask']+(['sock'] if variant else []):
    path=f'assets/worn/{name}_{kind}.webp';raw=original(path);(OUT/f'{name}_{kind}-before.webp').write_bytes(raw)
    im=Image.open(io.BytesIO(raw)).convert('RGBA');assert im.size==(w,h);a=im.getchannel('A');old=a.tobytes();z=bytearray(old);bp=band(a,3 if kind=='mask' else 9).tobytes()
    if kind=='mask':
     sm=a.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(.35)).tobytes()
     for i,v in enumerate(old):
      if bp[i] and trimnear[i] and y0<=i//w<=y1:
       z[i]=min(v,round(min(v,sm[i])*max(0,min(1,(230-warm[i])/170))))
    else:
     thin=a.point(lambda v:255 if v else 0)
     bp=ImageChops.lighter(Image.frombytes('L',(w,h),bp),ImageChops.subtract(thin.filter(ImageFilter.MaxFilter(19)),thin.filter(ImageFilter.MinFilter(19)))).tobytes()
     keep=components(old,w,h)
     yarn=Image.frombytes('L',(w,h),bytes(round(255*max(0,min(1,(min(g-r,g-b)-2)/10))) for r,g,b,pa in src)).filter(ImageFilter.MedianFilter(3)).tobytes()
     for i,v in enumerate(old):
      if bp[i] and i//w>=y0:
       if not keep[i]:z[i]=0
       elif i//w<=y1:z[i]=min(v,yarn[i])
     final=components(z,w,h)
     for i in range(w*h):
      if bp[i] and i//w>=y0 and not final[i]:z[i]=0
    after=im.copy();after.putalpha(Image.frombytes('L',(w,h),bytes(z)))
    changed=[i for i,(x,y) in enumerate(zip(old,z)) if x!=y]
    assert all(bp[i] and i//w>=y0 and (i//w<=y1 or kind=='sock') for i in changed)
    assert im.convert('RGB').tobytes()==after.convert('RGB').tobytes()
    loss=sum(old[i]>=128 and z[i]<64 and not trimnear[i] for i in range(w*h)) if kind=='mask' else 0
    assert loss==0,(name,loss)
    encoded=io.BytesIO();after.save(encoded,format='WEBP',lossless=True,exact=True)
    if '--check' in sys.argv:assert (ROOT/path).read_bytes()==encoded.getvalue(),path
    else:(ROOT/path).write_bytes(encoded.getvalue())
    Image.frombytes('L',(w,h),bp).save(OUT/f'{name}_{kind}-allowed-band.png')
    rows.append(dict(file=path,size=[w,h],changed_pixels=len(changed),y_range=[y0,h-1 if kind=='sock' else y1],rgb_exact=True,outside_band_exact=True,undyed_beyond_3px_trim=loss,sha256=hashlib.sha256(encoded.getvalue()).hexdigest()))
  print('PASS painting-specific edge / sock repair',base,flush=True)
 (OUT/'mask-verification.json').write_text(json.dumps(dict(baseline=BASELINE,files=rows),indent=2)+'\n')
if __name__=='__main__':main()
