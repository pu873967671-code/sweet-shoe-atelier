#!/usr/bin/env python3
"""Pinned, per-painting edge repair for the five edges-a bases only.

All changes are within nine source pixels of an original alpha boundary.
Dye RGB and sock luminance remain exact; no painting or geometry is altered.
"""
import io,json,subprocess,hashlib,sys
from pathlib import Path
from PIL import Image,ImageFilter,ImageChops
from importlib import import_module
components=import_module('clean-maryjane-specks').components
ROOT=Path(__file__).resolve().parents[1]
BASELINE='83fb1675031e2e1f0ab1c62af3181979ce1d0fba'
OUT=ROOT/'dev/qa-out/edges-a'
# Each range is read from that last's own collar and counter, not a shared trace.
BASES={'flat':(625,815),'block':(620,825),'kitten':(610,830),'stiletto6':(610,825),'wedge':(620,825)}
def original(path):return subprocess.check_output(['git','show',f'{BASELINE}:{path}'],cwd=ROOT)
def band(alpha,radius=9):
 solid=alpha.point(lambda v:255 if v>=128 else 0)
 return ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(radius*2+1)),solid.filter(ImageFilter.MinFilter(radius*2+1)))
def main():
 OUT.mkdir(parents=True,exist_ok=True);report=[]
 for base,(y0,y1) in BASES.items():
  for variant in ['', '_frill','_lace']:
   name=base+variant;painting=Image.open(ROOT/f'assets/worn/{name}.webp').convert('RGBA');w,h=painting.size;src=list(painting.getdata())
   legs=Image.open(ROOT/f'assets/worn/{base}_legs.webp').convert('RGBA').getchannel('A')
   registration={'kitten':-1}.get(base,0) if variant else 0
   aligned=Image.new('L',(w,h));aligned.paste(legs,(registration,0))
   solid=aligned.point(lambda v:255 if v>=128 else 0)
   solid=Image.frombytes('L',(w,h),bytes(components(solid.tobytes(),w,h)))
   contact=solid.filter(ImageFilter.MaxFilter(19)).tobytes()
   # Actual cream/skin/yarn material in this painting supplies its own edge.
   reject=bytes(round(255*max(max(0,min(1,(r-b-4)/6)),max(0,min(1,(min(g-r,g-b)-1)/6)))) for r,g,b,a in src)
   material=Image.frombytes('L',(w,h),reject).filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(.45)).tobytes()
   for kind in ['mask']+(['sock'] if variant else []):
    path=f'assets/worn/{name}_{kind}.webp';raw=original(path);(OUT/f'{name}_{kind}-before.webp').write_bytes(raw)
    im=Image.open(io.BytesIO(raw)).convert('RGBA');assert im.size==(w,h)
    a=im.getchannel('A');old=a.tobytes();alpha=bytearray(old);allowed=band(a);bp=allowed.tobytes()
    near=band(a,2).tobytes();smooth=a.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(.4)).tobytes()
    if kind=='sock':
     yarn=bytes(round(255*max(0,min(1,(min(g-r,g-b)-2)/10))) for r,g,b,pa in src)
     yarn=Image.frombytes('L',(w,h),yarn).filter(ImageFilter.MedianFilter(3)).tobytes()
     keep=components(old,w,h)
     # Detached sole reflections have their own tiny original contour.
     thin=a.point(lambda v:255 if v else 0)
     islands=ImageChops.subtract(thin.filter(ImageFilter.MaxFilter(19)),thin.filter(ImageFilter.MinFilter(19))).tobytes()
     bp=bytes(max(x,y) for x,y in zip(bp,islands))
     allowed=Image.frombytes('L',(w,h),bp)
    for i,v in enumerate(old):
     if kind=='sock' and i//w>=y0 and bp[i] and not keep[i]:
      alpha[i]=0;continue
     if not y0<=i//w<=y1 or not bp[i] or not contact[i]:continue
     if kind=='mask':
      coverage=max(0,min(1,(230-material[i])/170))
      alpha[i]=min(v,round((smooth[i] if near[i] else v)*coverage))
     else:alpha[i]=min(v,yarn[i])
    if kind=='sock':
     final=components(alpha,w,h)
     for i,v in enumerate(alpha):
      if i//w>=y0 and bp[i] and not final[i]:alpha[i]=0
    after=im.copy();after.putalpha(Image.frombytes('L',(w,h),bytes(alpha)))
    changed=[i for i,(a,b) in enumerate(zip(old,alpha)) if a!=b]
    assert all(bp[i] and y0<=i//w and (i//w<=y1 or kind=='sock') for i in changed)
    assert im.convert('RGB').tobytes()==after.convert('RGB').tobytes()
    encoded=io.BytesIO();after.save(encoded,format='WEBP',lossless=True,exact=True)
    if '--check' in sys.argv:assert (ROOT/path).read_bytes()==encoded.getvalue(),path
    else:(ROOT/path).write_bytes(encoded.getvalue())
    assert Image.open(ROOT/path).convert('RGBA').tobytes()==after.tobytes()
    allowed.save(OUT/f'{name}_{kind}-allowed-band.png')
    report.append(dict(file=path,size=[w,h],changed_pixels=len(changed),band_radius=9,y_range=[y0,h-1 if kind=='sock' else y1],outside_band_exact=True,rgb_exact=True,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()))
 (OUT/'mask-verification.json').write_text(json.dumps(dict(baseline=BASELINE,files=report),indent=2)+'\n')
 print('PASS 25 scoped lossless masks, exact RGB and outside-band pixels',flush=True)
if __name__=='__main__':main()
