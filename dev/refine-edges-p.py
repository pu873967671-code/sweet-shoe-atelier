#!/usr/bin/env python3
"""Rebuild product upper masks from pinned originals; never edit paintings.

Each last has its own inspected edge extent, warm-trim threshold and feather.
Alpha changes stay in the original three-pixel contour band; the independently
traced neutral footbed bindings alone include their fourth contour pixel.
"""
import hashlib, io, json, subprocess, sys
from collections import deque
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dev/qa-out/edges-p'
BASELINE='b5f06078c3853cb45658737a0570768dd2346cec'
# (source edge ROI, minimum warm chroma, feather radius). Separate calibrations
# retain the low flat welt, rope wedge, raised shafts and hardware contours.
LASTS={
 'flat':((90,235,935,548),16,.30),
 'block':((90,130,935,548),16,.35),
 'kitten':((90,135,935,548),17,.35),
 'stiletto6':((90,140,935,548),16,.45),
 'stiletto9':((90,125,935,548),16,.45),
 'wedge':((90,125,935,548),20,.30),
 'maryjane':((90,235,935,548),15,.35),
 'ballet':((90,160,1000,548),17,.30),
 'slingback':((90,130,935,548),18,.35),
 'loafer':((90,235,935,548),18,.30),
 'platform':((90,120,935,548),16,.60),
 'bootie':((90,110,935,548),17,.40),
 'pearlpump':((90,140,935,548),17,.40),
 'bowsling':((90,130,935,548),19,.30),
 'crystalpump':((90,140,935,548),17,.40),
 'studpump':((90,140,935,548),18,.35),
 'bowmule':((90,260,935,548),19,.30),
 'pearlheel':((90,140,935,548),17,.40),
 'luciteheel':((90,140,935,548),17,.40),
 'crystalsandal':((90,45,950,548),23,.22),
}
# Independently traced centre of the neutral white far-side footbed binding.
# These are source pixels, not a replacement contour or a transformed painting.
RAILS={
 'slingback':[(575,373),(580,368),(600,349),(620,329),(640,310),(660,294),(680,280),(700,267),(720,256),(740,248),(760,241),(770,238)],
 'bowsling':[(578,371),(580,368),(600,349),(620,329),(640,310),(660,294),(680,280),(700,267),(720,256),(733,250)],
}
def true_trim(base,painting):
 # Warm source lining, piping and leather outsole, plus the neutral binding
 # trace. Never infer protected material from the repaired output alpha.
 trim=Image.frombytes('L',painting.size,bytes(255 if r-b>=11 and r-g>=3 and a>128 else 0 for r,g,b,a in painting.getdata()))
 rail=Image.new('L',painting.size)
 if base in RAILS:
  ImageDraw.Draw(rail).line(RAILS[base],fill=255,width=9,joint='curve')
  ImageDraw.Draw(rail).line([(836,223),(850,222),(870,222),(890,223),(905,226),(916,230),(922,234)],fill=255,width=3,joint='curve')
  neutral=Image.frombytes('L',painting.size,bytes(255 if r>210 and r-b<18 and a>128 else 0 for r,g,b,a in painting.getdata()))
  rail=ImageChops.multiply(rail,neutral)
 return ImageChops.lighter(trim,rail),rail
