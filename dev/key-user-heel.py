#!/usr/bin/env python3
"""Extract the approved heel rear source without changing the immutable PNG.

Only background removal and edge decontamination; no anatomy painting/warp.
The colour-key seed excludes neutral floor shadow, then enclosed highlights
are filled and the connected skin silhouette receives a subpixel soft edge.
"""
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw
import hashlib, json
from collections import deque
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/src-user-legs-20261029/candidates/leg-rear-heel-candidate-v2.png'
OUT=ROOT/'dev/user-heel-derived'

def build():
 OUT.mkdir(parents=True,exist_ok=True)
 digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
 im=Image.open(SOURCE).convert('RGB'); w,h=im.size; pix=list(im.getdata())
 # Skin retains red chroma even at its white-background antialias. The
 # neutral grey-brown cast shadow has substantially less chroma.
 seed=bytearray(w*h)
 for i,(r,g,b) in enumerate(pix):
  if r-g>=(20 if i//w>=1200 else 9) and r-b>=(25 if i//w>=1200 else 15): seed[i]=255
 # Fill every enclosed highlight; background stays connected to frame edges.
 outside=bytearray(w*h); todo=deque()
 for x in range(w):
  for y in (0,h-1):
   i=y*w+x
   if not seed[i] and not outside[i]:outside[i]=1;todo.append(i)
 for y in range(h):
  for x in (0,w-1):
   i=y*w+x
   if not seed[i] and not outside[i]:outside[i]=1;todo.append(i)
 while todo:
  i=todo.popleft();x=i%w;y=i//w
  for j in ((i-1 if x else -1),(i+1 if x+1<w else -1),(i-w if y else -1),(i+w if y+1<h else -1)):
   if j>=0 and not seed[j] and not outside[j]:outside[j]=1;todo.append(j)
 mask=Image.frombytes('L',(w,h),bytes(255 if not outside[i] else 0 for i in range(w*h)))
 # A single connected organic source contour. Remove
 # isolated key noise by retaining the connected component at the shin.
 raw=list(mask.getdata()); connected=bytearray(w*h); todo=deque([450*w+430]);connected[450*w+430]=255
 while todo:
  i=todo.popleft();x=i%w;y=i//w
  for j in ((i-1 if x else -1),(i+1 if x+1<w else -1),(i-w if y else -1),(i+w if y+1<h else -1)):
   if j>=0 and raw[j] and not connected[j]:connected[j]=255;todo.append(j)
 mask=Image.frombytes('L',(w,h),bytes(connected)).filter(ImageFilter.GaussianBlur(.55))
 alpha=list(mask.getdata()); output=Image.new('RGBA',(w,h)); result=[]
 for i,(r,g,b) in enumerate(pix):
  a=alpha[i]
  if a and a<255:
   # Replace white-matted edge RGB with the nearest interior skin sample.
   # Sample a nearby solid source pixel before removing the matte;
   # saturated skin edges must never inherit neutral floor shadow.
   x,y=i%w,i//w
   nearby=[]
   for dy in range(-3,4):
    for dx in range(-3,4):
     xx,yy=x+dx,y+dy
     if 0<=xx<w and 0<=yy<h and connected[yy*w+xx]:
      nearby.append((dx*dx+dy*dy,pix[yy*w+xx]))
   if nearby:r,g,b=min(nearby,key=lambda z:z[0])[1]
   result.append((r,g,b,a))
  else: result.append((r,g,b,a))
 output.putdata(result); target=OUT/'rear-heel-v2.png';output.save(target)
 sheet=Image.new('RGB',(w*2,h),'white')
 for offset,bg in [(0,'#f7eee8'),(w,'#272432')]:
  tile=Image.new('RGBA',(w,h),bg);tile.alpha_composite(output);sheet.paste(tile.convert('RGB'),(offset,0))
 sheet.resize((768,683)).save(OUT/'extraction-light-dark.jpg',quality=94)
 report={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':digest,'derivative':str(target.relative_to(ROOT)),'derivative_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bounds':output.getbbox(),'anatomy_landmarks':{'ball':[325,1290],'toe_tip':[188,1283],'heel_seat':[538,1085]},'method':'connected chroma key; enclosed-highlight fill; neutral floor-shadow rejection; 0.55px soft edge; white matte decontamination'}
 (OUT/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
 print(json.dumps(report,indent=2))
 return target
if __name__=='__main__':build()
