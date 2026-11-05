#!/usr/bin/env python3
"""Add immutable-colour protection mattes; never rewrite existing artwork.

The authored upper mask overselects warm soles, welt/piping and woven wedges.
Source chroma distinguishes these from neutral satin. The same matte is shared
by registered sock variants; collect their warm details in base coordinates too.
Lucite stems are neutral rather than warm, so their two authored bounds are
included explicitly. Fabric-covered heels remain dyeable, as in product view.
"""
import json,re
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
ROOT=Path(__file__).resolve().parents[1]
REFS=json.loads(re.search(r'const SPRITES=(.*);',(ROOT/'js/worn-sprites.js').read_text()).group(1))
for heel,ref in REFS.items():
 if '_' in heel:continue
 w,h=ref['w'],ref['h'];protection=Image.new('L',(w,h))
 for suffix in ['', '_frill','_lace']:
  key=heel+suffix;r=REFS[key];src=np.array(Image.open(ROOT/f'assets/worn/{key}.webp').convert('RGBA')).astype(np.int16)
  # Protect warm natural materials and the warm ivory piping, not satin shadows.
  warm=(src[:,:,0]-src[:,:,2]>=24)&(src[:,:,1]-src[:,:,2]>=10)&(src[:,:,0]>=src[:,:,1])&(src[:,:,3]>0)
  upper=np.array(Image.open(ROOT/f'assets/worn/{key}_mask.webp').convert('RGBA'))[:,:,3]
  warm &= upper>16
  m=Image.fromarray(np.uint8(warm)*255)
  # Ignore skin far above footwear. The runtime dye mask still controls the
  # application, so inclusion of skin at openings does not change its pixels.
  m.paste(0,(0,0,m.width,round(h*.58)))
  aligned=Image.new('L',(w,h));aligned.paste(m,(r['x']-ref['x'],r['y']-ref['y']));protection=ImageChops.lighter(protection,aligned)
 if heel=='luciteheel':
  d=ImageDraw.Draw(protection)
  d.polygon([(296,704),(324,706),(322,780),(297,780)],fill=255)
  d.polygon([(539,761),(576,763),(575,851),(539,851)],fill=255)
 if heel=='pearlheel':
  # Original pearl orb and its metal mount are not fabric in product view.
  d=ImageDraw.Draw(protection);d.ellipse((464,767,522,823),fill=255);d.rectangle((480,752,509,830),fill=255)
 # A one-pixel source-derived expansion protects the antialiased welt edge.
 protection=protection.filter(ImageFilter.MaxFilter(3))
 # Never remove the incumbent dye at a skin/cuff fringe.
 legs=Image.open(ROOT/f'assets/worn/{heel}_legs.webp').getchannel('A')
 protection=ImageChops.subtract(protection,legs.point(lambda a:255 if a else 0))
 out=Image.new('RGBA',(w,h),'white');out.putalpha(protection)
 path=ROOT/f'assets/worn/{heel}_sole.webp';out.save(path,lossless=True,method=6)
 print(heel,path.stat().st_size)
