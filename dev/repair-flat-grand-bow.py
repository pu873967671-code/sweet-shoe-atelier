#!/usr/bin/env python3
"""Clean the product Grand bow extraction, preserving its painted satin.

The hand-traced perimeter discards source-background slivers on the loops and
white fringe at the tail tip. Supersampling gives the new edge a smooth alpha;
nearest opaque satin cleans the colour of the retained antialiased edge.
The worn camera and original shoe remain unchanged.
"""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
path = root / 'assets/shoe2d/accessories'
scale = 4
# Cubic contours follow the actual painted loops and hanging tails in source
# coordinates; the join between the two tails stays gently indented.
segments = [
 ((847,211),(849,199),(869,190),(886,191)),
 ((886,191),(894,180),(897,161),(908,153)),
 ((908,153),(919,145),(928,149),(933,158)),
 ((933,158),(939,170),(943,184),(946,195)),
 ((946,195),(956,195),(959,207),(954,222)),
 ((954,222),(963,235),(985,266),(989,282)),
 ((989,282),(989,296),(984,313),(979,323)),
 ((979,323),(974,319),(968,313),(965,311)),
 ((965,311),(966,339),(965,369),(962,381)),
 ((962,381),(949,369),(931,352),(917,337)),
 ((917,337),(914,323),(915,305),(916,291)),
 ((916,291),(910,289),(905,287),(900,289)),
 ((900,289),(895,295),(891,295),(887,290)),
 ((887,290),(876,277),(866,253),(859,239)),
 ((859,239),(853,227),(847,219),(847,211)),
]
points=[]
for a,b,c,d in segments:
 for i in range(25):
  t=i/24; u=1-t
  points.append(tuple(round(scale*(u**3*a[j]+3*u*u*t*b[j]+3*u*t*t*c[j]+t**3*d[j])) for j in range(2)))
mask=Image.new('L',(1024*scale,640*scale)); ImageDraw.Draw(mask).polygon(points,fill=255)
mask=mask.resize((1024,640),Image.Resampling.LANCZOS)
# Keep the original coverage, and clean weak edge pixels with nearby satin.
source=Image.open(root/'dev/heelbow-source/flat_decoration_big-original.webp').convert('RGBA')
pix=source.load(); alpha=mask.load()
result=Image.new('RGBA',source.size); out=result.load()
for y in range(145,390):
 for x in range(840,995):
  if not alpha[x,y]: continue
  r,g,b,a=pix[x,y]
  if a<245:
   candidates=[]
   for dy in range(-5,6):
    for dx in range(-5,6):
     if 0<=x+dx<1024 and 0<=y+dy<640 and pix[x+dx,y+dy][3]>=245:
      candidates.append((dx*dx+dy*dy,x+dx,y+dy))
   if candidates:
    _,sx,sy=min(candidates); r,g,b,_=pix[sx,sy]
  out[x,y]=(r,g,b,min(a,alpha[x,y]))
result.save(path/'flat_decoration_big.webp',lossless=True,method=6)
# This tint is a coverage mask; it must track exactly the new fabric contour.
tint=Image.new('RGBA',source.size,(255,255,255,0)); tint.putalpha(result.getchannel('A'))
tint.save(path/'flat_decoration_big_tint.webp',lossless=True,method=6)