def original(path):return subprocess.check_output(['git','show',f'{BASELINE}:{path}'],cwd=ROOT)
def small_islands(alpha,w,h,limit):
 seen=bytearray(v>0 for v in alpha);removed=bytearray(w*h)
 for i in range(w*h):
  if not seen[i]:continue
  seen[i]=0;queue=deque([i]);group=[]
  while queue:
   j=queue.popleft();group.append(j)
   for k in [j-w,j+w]+([j-1] if j%w else [])+([j+1] if j%w<w-1 else []):
    if 0<=k<w*h and seen[k]:seen[k]=0;queue.append(k)
  if len(group)<=limit:
   for j in group:removed[j]=255
 return removed
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for base,(roi,chroma,feather) in LASTS.items():
  path=f'assets/shoe2d/{base}_upper.webp';raw=original(path)
  before=Image.open(io.BytesIO(raw)).convert('RGBA');painting=Image.open(ROOT/f'assets/shoe2d/{base}_base.webp').convert('RGBA')
  assert before.size==painting.size==(1024,640)
  alpha=before.getchannel('A');old=alpha.tobytes();z=bytearray(old)
  solid=alpha.point(lambda v:255 if v>=128 else 0)
  band=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(7)),solid.filter(ImageFilter.MinFilter(7)))
  bp=band.tobytes();smooth=alpha.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(feather)).tobytes()
  trim,rail=true_trim(base,painting);near=trim.filter(ImageFilter.MaxFilter(7)).tobytes()
  rail_soft=rail.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.35)).tobytes()
  platform_warm=None
  if base=='platform':
   # Feather the source leather boundary, rather than thresholding each
   # brown antialias pixel into another visible stair on the platform welt.
   material=bytes(round(255*max(0,min(1,(r-b-(30 if i//1024>=450 else chroma-5))/5))) if r-g>=(12 if i//1024>=450 else 3) else 0 for i,(r,g,b,a) in enumerate(painting.getdata()))
   platform_warm=Image.frombytes('L',painting.size,material).filter(ImageFilter.GaussianBlur(.55)).tobytes()
  # Only these traced 6–8px binding strips need the fourth contour pixel.
  rail_band=ImageChops.multiply(rail.filter(ImageFilter.MaxFilter(3)),ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(9)),solid.filter(ImageFilter.MinFilter(9))))
  allowed=ImageChops.lighter(band,rail_band);bp=allowed.tobytes()
  pixels=painting.getdata();x0,y0,x1,y1=roi;warm_count=0
  islands=small_islands(old,1024,640,{'maryjane':200,'slingback':40,'bowsling':40}.get(base,0)) if base in ['maryjane','slingback','bowsling'] else None
  for i,(r,g,b,pa) in enumerate(pixels):
   x,y=i%1024,i//1024
   if not(bp[i] and x0<=x<x1 and y0<=y<y1):continue
   # The original upper is neutral; piping, insole and leather soles are warm.
   # Full warm material loses dye; mixed antialias pixels fade continuously.
   # Lower upper shadows can be slightly warm too. Below the vamp, only
   # leather-brown sole pixels qualify; never expose beige toe-shadow islands.
   threshold=max(chroma,35) if y>=450 else chroma
   warm=max(0,min(1,(r-b-(threshold-5))/5)) if r-g>=(12 if y>=450 else 3) else 0
   if platform_warm is not None:warm=platform_warm[i]/255
   if base=='crystalsandal':
    # Keep the original shaded arch: its warm white leather is upper, not
    # cream trim. Calibrate straps and forefoot separately from that arch.
    if y>=275 and x>525:
     continue
   value=round(smooth[i]*(1-warm))
   # A soft contour may only extend into opaque neutral upper painting.
   # Never grow dye into the transparent silhouette or warm sole/lining.
   if value>old[i] and (pa<250 or r-b>=chroma-5):value=old[i]
   z[i]=value
   if islands and islands[i]:z[i]=0
   if rail_soft[i]:z[i]=round(z[i]*(1-rail_soft[i]/255))
   # Anti-regression: retain any previously dyed pixel away from real source
   # trim, even faint codec/antialias tails removed by the median filter.
   if not near[i] and (old[i]>0 and z[i]==0 or old[i]>=64 and old[i]-z[i]>=32):z[i]=old[i]
   if old[i] and warm:warm_count+=1
  after=before.copy();after.putalpha(Image.frombytes('L',before.size,bytes(z)))
  changed=[i for i in range(len(old)) if old[i]!=z[i]]
  assert all(bp[i] and x0<=i%1024<x1 and y0<=i//1024<y1 for i in changed)
  assert before.convert('RGB').tobytes()==after.convert('RGB').tobytes()
  encoded=io.BytesIO();after.save(encoded,format='WEBP',lossless=True,exact=True)
  if '--check' in sys.argv:assert (ROOT/path).read_bytes()==encoded.getvalue(),path
  else:(ROOT/path).write_bytes(encoded.getvalue())
  allowed.save(OUT/f'{base}-allowed-band.png');trim.save(OUT/f'{base}-true-trim.png')
  delta=ImageChops.difference(alpha,after.getchannel('A'));delta.save(OUT/f'{base}-alpha-delta.png')
  rows.append(dict(base=base,file=path,roi=roi,chroma=chroma,feather=feather,changed_pixels=len(changed),warm_edge_pixels=warm_count,size=list(before.size),rgb_exact=True,contour_band_px=4 if base in RAILS else 3,sha256=hashlib.sha256(encoded.getvalue()).hexdigest()))
  print('PASS product mask',base,len(changed),flush=True)
 (OUT/'mask-verification.json').write_text(json.dumps(dict(status='PASS',baseline=BASELINE,files=rows),indent=2)+'\n')
if __name__=='__main__':main()
