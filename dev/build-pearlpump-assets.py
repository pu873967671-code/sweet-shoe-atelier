#!/usr/bin/env python3
"""Extract genuine camera-specific pearl studs over exact accepted 6cm artwork.

Only hand-reviewed bead islands from the generated edits are retained. The
immutable existing shoe, skin, binding and sole never use generated replacement
pixels. Pearl cutouts include their small source-painted contact shadows.
"""
from pathlib import Path
import json, shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageChops
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'dev/pearlpump-source'

def rgba(p):return np.array(Image.open(p).convert('RGBA'))
def save(p,a):Image.fromarray(a.clip(0,255).astype('uint8')).save(p,lossless=True,method=6)
def blur(a,s=.65):return cv2.GaussianBlur(a.astype('float32'),(0,0),s)

# Source-camera pearl centres/radii reviewed against genuine generated edits.
# Each is a small local crop, never an invented procedural bead painting.
PEARLS={
 'product': [(182,468,11,11),(234,448,11,10),(280,408,10,10),(322,430,15,15),(268,478,10,10),(226,506,10,10),(344,482,15,15),(396,448,10,10),(420,500,11,11),(472,466,14,14),(522,500,14,14),(560,470,10,10),(606,482,10,10),(636,444,14,14),(686,390,11,11),(724,336,11,11),(766,292,14,14),(796,236,13,13),(834,192,11,11),(838,266,12,12),(876,118,9,9),(896,158,11,11),(882,224,9,9)],
 'fitting': [(214,916,9,9),(240,876,8,8),(276,856,11,11),(288,916,14,14),(328,832,8,8),(332,884,9,9),(380,926,9,9),(392,870,12,12),(438,912,14,14),(482,880,14,14),(500,928,8,8),(540,870,8,8),(558,902,10,10),(592,840,9,9),(666,722,8,8),(686,670,12,12),(716,616,9,9),(744,580,14,14),(742,644,9,9),(762,520,10,10),(780,476,9,9),(808,542,11,11),(792,590,8,8)]
}
metadata={}
for view,folder,basepart in [('product','shoe2d','base'),('fitting','fitting2d','shoe')]:
 original=rgba(ROOT/f'assets/{folder}/stiletto6_{basepart}.webp')
 generated=rgba(SRC/f'{view}.png')
 if view=='product':
  yy,xx=np.where(generated[:,:,3]>127)
  beadsource=Image.fromarray(generated).crop((int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))).resize((833,490),Image.Resampling.LANCZOS)
  normalized=Image.new('RGBA',(1024,640));normalized.paste(beadsource,(96,51));generated=np.array(normalized)
 else:generated=np.array(Image.fromarray(generated).resize((1024,1024),Image.Resampling.LANCZOS))
 Image.fromarray(generated).save(SRC/f'{view}-normalized.png')
 upper=rgba(ROOT/f'assets/{folder}/stiletto6_upper.webp')
 Y,X=np.indices(original.shape[:2]);mask=np.zeros(original.shape[:2],np.float32)
 accepted=[]
 for x,y,rx,ry in PEARLS[view]:
  d=((X-x)/rx)**2+((Y-y)/ry)**2
  # A rim-adjacent bead would be clipped by the immutable binding. Omit that
  # bead rather than cut a pearl in half or paint over the approved stitching.
  if np.mean(upper[:,:,3][d<.9]>220)<.985:continue
  accepted.append((x,y,rx,ry))
  mask=np.maximum(mask,np.clip((1.06-d)*10,0,1))
 # Pearls stay entirely on accepted fabric; no resampled body/calf is retained.
 mask*=upper[:,:,3]/255
 studs=generated.copy();studs[:,:,3]=(mask*255).astype('uint8')
 stitched=Image.fromarray(original);stitched.alpha_composite(Image.fromarray(studs))
 save(ROOT/f'assets/{folder}/pearlpump_{basepart}.webp',np.array(stitched))
 save(SRC/f'{view}-pearls.webp',studs)
 for part in (['binding','insole','sole'] if view=='product' else ['legs','occlusion']):
  shutil.copyfile(ROOT/f'assets/{folder}/stiletto6_{part}.webp',ROOT/f'assets/{folder}/pearlpump_{part}.webp')
 # Every effect mask excludes neutral bead cores, preserving pearl colour under
 # dark velvet as well as bright satin. Contact-shadow edges remain original.
 keep=1-np.clip(mask*1.15,0,1)
 for part in ['upper','shadow','highlight']:
  a=rgba(ROOT/f'assets/{folder}/stiletto6_{part}.webp');a[:,:,3]=(a[:,:,3]*keep).astype('uint8')
  save(ROOT/f'assets/{folder}/pearlpump_{part}.webp',a)
 before=original;after=np.array(stitched);outside=mask==0
 assert np.array_equal(before[outside],after[outside]),'body outside pearl cutouts must stay pixel-identical'
 metadata[view]={'frame':[original.shape[1],original.shape[0]],'base':'stiletto6','pearlCount':len(accepted),'source':view+'.png','pearlRegions':accepted,'unchangedOutsidePearls':True,'toe':[96,540] if view=='product' else [171,964],'groundY':540 if view=='product' else 964,'skin':'exact accepted stiletto6 cel skin' if view=='fitting' else None}
(SRC/'export.json').write_text(json.dumps(metadata,indent=2)+'\n');(SRC/'anchors.json').write_text(json.dumps(metadata,indent=2)+'\n')
sheet=Image.new('RGB',(1440,1100),'#ecfff5');d=ImageDraw.Draw(sheet)
for col,(folder,part) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 for row,bg in enumerate(['#fdf3e8','#213c40']):
  im=Image.open(ROOT/f'assets/{folder}/pearlpump_{part}.webp').convert('RGBA')
  if col:
   leg=Image.open(ROOT/f'assets/{folder}/pearlpump_legs.webp').convert('RGBA');occ=Image.open(ROOT/f'assets/{folder}/pearlpump_occlusion.webp').getchannel('A');leg.putalpha(ImageChops.subtract(leg.getchannel('A'),occ));leg.alpha_composite(im);im=leg
  im.thumbnail((690,510));tile=Image.new('RGB',(720,550),bg);tile.paste(im,((720-im.width)//2,0),im);sheet.paste(tile,(col*720,row*550));d.text((col*720+12,row*550+525),folder+' pearl satin pump',fill='#f680ae')
sheet.save(SRC/'export-contact.jpg',quality=95)
print(json.dumps(metadata,indent=2))
