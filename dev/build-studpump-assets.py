#!/usr/bin/env python3
"""Extract original camera-painted pyramid studs onto immutable accepted 6cm art.

Per-stud contours retain only metallic hardware and its narrow contact edge.
The accepted shoe silhouette, neutral piping, outsole and anatomy stay exact.
"""
from pathlib import Path
import json, shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageChops
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'dev/studpump-source'
STUDS={
 'product':[(316,412),(351,425),(391,436),(434,446),(478,454),(523,457),(568,454),(609,442),(642,418),(675,388),(704,354),(730,319),(753,281),(778,243),(801,208),(822,174),(843,145),(863,116),(876,92)],
 'fitting':[(318,823),(343,840),(375,855),(410,866),(446,873),(484,875),(522,870),(556,856),(584,835),(607,806),(627,769),(647,733),(665,694),(683,657),(699,621),(717,584),(732,551),(744,522),(758,493),(770,466)]
}
def rgba(p):return np.array(Image.open(p).convert('RGBA'))
def save(p,a):Image.fromarray(a.clip(0,255).astype('uint8')).save(p,lossless=True,method=6,exact=True)
meta={}
for view,folder,part in [('product','shoe2d','base'),('fitting','fitting2d','shoe')]:
 original=rgba(ROOT/f'assets/{folder}/stiletto6_{part}.webp')
 generated=Image.open(SRC/f'{view}.png').convert('RGBA')
 if view=='product':
  bounds=generated.getchannel('A').point(lambda a:255 if a>127 else 0).getbbox()
  crop=generated.crop(bounds).resize((833,490),Image.Resampling.LANCZOS)
  generated=Image.new('RGBA',(1024,640));generated.paste(crop,(96,51))
 else:generated=generated.resize((1024,1024),Image.Resampling.LANCZOS)
 generated.save(SRC/f'{view}-normalized.png');generated=np.array(generated)
 region=Image.new('L',(original.shape[1],original.shape[0]));draw=ImageDraw.Draw(region)
 for x,y in STUDS[view]:
  rx,ry=(10,11) if view=='product' else (9,10)
  draw.polygon([(x-rx,y-1),(x+1,y-ry),(x+rx,y+1),(x-1,y+ry)],fill=255)
 mask=cv2.GaussianBlur(np.array(region).astype('float32'),(0,0),.4);mask[mask<1]=0
 upper=rgba(ROOT/f'assets/{folder}/stiletto6_upper.webp')
 mask*=upper[:,:,3]/255;mask[original[:,:,3]<255]=0;mask*=np.where(generated[:,:,3]>240,1,generated[:,:,3]/255);mask[mask>254]=255
 studs=generated.copy();studs[:,:,3]=mask.astype('uint8');save(SRC/f'{view}-studs.webp',studs)
 output=Image.fromarray(original);output.alpha_composite(Image.fromarray(studs));output=np.array(output);outside=mask==0;output[outside]=original[outside]
 save(ROOT/f'assets/{folder}/studpump_{part}.webp',output)
 assert np.array_equal(rgba(ROOT/f'assets/{folder}/studpump_{part}.webp')[outside],original[outside])
 assert np.array_equal(output[:,:,3],original[:,:,3]),'studs changed body silhouette'
 for cp in (['binding','insole','sole'] if view=='product' else ['legs','occlusion']):shutil.copyfile(ROOT/f'assets/{folder}/stiletto6_{cp}.webp',ROOT/f'assets/{folder}/studpump_{cp}.webp')
 for effect in ['upper','shadow','highlight']:
  a=rgba(ROOT/f'assets/{folder}/stiletto6_{effect}.webp');a[:,:,3]=(a[:,:,3]*(1-mask/255)).astype('uint8');save(ROOT/f'assets/{folder}/studpump_{effect}.webp',a)
 meta[view]={'base':'stiletto6','frame':[original.shape[1],original.shape[0]],'studCenters':STUDS[view],'outsideStudsExactRGBA':True,'exactBodyAlpha':True,'toeX':96 if view=='product' else 171,'groundY':540 if view=='product' else 964,'source':view+'.png','opaqueStudPixels':int((mask==255).sum())}
meta['workflow']={'model':'gpt-image-2','mode':'images/edits','quality':'high','endpoint':'https://afgp.cc.cd/v1','runtimeNetwork':False}
(SRC/'export.json').write_text(json.dumps(meta,indent=2)+'\n');(SRC/'anchors.json').write_text(json.dumps(meta,indent=2)+'\n')
sheet=Image.new('RGB',(1440,1100),'#ecfff5');d=ImageDraw.Draw(sheet)
for col,(folder,part) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 for row,bg in enumerate(['#fff4ed','#233c43']):
  im=Image.open(ROOT/f'assets/{folder}/studpump_{part}.webp').convert('RGBA')
  if col:
   legs=Image.open(ROOT/'assets/fitting2d/studpump_legs.webp').convert('RGBA');legs.putalpha(ImageChops.subtract(legs.getchannel('A'),Image.open(ROOT/'assets/fitting2d/studpump_occlusion.webp').getchannel('A')));legs.alpha_composite(im);im=legs
  im.thumbnail((690,510));tile=Image.new('RGB',(720,550),bg);tile.paste(im,((720-im.width)//2,0),im);sheet.paste(tile,(col*720,row*550));d.text((col*720+12,row*550+525),folder+' / source-painted pyramid studs / exact accepted body',fill='#f680ae')
sheet.save(SRC/'export-contact.jpg',quality=95)
print(json.dumps(meta,indent=2))
