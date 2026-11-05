#!/usr/bin/env python3
"""Build honest stiletto6 browser/seat evidence without changing source artwork.

Native leg canvases include a 1500px calf extension: crop at OY before placing
onto the original shoe. All contour metrics use the *unoccluded* source alpha.
"""
from pathlib import Path
import argparse,json,math,runpy
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OY=1500
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--qa',type=Path,default=ROOT/'qa/stiletto6-seat-20261030/after')
ap.add_argument('--before',type=Path,default=ROOT/'qa/stiletto6-seat-20261030/before')
ap.add_argument('--calibration',type=Path,default=ROOT/'qa/heel-collar-20261030/calibration/stiletto6')
ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();a.qa.mkdir(exist_ok=True,parents=True)
BG='#f7f1eb';INK='#423642';CYAN='#00a7b4';PINK='#ed2b80'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',29)
sheet=Image.new('RGB',(2000,3070),BG);d=ImageDraw.Draw(sheet)
def flatten(im):
 bg=Image.new('RGBA',im.size,BG);bg.alpha_composite(im.convert('RGBA'));return bg.convert('RGB')
def tile(im,box,label):
 x,y,w,h=box;d.text((x,y),label,font=font,fill=INK)
 if isinstance(im,Path):im=Image.open(im).convert('RGBA')
 im=flatten(im);im.thumbnail((w,h-30),Image.Resampling.LANCZOS)
 sheet.paste(im,(x+(w-im.width)//2,y+30+(h-30-im.height)//2))
base=Image.open(ROOT/'assets/shoe2d/stiletto6_base.webp').convert('RGBA')
product=Image.open(a.qa/'stiletto6-product-1920.png').convert('RGBA')
insole=np.asarray(Image.open(ROOT/'assets/shoe2d/stiletto6_insole.webp').convert('RGBA'))[:,:,3]
metrics={}
cfg=json.loads((ROOT/'dev/fitting-calibration/stiletto6.json').read_text())
def composite(side,kind='white'):
 im=product.copy();leg=Image.open(a.qa/f'stiletto6-{kind}-{side}-native.png').convert('RGBA')
 im.alpha_composite(leg.crop((0,OY,1024,OY+640)));return im

def overlay(side,phase):
 path=(a.before if phase=='before' else a.calibration)/f'{side}-unoccluded.png'
 if path.exists():
  foot=Image.open(path).convert('RGBA')
 else:
  config_path=a.before/'calibration.json' if phase=='before' else ROOT/'dev/fitting-calibration/stiletto6.json'
  spec=json.loads(config_path.read_text())[side]
  transform=runpy.run_path(str(ROOT/'dev/build-calibrated-user-legs.py'))['transform']
  foot=transform(Image.open(ROOT/spec['source']).convert('RGBA'),spec.get('placement_override') or spec['placement'])
 fa=np.asarray(foot)[:,:,3]
 im=Image.new('RGBA',base.size,BG);im.alpha_composite(base)
 ghost=foot.crop((0,OY,1024,OY+640));ghost.putalpha(ghost.getchannel('A').point(lambda x:round(x*.20)));im.alpha_composite(ghost)
 draw=ImageDraw.Draw(im);ip=[];fp=[];res=[]
 for x in range(1024):
  iy=np.flatnonzero(insole[:,x]>128);fy=np.flatnonzero(fa[:,x]>128)
  if len(iy):ip.append((x,int(iy[-1])))
  if len(fy):
   y=int(fy[-1])-OY
   if 0<=y<640:
    fp.append((x,y))
    if len(iy):res.append(y-int(iy[-1]))
 for points,color in [(ip,CYAN),(fp,PINK)]:
  run=[]
  for p in points:
   if run and p[0]-run[-1][0]>1:
    if len(run)>1:draw.line(run,fill=color,width=4)
    run=[]
   run.append(p)
  if len(run)>1:draw.line(run,fill=color,width=4)
 r=np.asarray(res);m={'samples':len(res),'median_signed_px':float(np.median(r)),'median_absolute_px':float(np.median(np.abs(r))),'p95_absolute_px':float(np.percentile(np.abs(r),95))}
 metrics[f'{side}_{phase}']=m
 im=flatten(im);im.save(a.qa/f'{side}-{phase}-sole-overlay.jpg',quality=95)
 return im

d.text((20,14),'Stiletto6 | front / approved raised-heel rear | physical seating review',font=title,fill=INK)
d.text((20,54),'Actual /usr/bin/chromium, 390 x 844 and 1920 x 1080; original rigid shoes; white and bare anatomy.',font=font,fill=INK)
tile(a.qa/'stiletto6-white-390.png',(20,92,230,500),'390 x 844')
tile(a.qa/'stiletto6-white-1920.png',(270,92,610,500),'1920 x 1080')
pair_path=a.qa/'stiletto6-white-1920-pair.png'
pair=Image.open(pair_path).convert('RGBA')
# Keep both complete shoes in the actual canvas crop. A narrow central crop
# hides the rear toe and defeats the side-by-side pose comparison.
pair=pair.crop((int(pair.width*.08),int(pair.height*.04),int(pair.width*.94),int(pair.height*.96)))
tile(pair,(900,92,650,500),'Actual fitting pair / canvas crop')
tile(ROOT/'assets/src-user-legs-20261029/pair-reference-user.png',(1570,92,410,500),'User pair reference')
for col,side in enumerate(['front','rear']):
 x=20+col*990
 whole=composite(side)
 whole.save(a.qa/f'{side}-white-shoe-native.png')
 tile(whole,(x,615,970,555),f'{side.title()} / actual product + runtime white foot')
 # Exact 3x, not a calf-only crop: foot was shifted by OY above.
 crop=flatten(whole.crop((575,230,875,430))).resize((900,600),Image.Resampling.LANCZOS)
 crop.save(a.qa/f'{side}-white-collar-3x.png')
 d.text((x,1185),f'{side.title()} collar + arch / exact 3x source pixels',font=font,fill=INK)
 sheet.paste(crop,(x+35,1218))
 bare=flatten(composite(side,'bare').crop((635,100,895,335))).resize((520,470),Image.Resampling.LANCZOS)
 bare.save(a.qa/f'{side}-bare-counter-2x.png')
 # Retain a separate 2x heel-counter artifact for native inspection.
for col,(side,phase) in enumerate([('front','before'),('front','after'),('rear','before'),('rear','after')]):
 x=20+col*495;im=overlay(side,phase)
 tile(im,(x,1850,475,335),f'{side.title()} / {phase} / sole overlay')
 m=metrics[f'{side}_{phase}']
 d.text((x,2190),f'Visible-edge separation: median {m["median_signed_px"]:.1f}px',font=small,fill=INK)
 d.text((x,2214),f'Absolute median {m["median_absolute_px"]:.1f}px',font=small,fill=INK)
 d.text((x,2238),f'Absolute p95 {m["p95_absolute_px"]:.1f}px',font=small,fill=INK)

def seat_overlay(side):
 """Plot measured anatomy points separately from a manually traced hidden seat.

 The public insole mask follows the visible opening edge, not the hidden
 physical support plane. Keep that original contour visible, and do not
 replace measured full-source contours with a target or inferred curve.
 """
 spec=cfg[side];landmarks=spec.get('sole_seat_landmarks',[])
 im=Image.new('RGBA',base.size,BG);im.alpha_composite(base)
 foot=Image.open(a.calibration/f'{side}-unoccluded.png').convert('RGBA')
 ghost=foot.crop((0,OY,1024,OY+640));ghost.putalpha(ghost.getchannel('A').point(lambda v:round(v*.24)));im.alpha_composite(ghost)
 draw=ImageDraw.Draw(im);targets=[];actual=[];records=[]
 p=spec.get('placement_override') or spec['placement'];r=math.radians(p['degrees']);c,s=math.cos(r),math.sin(r)
 for landmark in landmarks:
  sx,sy=landmark['source'];tx,ty=landmark['seat']
  x=p['scale']*(c*sx-s*sy)+p['tx'];y=p['scale']*(s*sx+c*sy)+p['ty']-OY
  targets.append((tx,ty));actual.append((x,y))
  records.append(dict(name=landmark['name'],source=[sx,sy],target=[tx,ty],actual=[x,y],dx=x-tx,dy=y-ty,distance_px=math.hypot(x-tx,y-ty)))
 if len(targets)>1:draw.line(targets,fill='#df8b11',width=4)
 if len(actual)>1:draw.line(actual,fill=PINK,width=3)
 for item,(x,y),(tx,ty) in zip(records,actual,targets):
  draw.line([(tx,ty),(x,y)],fill='#423642',width=2)
  draw.rectangle((tx-6,ty-6,tx+6,ty+6),outline='#df8b11',width=3)
  draw.ellipse((x-5,y-5,x+5,y+5),fill=PINK)
  draw.text((tx-25,ty+10),item['name'],font=small,fill=INK)
 if not records:draw.text((100,540),'No physical-seat landmarks supplied; no fit claim.',font=font,fill=INK)
 metrics[f'{side}_physical_seat']=dict(method='Actual source landmarks transformed by the saved similarity placement; target seat is manually traced inside original sidewall, not insole alpha boundary.',landmarks=records)
 im=flatten(im);im.save(a.qa/f'{side}-physical-seat-overlay.jpg',quality=95)
 return im,records

for col,side in enumerate(['front','rear']):
 x=20+col*990;im,records=seat_overlay(side)
 tile(im,(x,2280,970,470),f'{side.title()} / hidden physical seat guide + measured anatomy')
 for row,item in enumerate(records):
  d.text((x,2760+row*23),f'{item["name"]}: dx {item["dx"]:+.1f}px / dy {item["dy"]:+.1f}px / distance {item["distance_px"]:.1f}px',font=small,fill=INK)
d.text((20,2850),'Cyan: original insole-layer visible lower edge. Pink: actual full-foot alpha contour. Their separation is NOT a physical-seat residual.',font=small,fill=INK)
d.text((20,2880),'Orange squares / line: manually traced ball, arch and heel seat inside the rigid sidewall. Pink dots: transformed source anatomy landmarks.',font=small,fill=INK)
d.text((20,2910),'The hidden seat guide is a developer calibration, not visible source pixels. Per-landmark distances remain separate from alpha-edge statistics.',font=small,fill=INK)
d.text((20,2940),'Original alpha threshold (>128), original before/after contours, and original measured separations retained; no target snapping or hidden residual.',font=small,fill=INK)
d.text((20,2970),'Whole-source translation / uniform scale / rotation only; own front / rear near-collar masks. Original user sources and rigid shoe pixels unchanged.',font=small,fill=INK)
d.text((20,3000),'Separate exact 3x arch/collar and 2x bare heel-counter images accompany this sheet. Developer visual inspection; supervisor review pending.',font=small,fill=INK)
a.output.parent.mkdir(exist_ok=True,parents=True);sheet.save(a.output,quality=94,optimize=True)
(a.qa/'sole-overlay-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(a.output);print(json.dumps(metrics,indent=2))
