#!/usr/bin/env python3
"""Per-painting stocking coverage; original legs alpha and registration are immutable."""
import argparse, io, json, math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
LANDMARKS=json.loads((ROOT/'dev/hose-landmarks.json').read_text())
def build(base,kind):
 legs=Image.open(ROOT/f'assets/worn/{base}_legs.webp').convert('RGBA');w,h=legs.size
 px=legs.load();out=Image.new('RGBA',(w,h),(255,255,255,0));dst=out.load()
 rows=LANDMARKS[base][kind]
 # Each foot's own silhouette at its calibrated row supplies centre/width.
 spans=[]
 for front,row in enumerate(rows):
  xs=[]
  for sample in sorted(range(h),key=lambda y:abs(y-row)):
   xs=[x for x in range(w) if px[x,sample][3]>=128 and (px[x,sample][0]>=207)==bool(front)]
   if xs:break
  spans.append(((min(xs)+max(xs))/2,max(xs)-min(xs)))
 for y in range(h):
  for x in range(w):
   r,g,b,a=px[x,y]
   if not a:continue
   front=int(r>=207);centre,width=spans[front];u=max(-1.5,min(1.5,2*(x-centre)/max(1,width)))
   top=rows[front]-.09*(x-centre)+3*u*u
   # Soft subpixel knit edge. Alpha is coverage only; skin is clipped once at runtime.
   coverage=max(0,min(1,(y-top+1.5)/3))
   dst[x,y]=(255,255,255,round(255*coverage))
 stream=io.BytesIO();out.save(stream,'WEBP',lossless=True,exact=True,method=6);return stream.getvalue()
def main():
 verify='--verify' in __import__('sys').argv
 for base in LANDMARKS:
  if base.startswith('_'):continue
  for kind in ['knee','thigh']:
   data=build(base,kind);path=ROOT/f'assets/worn/{base}_{kind}.webp'
   if verify:assert path.read_bytes()==data,path
   else:path.write_bytes(data)
  print(base, 'verified' if verify else 'built',flush=True)
if __name__=='__main__':main()
