#!/usr/bin/env python3
"""Restore dyed source edges; keep edges-p only on source-located real trim.

Both inputs are pinned so rebuilding never compounds mask edits. Source part
masks locate lining/binding/outsole; source RGB alone cannot identify material.
"""
import hashlib, io, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dev/qa-out/edges-p3'
BEFORE='c69f3e06'
EDGES_P='04531ea5'
BASES=['flat','block','kitten','stiletto6','stiletto9','wedge','maryjane','ballet','slingback','loafer','platform','bootie','pearlpump','bowsling','crystalpump','studpump','bowmule','pearlheel','luciteheel','crystalsandal']
def pinned(commit,path):
 return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
def rgba(raw):return Image.open(io.BytesIO(raw)).convert('RGBA')
def true_trim(base):
 # Original semantic part masks are independent of every repaired upper.
 def part(name):return rgba(pinned(BEFORE,f'assets/shoe2d/{base}_{name}.webp')).getchannel('A')
 painting=rgba(pinned(BEFORE,f'assets/shoe2d/{base}_base.webp'))
 lining=ImageChops.lighter(part('insole'),part('binding')).point(lambda v:255 if v>=64 else 0).filter(ImageFilter.MaxFilter(3))
 sole=part('sole').point(lambda v:255 if v>=64 else 0).filter(ImageFilter.MaxFilter(7))
 warm=Image.frombytes('L',painting.size,bytes(255 if r-b>=20 and r-g>=6 else 0 for r,g,b,a in painting.getdata()))
 trim=ImageChops.lighter(lining,ImageChops.multiply(sole,warm))
 # Keep the independently traced neutral far footbed piping from edges-p.
 # It is absent from the older generic insole part masks on these two lasts.
 rails={
  'slingback':[(575,373),(580,368),(600,349),(620,329),(640,310),(660,294),(680,280),(700,267),(720,256),(740,248),(760,241),(770,238)],
  'bowsling':[(578,371),(580,368),(600,349),(620,329),(640,310),(660,294),(680,280),(700,267),(720,256),(733,250)],
 }
 if base in rails:
  rail=Image.new('L',painting.size);draw=ImageDraw.Draw(rail)
  draw.line(rails[base],fill=255,width=9,joint='curve')
  draw.line([(836,223),(850,222),(870,222),(890,223),(905,226),(916,230),(922,234)],fill=255,width=3,joint='curve')
  neutral=Image.frombytes('L',painting.size,bytes(255 if r>210 and r-b<18 and a>128 else 0 for r,g,b,a in painting.getdata()))
  rail=ImageChops.multiply(rail,neutral).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.35)).point(lambda v:255 if v else 0)
  trim=ImageChops.lighter(trim,rail)
 # These source contours belong to upper material, even where a generic
 # insole/binding trace touches their edge. No geometric mask is used to
 # draw the shoe: these regions only protect the original alpha unchanged.
 protect=Image.new('L',painting.size);d=ImageDraw.Draw(protect)
 if base=='loafer':d.polygon([(90,440),(90,350),(420,235),(485,235),(548,430),(548,455)],fill=255)
 if base=='bowmule':d.rectangle((200,300,555,450),fill=255)
 return ImageChops.subtract(trim,protect)
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for base in BASES:
  name=f'assets/shoe2d/{base}_upper.webp'
  before=rgba(pinned(BEFORE,name));previous=rgba(pinned(EDGES_P,name));a=before.getchannel('A').tobytes();p=previous.getchannel('A').tobytes();trim=true_trim(base);t=trim.tobytes()
  z=bytes(old if new<old and not allowed else new for old,new,allowed in zip(a,p,t))
  result=previous.copy();result.putalpha(Image.frombytes('L',before.size,z))
  raw=io.BytesIO();result.save(raw,format='WEBP',lossless=True,exact=True)
  if '--check' in sys.argv:assert (ROOT/name).read_bytes()==raw.getvalue(),name
  else:(ROOT/name).write_bytes(raw.getvalue())
  trim.save(OUT/f'{base}-true-trim.png')
  restored=sum(x!=y for x,y in zip(p,z));kept=sum(x>y for x,y in zip(a,z))
  rows.append(dict(base=base,restored_dyed_pixels=restored,retained_trim_cleanup_pixels=kept,remaining_dye_loss_outside_trim=sum(x>y and not allow for x,y,allow in zip(a,z,t)),sha256=hashlib.sha256(raw.getvalue()).hexdigest()))
  print('PASS',base,'restored',restored,'retained trim',kept,flush=True)
 (OUT/'mask-counts.json').write_text(json.dumps(dict(status='PASS',baseline=BEFORE,edges_p=EDGES_P,bases=rows),indent=2)+'\n')
if __name__=='__main__':main()
