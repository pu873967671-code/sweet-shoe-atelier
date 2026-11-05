#!/usr/bin/env python3
"""Restore original painted nacre inside fixed product bezels; preserve exterior/chain.
Pillow-only, no artwork synthesis. Run after legacy height/platform exporters.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, json, math, shutil
ROOT=Path(__file__).resolve().parents[2]
BACK=ROOT/'dev/fitting-polish/pearl-nacre-source';OUT=ROOT/'qa/pearl-nacre'
BACK.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
FAMILIES=['flat','block','kitten','wedge','stiletto6','stiletto9','platform']
CORES={'flat':(260,374,306,416),'block':(296,372,347,420),'kitten':(292,388,337,428),'wedge':(264,350,321,393)}
report={'status':'PASS','provenance':'Original retained gpt-image product edits; semantic nacre alpha repair only','families':{}}
records=json.loads((ROOT/'dev/accessory-edits/extraction-report.json').read_text())['layers']
aligned={};masks={}
for family,box in CORES.items():
 record=next(r for r in records if r['name']==family+'_charm_pearl')
 im=Image.open(ROOT/'dev/accessory-edits'/f'{family}_charm_pearl.png').convert('RGBA').resize((1024,640),Image.Resampling.LANCZOS)
 aligned[family]=im.transform((1024,640),Image.Transform.AFFINE,tuple(v for row in record['warp'] for v in row),Image.Resampling.BICUBIC)
 mask=Image.new('L',(1024*4,640*4));ImageDraw.Draw(mask).ellipse(tuple(v*4 for v in box),fill=255)
 masks[family]=mask.resize((1024,640),Image.Resampling.LANCZOS)
review=Image.new('RGB',(1200,len(FAMILIES)*210),'#f9f0e7');d=ImageDraw.Draw(review)
for index,family in enumerate(FAMILIES):
 path=ROOT/'assets/shoe2d/accessories'/f'{family}_charm_pearl.webp';backup=BACK/path.name
 if not backup.exists():shutil.copyfile(path,backup)
 old=Image.open(backup).convert('RGBA');new=old.copy();op=old.load();np=new.load();bbox=old.getbbox();changed=[];semantic=Image.new('L',old.size);sp=semantic.load()
 base='kitten' if family.startswith('stiletto') else 'block' if family=='platform' else family
 source=aligned[base];mask=masks[base]
 columns={x:[y for y in range(bbox[1],bbox[3]) if op[x,y][3]>0] for x in range(bbox[0],bbox[2])}
 rows={y:[x for x in range(bbox[0],bbox[2]) if op[x,y][3]>0] for y in range(bbox[1],bbox[3])}
 for x in range(bbox[0],bbox[2]):
  for y in range(bbox[1],bbox[3]):
   sy=float(y)
   if family.startswith('stiletto'):
    height=int(family[-1]);delta=15 if x<=285 and height==6 else 20 if x<=285 else (15 if height==6 else 20)+(x-285)/309*(14-(15 if height==6 else 20));sy-=delta
   elif family=='platform':sy+=52*(1-min(1,max(0,(x-300)/550)))
   # Reuse the exporter's fixed per-column shift at the measured source
   # pixel. ECC registration above uses bicubic sampling; mounts never move.
   yy=round(sy);alpha=mask.getpixel((x,yy)) if 0<=yy<640 else 0
   if not alpha:continue
   rgb=source.getpixel((x,yy))[:3]
   # Original key-green and lavender upper lie outside nacre, including
   # its rotated rim. They must never enter restored matte pixels.
   if rgb[1]>max(rgb[0],rgb[2])+20:continue
   sp[x,y]=alpha
   if alpha>op[x,y][3]:
    np[x,y]=(*rgb,alpha);changed.append((x,y))
 assert new.getbbox()==bbox
 assert all(np[x,y]==op[x,y] for x in range(1024) for y in range(640) if not sp[x,y])
 new.save(path,lossless=True,exact=True,method=6);semantic.save(OUT/f'{family}-nacre-mask.png')
 report['families'][family]={'changedAlphaPixels':len(changed),'bbox':bbox,'coreSource':base,'coreEllipse':CORES[base],'beforeSHA256':hashlib.sha256(backup.read_bytes()).hexdigest(),'afterSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'semanticMask':str((OUT/f'{family}-nacre-mask.png').relative_to(ROOT)),'outsideSemanticExact':True,'fullBBoxExact':True}
 for j,bg in enumerate(['#f9f0e7','#25382f']):
  for k,im in enumerate([old,new]):
   tile=Image.new('RGBA',(300,200),bg);crop=im.crop((bbox[0]-5,bbox[1]-5,bbox[2]+5,bbox[3]+5));crop=crop.resize((crop.width*2,crop.height*2),Image.Resampling.LANCZOS);tile.alpha_composite(crop,(35,45));review.paste(tile.convert('RGB'),(j*600+k*300,index*210));d.text((j*600+k*300+10,index*210+10),family+(' before' if k==0 else ' after'),fill='white' if j else '#25382f')
review.save(OUT/'before-after-light-dark.png')
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
