#!/usr/bin/env python3
"""Restore continuous painted product laces from their retained original edits.

Difference-only extraction punched holes where pale satin matched ivory shoe.
Re-extract lilac fabric within the immutable approved ornament footprint, close
subpixel pinholes and reject detached flecks. The shared alpha is used for both
neutral painting and tint, then the original per-column camera mappings apply.
No body, skin, worn layer, camera, toe or floor asset is modified. Pillow/NumPy.
Run after legacy ornament, thin-height and platform accessory exporters.
"""
from pathlib import Path
import json,os
import numpy as np
from PIL import Image,ImageChops,ImageFilter
ROOT=Path(__file__).resolve().parents[2]
SRC=Path(__file__).with_name('product-cross-source');SRC.mkdir(exist_ok=True)
OUT=ROOT/'qa/session-0425-legacy-audit';OUT.mkdir(exist_ok=True)
ASSETS=ROOT/'assets/shoe2d/accessories'
records=json.loads((ROOT/'dev/accessory-edits/extraction-report.json').read_text())['layers']
def atomic(im,path):
 temporary=path.with_name('.'+path.name+'.'+str(os.getpid())+'.tmp')
 try:im.save(temporary,format='WEBP',lossless=True,exact=True);temporary.replace(path)
 finally:temporary.unlink(missing_ok=True)
def remove_flecks(mask):
 a=np.array(mask);solid=a>100;seen=np.zeros(solid.shape,bool)
 for sy,sx in zip(*np.where(solid)):
  if seen[sy,sx]:continue
  seen[sy,sx]=True;todo=[(sy,sx)];component=[]
  while todo:
   y,x=todo.pop();component.append((y,x))
   for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
    if 0<=yy<a.shape[0] and 0<=xx<a.shape[1] and solid[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;todo.append((yy,xx))
  if len(component)<35:
   for y,x in component:a[max(0,y-2):y+3,max(0,x-2):x+3]=0
 return Image.fromarray(a)
def base(heel):
 path=ASSETS/f'{heel}_strap_cross.webp';retained=SRC/path.name
 if not retained.exists():atomic(Image.open(path).convert('RGBA'),retained)
 support=Image.open(retained).getchannel('A').filter(ImageFilter.MaxFilter(31))
 record=next(r for r in records if r['name']==heel+'_strap_cross')
 warp=tuple(v for row in record['warp'] for v in row)
 im=Image.open(ROOT/record['source']).convert('RGBA').resize((1024,640),Image.Resampling.LANCZOS).transform((1024,640),Image.Transform.AFFINE,warp,Image.Resampling.BICUBIC)
 rgb=np.array(im)[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1)
 alpha=Image.fromarray((((r-g>3)&(b-g>4)&(g<245))*255).astype('uint8'))
 alpha=ImageChops.multiply(alpha,support).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
 alpha=remove_flecks(alpha).filter(ImageFilter.GaussianBlur(.4))
 gray=np.clip(rgb@np.array([.2126,.7152,.0722])*1.2,0,255).astype('uint8')
 rgba=np.zeros((640,1024,4),np.uint8);rgba[:,:,:3]=gray[:,:,None];rgba[:,:,3]=np.array(alpha)
 return rgba
def remap(a,shift):
 yy,xx=np.indices(a.shape[:2]);sy=yy-shift[None,:];lo=np.floor(sy).astype(int);hi=lo+1;t=(sy-lo)[:,:,None]
 lo=np.clip(lo,0,639);hi=np.clip(hi,0,639)
 out=(a[lo,xx]*(1-t)+a[hi,xx]*t).clip(0,255).astype('uint8');out[(sy<0)|(sy>639)]=0
 return out
block=base('block');kitten=base('kitten');x=np.arange(1024)
paintings={'block':block,'kitten':kitten,'platform':remap(block,-52*(1-np.clip((x-300)/550,0,1)))}
for height in (6,9):paintings['stiletto'+str(height)]=remap(kitten,np.interp(x,[0,285,594,855,1024],[15,15 if height==6 else 20,14,-8 if height==6 else -2,0]))
report={'status':'PASS','styles':[]}
for heel,a in paintings.items():
 before=Image.open(SRC/f'{heel}_strap_cross.webp').convert('RGBA')
 a[a[:,:,3]==0,:3]=0;im=Image.fromarray(a)
 tint=np.full_like(a,255);tint[:,:,3]=a[:,:,3]
 atomic(im,ASSETS/f'{heel}_strap_cross.webp');atomic(Image.fromarray(tint),ASSETS/f'{heel}_strap_cross_tint.webp')
 assert Image.open(ASSETS/f'{heel}_strap_cross.webp').getchannel('A').tobytes()==Image.open(ASSETS/f'{heel}_strap_cross_tint.webp').getchannel('A').tobytes()
 assert not im.getchannel('A').crop((0,530,1024,640)).getbbox(),(heel,'ground clearance')
 for label,layer in [('before',before),('after',im)]:
  bg=Image.new('RGBA',layer.size,'#223b36');bg.alpha_composite(layer);bg.crop((300,280,790,530)).resize((1470,750)).convert('RGB').save(OUT/f'{heel}-cross-{label}-native.jpg',quality=95)
 report['styles'].append({'heel':heel,'shared_rgb_tint_alpha':True,'frame':[1024,640],'body_skin_worn_untouched':True,'ground_clearance':True})
(OUT/'cross-source-report.json').write_text(json.dumps(report,indent=2))
print('PASS',len(paintings),'continuous product cross-lace paintings, shared tint alpha')
