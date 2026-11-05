#!/usr/bin/env python3
"""Actual stiletto6 browser/native evidence; independently measured contour overlay."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'qa/heel-collar-20261030'
OUT=ROOT/'qa/contact/stiletto6-20261030-0230.jpg'
BG='#f7f1eb'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',27)
sheet=Image.new('RGB',(1600,1580),BG);d=ImageDraw.Draw(sheet)
def tile(path,box,label):
 x,y,w,h=box;d.text((x,y),label,font=font,fill='#423642')
 im=Image.open(path).convert('RGBA');im.thumbnail((w,h-27),Image.Resampling.LANCZOS)
 bg=Image.new('RGBA',im.size,BG);bg.alpha_composite(im)
 sheet.paste(bg.convert('RGB'),(x+(w-im.width)//2,y+27+(h-27-im.height)//2))
def native_crop(side,box,x,y,label):
 im=Image.open(QA/f'stiletto6-white-{side}-native.png').convert('RGBA').crop(box)
 bg=Image.new('RGBA',im.size,BG);bg.alpha_composite(im)
 im=bg.convert('RGB').resize((im.width*3,im.height*3),Image.Resampling.LANCZOS)
 d.text((x,y),label,font=font,fill='#423642');sheet.paste(im,(x,y+27))
d.text((18,12),'Stiletto6 | independent front / rear fit and collar review',font=title,fill='#423642')
d.text((18,48),'Actual Chromium 390 x 844 / 1920 x 1080; white hosiery; approved heel-raised rear source.',font=font,fill='#423642')
tile(QA/'stiletto6-white-390.png',(18,82,190,410),'390 x 844')
tile(QA/'stiletto6-white-1920.png',(230,82,540,410),'1920 x 1080')
tile(QA/'stiletto6-white-1920-pair.png',(790,82,460,410),'Actual pair')
tile(ROOT/'assets/src-user-legs-20261029/pair-reference-user.png',(1270,82,310,410),'User pair reference')
native_crop('front',(590,305,760,405),18,510,'Front arch / collar - exact 3x')
native_crop('rear',(590,305,760,405),545,510,'Rear arch / collar - exact 3x')
native_crop('front',(360,445,530,545),1072,510,'Ball / sole - exact 3x')
# Every plotted point comes from current image alpha; no idealized line is used.
base=Image.open(ROOT/'assets/shoe2d/stiletto6_base.webp').convert('RGBA')
insole=np.asarray(Image.open(ROOT/'assets/shoe2d/stiletto6_insole.webp').convert('RGBA'))[:,:,3]
report={}
for col,side in enumerate(['front','rear']):
 im=Image.new('RGBA',base.size,'#eee5df');im.alpha_composite(base)
 foot=Image.open(QA/f'calibration/stiletto6/{side}-unoccluded.png').convert('RGBA')
 fa=np.asarray(foot)[:,:,3]
 overlay=foot.crop((0,1500,1024,2140));overlay.putalpha(overlay.getchannel('A').point(lambda a:int(a*.22)));im.alpha_composite(overlay)
 q=ImageDraw.Draw(im)
 ip=[];fp=[];residual=[]
 for x in range(1024):
  iy=np.flatnonzero(insole[:,x]>128);fy=np.flatnonzero(fa[:,x]>128)
  if len(iy):ip.append((x,int(iy[-1])))
  if len(fy):
   yy=int(fy[-1])-1500
   if 0<=yy<640:fp.append((x,yy))
   if len(iy) and 0<=yy<640:residual.append(yy-int(iy[-1]))
 for points,color in [(ip,'#00a7b4'),(fp,'#ed2b80')]:
  run=[]
  for p in points:
   if run and p[0]-run[-1][0]>1:
    if len(run)>1:q.line(run,fill=color,width=4)
    run=[]
   run.append(p)
  if len(run)>1:q.line(run,fill=color,width=4)
 im.resize((770,481),Image.Resampling.LANCZOS).convert('RGB').save(QA/f'stiletto6-{side}-actual-sole-overlay.jpg',quality=95)
 tile(QA/f'stiletto6-{side}-actual-sole-overlay.jpg',(18+col*790,885,770,510),f'{side.title()} - actual insole / unoccluded foot contour')
 report[side]=dict(samples=len(residual),median_signed_gap_px=float(np.median(residual)),p95_absolute_gap_px=float(np.percentile(np.abs(residual),95)))
 d.text((18+col*790,1410),f"Measured shared-x residual: median {report[side]['median_signed_gap_px']:.1f}px; |gap| p95 {report[side]['p95_absolute_gap_px']:.1f}px",font=small,fill='#423642')
d.text((18,1450),'Cyan: original shoe insole alpha lower edge. Pink: actual transformed, unoccluded foot alpha lower edge.',font=font,fill='#423642')
d.text((18,1480),'Overlay shows measured contours and their remaining residual; it is not an idealized or snapped alignment.',font=font,fill='#423642')
d.text((18,1510),'Original shoes retain translation / uniform scale only. Source PNGs remain immutable. Developer inspection.',font=font,fill='#423642')
OUT.parent.mkdir(exist_ok=True,parents=True);sheet.save(OUT,quality=94,optimize=True)
(QA/'stiletto6-independent-overlay-metrics.json').write_text(json.dumps(report,indent=2)+'\n')
print(OUT);print(json.dumps(report))
