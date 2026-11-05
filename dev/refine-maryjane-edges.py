#!/usr/bin/env python3
"""Refine only the nine-pixel boundary band of the three Mary Jane dye mattes.

Pinned input makes the lossless output reproducible and prevents cumulative blur.
The registered painting supplies material separation: neutral satin is dyeable,
warm ivory/skin and green source yarn are not. No painting is resampled.
"""
import io,json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageFilter,ImageChops
ROOT=Path(__file__).resolve().parents[1]
BASELINE='50e6c3f8681498386d58c3c7a50f6a03d97b1254'
OUT=ROOT/'dev/qa-out/maryjane-edges'
NAMES=['maryjane','maryjane_frill','maryjane_lace']
def original(path):
 return subprocess.check_output(['git','show',f'{BASELINE}:{path}'],cwd=ROOT)
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for name in NAMES:
  path=f'assets/worn/{name}_mask.webp';raw=original(path);(OUT/(name+'-before.webp')).write_bytes(raw)
  before=Image.open(io.BytesIO(raw)).convert('RGBA');painting=Image.open(ROOT/f'assets/worn/{name}.webp').convert('RGBA')
  legs=Image.open(ROOT/'assets/worn/maryjane_legs.webp').convert('RGBA').getchannel('A')
  aligned=Image.new('L',before.size);aligned.paste(legs,(-1 if name!='maryjane' else 0,0))
  contact=aligned.point(lambda v:255 if v>=128 else 0).filter(ImageFilter.MaxFilter(19)).tobytes()
  a=before.getchannel('A');solid=a.point(lambda v:255 if v>=128 else 0)
  # 9 px on either side of the existing contour. Restrict to collar/strap/vamp.
  band=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(19)),solid.filter(ImageFilter.MinFilter(19)))
  near=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid.filter(ImageFilter.MinFilter(5)))
  smooth=a.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(.45))
  alpha=bytearray(a.tobytes());bp=band.tobytes();np=near.tobytes();sm=smooth.tobytes();src=list(painting.getdata());w,h=before.size
  colour=bytearray(w*h)
  for i,(r,g,b,pa) in enumerate(src):
   warm=max(0,min(1,(r-b-4)/6));green=max(0,min(1,(min(g-r,g-b)-1)/6))
   colour[i]=round(255*max(warm,green))
  material=Image.frombytes('L',before.size,bytes(colour)).filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(.55)).tobytes()
  for i,(r,g,b,pa) in enumerate(src):
   y=i//w
   if not 630<=y<=810 or not bp[i] or not contact[i]:continue
   # Soft material transition follows painted antialias pixels; pure cream
   # piping and source yarn have exactly zero dye / motif ownership.
   coverage=max(0,min(1,(230-material[i])/170))
   value=sm[i] if np[i] else alpha[i]
   alpha[i]=min(alpha[i],round(value*coverage))
  after=before.copy();after.putalpha(Image.frombytes('L',before.size,bytes(alpha)))
  changed=[i for i,(x,y) in enumerate(zip(a.tobytes(),alpha)) if x!=y]
  assert changed and all(bp[i] and 630<=i//w<=810 for i in changed)
  assert all(x[:3]==y[:3] for x,y in zip(before.getdata(),after.getdata()))
  after.save(ROOT/path,lossless=True,exact=True)
  assert Image.open(ROOT/path).convert('RGBA').tobytes()==after.tobytes()
  band.save(OUT/(name+'-allowed-band.png'))
  rows.append(dict(file=path,changed_pixels=len(changed),size=list(before.size),outside_band_exact=True,rgb_exact=True,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()))
 (OUT/'mask-verification.json').write_text(json.dumps(dict(baseline=BASELINE,max_boundary_distance=9,y_range=[630,810],files=rows),indent=2)+'\n')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
