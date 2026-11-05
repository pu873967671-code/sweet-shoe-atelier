#!/usr/bin/env python3
"""Pinned pre-edges-p / repaired native Chromium evidence and real UI checks."""
import importlib,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/edges-p3'
repair=importlib.import_module('refine-edges-p3')
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if '--ui' in sys.argv:
  ui=importlib.import_module('edges-p-ui');ui.OUT=OUT
  if '--rails-only' in sys.argv:ui.survey.BASES=['slingback','bowsling']
  ui.main();return
 baseline=OUT/'baseline';baseline.mkdir(exist_ok=True)
 for base in repair.BASES:
  (baseline/f'{base}_upper.webp').write_bytes(repair.pinned(repair.BEFORE,f'assets/shoe2d/{base}_upper.webp'))
 survey=importlib.import_module('edges-p-check');survey.OUT=OUT
 if '--after-only' not in sys.argv:
  sys.argv=[sys.argv[0],'--before'];survey.main()
 sys.argv=[sys.argv[0]];survey.main()
 supplemental_crops()
def supplemental_crops():
 contact=[]
 for base,box,label in [('loafer',(300,240,550,440),'tongue'),('bowmule',(210,300,560,535),'bow-loops')]:
  for case in range(3):
   cuts=[]
   for phase in ['before','after']:
    im=Image.open(OUT/f'{base}-{case}-{phase}.png').convert('RGBA').crop(box)
    cuts.append(im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST))
   sheet=Image.new('RGB',(cuts[0].width*2,cuts[0].height+24),'#e8ddd4');draw=ImageDraw.Draw(sheet)
   draw.text((8,6),f'{base} case {case}: pre-edges-p c69f3e06 / AFTER (3x)',fill='#302838')
   for i,im in enumerate(cuts):sheet.paste(im,(i*im.width,24),im)
   sheet.save(OUT/f'{base}-{case}-{label}-3x.png')
   if case==1:sheet.thumbnail((1600,750));contact.append(sheet)
 sheet=Image.new('RGB',(1600,sum(im.height for im in contact)),'#e8ddd4');top=0
 for im in contact:sheet.paste(im,(0,top));top+=im.height
 sheet.save(OUT/'contact.jpg',quality=95)
if __name__=='__main__':main()
