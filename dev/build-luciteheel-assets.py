#!/usr/bin/env python3
"""Original transparent faceted lucite heel on the accepted 6cm shoe cameras.

Native authored geometry: no generated painting or new anatomy is claimed.
Only distal heel stem changes; accepted upper/skin and original heel cap stay.
"""
from pathlib import Path
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageChops

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'dev/luciteheel-source'
SRC.mkdir(exist_ok=True)
CONFIG={
 'product':{'folder':'shoe2d','part':'base','start':326,'stop':461,'left':800,'top':[823,872],'bottom':[825,866],'toe':96,'floor':540,'heelFloor':478},
 'fitting':{'folder':'fitting2d','part':'shoe','start':714,'stop':850,'left':704,'top':[736,776],'bottom':[736,772],'toe':171,'floor':964,'heelFloor':866}
}

def save(path,array):
 temporary=path.with_name(path.stem+'.tmp.webp')
 Image.fromarray(np.clip(array,0,255).astype('uint8')).save(temporary,lossless=True,method=6,exact=True)
 temporary.replace(path)

def geometry(size,cfg):
 # Four-times authored geometry makes even the hairline bevels antialiased.
 scale=4
 layer=Image.new('RGBA',(size[0]*scale,size[1]*scale))
 p=ImageDraw.Draw(layer)
 top,bottom=cfg['start'],cfg['stop']+1
 xl,xr=cfg['top'];bl,br=cfg['bottom'];width=xr-xl
 left=xl+width*.24;right=xr-width*.17
 bleft=bl+(br-bl)*.27;bright=br-(br-bl)*.22
 def poly(points,color):p.polygon([(round(x*scale),round(y*scale)) for x,y in points],fill=color)
 def line(points,color,width=1):p.line([(round(x*scale),round(y*scale)) for x,y in points],fill=color,width=round(width*scale),joint='curve')
 # The central pane is deliberately very transparent. Edge faces contain
 # soft mint/rose reflections and remain translucent over both backplates.
 poly([(xl,top),(left,top),(bleft,bottom),(bl,bottom)],(155,188,191,117))
 poly([(left,top),(right,top),(bright,bottom),(bleft,bottom)],(226,247,240,43))
 poly([(right,top),(xr,top),(br,bottom),(bright,bottom)],(132,192,185,135))
 line([(xl+.4,top),(bl+.4,bottom)],(222,251,240,208),1.15)
 line([(left,top),(bleft,bottom)],(255,249,236,202),1.15)
 line([(right,top),(bright,bottom)],(231,255,253,196),1)
 line([(xr-.5,top),(br-.5,bottom)],(94,145,148,170),1.1)
 # Restrained diagonal reflected light, clipped to the front pane.
 mid=top+(bottom-top)*.35
 poly([(left+1,mid),(right-2,mid-13),(right-4,mid-5),(left+1,mid+9)],(250,255,246,119))
 poly([(left+2,mid+16),(right-5,mid+2),(right-5,mid+5),(left+2,mid+20)],(255,238,226,78))
 # Tiny champagne collar connects the glass to the unchanged painted heel.
 poly([(xl,top),(xr,top),(xr-.2,top+3),(xl+.2,top+3)],(201,171,129,255))
 line([(xl+.5,top+.6),(xr-.5,top+.6)],(250,228,187,255),.8)
 # Source cap below remains byte-exact and receives this matching rim.
 line([(bl,bottom-.8),(br,bottom-.8)],(230,204,163,220),1.1)
 return layer.resize(size,Image.Resampling.LANCZOS)

metadata={}
for view,cfg in CONFIG.items():
 folder=ROOT/'assets'/cfg['folder']
 original=np.array(Image.open(folder/f"stiletto6_{cfg['part']}.webp").convert('RGBA'))
 h,w=original.shape[:2];y,x=np.indices((h,w))
 region=(y>=cfg['start'])&(y<cfg['stop'])&(x>=cfg['left'])
 shell=original.copy();shell[region]=0
 support=geometry((w,h),cfg)
 # Keep all geometry inside the designated distal stem band. In particular
 # the original top contour and the original floor-contact cap stay exact.
 support_array=np.array(support);support_array[~region]=0
 support=Image.fromarray(support_array)
 result=Image.fromarray(shell);result.alpha_composite(support)
 output=np.array(result);outside=~region
 output[outside]=original[outside]
 save(folder/f"luciteheel_{cfg['part']}.webp",output)
 save(SRC/f'{view}-support.webp',support_array)
 for part in ['upper','shadow','highlight']+(['binding','insole','sole'] if view=='product' else []):
  effect=np.array(Image.open(folder/f'stiletto6_{part}.webp').convert('RGBA'))
  effect[region,3]=0
  save(folder/f'luciteheel_{part}.webp',effect)
 if view=='fitting':
  for part in ['legs','occlusion']:
   destination=folder/f'luciteheel_{part}.webp';temporary=destination.with_name(destination.stem+'.tmp.webp')
   shutil.copyfile(folder/f'stiletto6_{part}.webp',temporary);temporary.replace(destination)
 assert np.array_equal(output[outside],original[outside])
 bounds=Image.fromarray(output[:,:,3]).point(lambda a:255 if a>127 else 0).getbbox()
 assert bounds[0]==cfg['toe'] and bounds[3]-1==cfg['floor'],bounds
 assert np.array_equal(output[cfg['stop']:],original[cfg['stop']:])
 # Deliberately transparent glass must not become an opaque white stem.
 a=support_array[:,:,3];glass=(a>10)&(a<160)
 assert glass.sum()>3000
 metadata[view]={**cfg,'base':'stiletto6','frame':[w,h], 'translucentGlassPixels':int(glass.sum()),'unchangedOutsideDistalStem':True,'originalHeelCapExact':True,'source':'original code-native translucent beveled prism'}
(SRC/'export.json').write_text(json.dumps(metadata,indent=2)+'\n')
(SRC/'anchors.json').write_text(json.dumps(metadata,indent=2)+'\n')
sheet=Image.new('RGB',(1440,1100),'#f8fff5');draw=ImageDraw.Draw(sheet)
for col,(folder,part) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 for row,bg in enumerate(['#fff4ed','#233c43']):
  im=Image.open(ROOT/f'assets/{folder}/luciteheel_{part}.webp').convert('RGBA')
  if col:
   skin=Image.open(ROOT/'assets/fitting2d/luciteheel_legs.webp').convert('RGBA')
   skin.putalpha(ImageChops.subtract(skin.getchannel('A'),Image.open(ROOT/'assets/fitting2d/luciteheel_occlusion.webp').getchannel('A')))
   skin.alpha_composite(im);im=skin
  im.thumbnail((690,510));tile=Image.new('RGB',(720,550),bg)
  tile.paste(im,((720-im.width)//2,0),im);sheet.paste(tile,(col*720,row*550))
  draw.text((col*720+12,row*550+525),folder+' / translucent lucite / original upper, skin, heel cap',fill='#f680ae')
sheet.save(SRC/'export-contact.jpg',quality=95)
print('PASS:13 layers; transparent glass; exact upper, skin, contact cap, toe and floor')
