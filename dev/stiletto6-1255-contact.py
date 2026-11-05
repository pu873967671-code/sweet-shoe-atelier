#!/usr/bin/env python3
"""Actual browser evidence with the full counter apex, not an arch-only crop."""
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'qa/stiletto6-1255/after'
BG='#f7f1eb';INK='#423642'
sheet=Image.new('RGB',(1900,2300),BG);d=ImageDraw.Draw(sheet)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
def flatten(im):
 bg=Image.new('RGBA',im.size,BG);bg.alpha_composite(im.convert('RGBA'));return bg.convert('RGB')
def tile(path,box,label):
 x,y,w,h=box;d.text((x,y),label,font=font,fill=INK)
 im=flatten(Image.open(path));im.thumbnail((w,h-32),Image.Resampling.LANCZOS)
 sheet.paste(im,(x+(w-im.width)//2,y+32+(h-32-im.height)//2))
d.text((20,15),'Stiletto6 | SUPERVISOR 12:55 | developer visual review',font=title,fill=INK)
d.text((20,56),'Actual /usr/bin/chromium. Bright white cloth, smooth counter dye / collar, whole-source heel seating.',font=font,fill=INK)
tile(QA/'stiletto6-white-390.png',(20,100,235,470),'390 x 844')
tile(QA/'stiletto6-white-1920.png',(280,100,650,470),'1920 x 1080')
tile(QA/'stiletto6-white-1920-pair.png',(950,100,565,470),'Actual fitting pair')
tile(ROOT/'assets/src-user-legs-20261029/pair-reference-user.png',(1535,100,345,470),'Pair reference')
shoe=Image.open(QA/'stiletto6-product-1920.png').convert('RGBA')
for col,side in enumerate(['front','rear']):
 x=20+col*940
 for kind in ['white','bare','black']:
  im=shoe.copy();foot=Image.open(QA/f'stiletto6-{kind}-{side}-native.png').convert('RGBA');im.alpha_composite(foot.crop((0,1500,1024,2140)))
  im.save(QA/f'{side}-{kind}-shoe-native.png')
 tile(QA/f'{side}-white-shoe-native.png',(x,590,920,530),f'{side.title()} / white / original rigid shoe')
 for row,(kind,box) in enumerate([('white',(790,0,960,225)),('bare',(790,0,960,225))]):
  im=flatten(Image.open(QA/f'{side}-{kind}-shoe-native.png').crop(box));im=im.resize((510,675),Image.Resampling.LANCZOS)
  im.save(QA/f'{side}-{kind}-counter-3x.png')
  # Keep exact source-pixel magnification; both kinds placed side by side.
  cx=x+(0 if row==0 else 470)
  crop=im.crop((35,0,505,675))
  d.text((cx,1140),f'{side} / {kind} counter / 3x',font=font,fill=INK);sheet.paste(crop,(cx,1175))
 im=flatten(Image.open(QA/f'{side}-white-shoe-native.png').crop((320,280,740,450))).resize((840,340),Image.Resampling.LANCZOS)
 im.save(QA/f'{side}-white-instep-2x.png');d.text((x,1880),f'{side} / white instep and collar / 2x',font=font,fill=INK);sheet.paste(im,(x+35,1915))
d.text((20,2260),'Original user PNGs, raised-heel source and shoe base unchanged. Artistic supervisor acceptance remains separate.',font=font,fill=INK)
out=ROOT/'qa/contact'/f'{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.jpg';out.parent.mkdir(exist_ok=True);sheet.save(out,quality=94,optimize=True);print(out)
