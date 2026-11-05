#!/usr/bin/env python3
"""Build immutable Mary Jane and ribbon ballet derivatives from genuine edits.
Only the reviewed added strap/ribbon component is composited over the accepted
flat. Body, toe, sole, leg and their frame retain the accepted exact pixels.
"""
from pathlib import Path
import argparse,json,shutil
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/maryjane-source'
def rgba(p,size=None):
 im=Image.open(p).convert('RGBA')
 return im.resize(size,Image.Resampling.LANCZOS) if size else im
def extract(style,view,size):
 name=('' if style=='maryjane' else 'ballet-')+('product' if view=='product' else 'fitting')
 im=rgba(SRC/(name+'.png'),size);a=np.array(im);rgb=a[:,:,:3].astype(float);r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
 yy,xx=np.indices((size[1],size[0]))
 roi=(yy>(60 if style=='ballet' else 110))&(yy<440)&(xx>380) if view=='product' else (yy>220)&(yy<760)&(xx>350)
 if style=='maryjane':roi &= (yy>190)&(xx<760) if view=='product' else (yy>510)&(xx<740)
 seed=((b-g>5)&(r-g>2)&(a[:,:,3]>10)&roi).astype('uint8')
 seed=cv2.morphologyEx(seed,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
 n,parts,stats,_=cv2.connectedComponentsWithStats(seed,8);keep=np.zeros_like(seed)
 for i in range(1,n):
  if stats[i,cv2.CC_STAT_AREA]>120:keep[parts==i]=1
 # All edited ornament cores are lavender; warm buckle joins by proximity only.
 near=cv2.dilate(keep,np.ones((9,9),np.uint8));warm=(r-b>8)&(r-g>1)&(r>100)
 keep |= ((near>0)&warm&roi&(a[:,:,3]>10)).astype('uint8')
 contours,_=cv2.findContours(keep,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(keep,contours,-1,1,cv2.FILLED)
 alpha=cv2.GaussianBlur(keep.astype('float32'),(0,0),.5)*a[:,:,3]
 # Neutral satin keeps fold luminance; warm metallic buckle retains original gold.
 cloth=(b-g>3)&(r-g>1)
 lum=rgb@np.array([.2126,.7152,.0722]);neutral=np.minimum(255,lum*1.08+8)
 rgb[cloth]=np.repeat(neutral[:,:,None],3,axis=2)[cloth]
 out=np.dstack([rgb,alpha]).clip(0,255).astype('uint8');clothalpha=alpha*cloth
 return Image.fromarray(out),clothalpha

def mask_image(colour,alpha):
 out=np.empty((*alpha.shape,4),np.uint8);out[:,:,:3]=colour;out[:,:,3]=np.clip(alpha,0,255).astype('uint8');return Image.fromarray(out)
def build(style):
 meta={}
 for view,folder,size,basepart in [('product','shoe2d',(1024,640),'base'),('fitting','fitting2d',(1024,1024),'shoe')]:
  out=ROOT/'assets'/folder;patch,cloth=extract(style,view,size);base=rgba(out/f'flat_{basepart}.webp');merged=Image.alpha_composite(base,patch);merged.save(out/f'{style}_{basepart}.webp',lossless=True)
  for part in (['binding','insole','sole'] if view=='product' else ['occlusion','legs']):shutil.copy2(out/f'flat_{part}.webp',out/f'{style}_{part}.webp')
  upper=np.array(rgba(out/'flat_upper.webp'))[:,:,3].astype(float);ua=np.maximum(upper,cloth)
  mask_image([255,255,255],ua).save(out/f'{style}_upper.webp',lossless=True)
  rgb=np.array(patch)[:,:,:3].astype(float);lum=rgb@np.array([.2126,.7152,.0722])
  for part,col,weight in [('shadow',[0,0,0],np.clip((248-lum)/175,0,.65)),('highlight',[255,255,255],np.clip((lum-205)/65,0,.6))]:
   old=np.array(rgba(out/f'flat_{part}.webp'))[:,:,3].astype(float)
   combined=old*(1-cloth/255)+weight*cloth
   mask_image(col,combined).save(out/f'{style}_{part}.webp',lossless=True)
  if view=='fitting':
   # Added cloth occludes skin through its own shoe alpha, never alters source skin.
   occ=np.array(rgba(out/'flat_occlusion.webp'))[:,:,3].astype(float);occ=np.maximum(occ,np.array(patch)[:,:,3]);mask_image([255,255,255],occ).save(out/f'{style}_occlusion.webp',lossless=True)
  patch.save(SRC/f'{style}-{view}-extracted.png');meta[view]={'frame':size,'componentBounds':patch.getbbox(),'componentPixels':int(np.count_nonzero(np.array(patch)[:,:,3])),'bodySource':f'assets/{folder}/flat_{basepart}.webp'}
 (SRC/f'{style}-export.json').write_text(json.dumps(meta,indent=2));return meta
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--style',choices=['maryjane','ballet','all'],default='all');args=p.parse_args();styles=['maryjane','ballet'] if args.style=='all' else [args.style]
 print(json.dumps({s:build(s) for s in styles},indent=2))
 sheet=Image.new('RGB',(1440,800),'#edfff5');d=ImageDraw.Draw(sheet)
 for i,s in enumerate(styles):
  for j,(folder,part) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
   im=rgba(ROOT/f'assets/{folder}/{s}_{part}.webp')
   if j:im=Image.alpha_composite(rgba(ROOT/f'assets/fitting2d/{s}_legs.webp'),im)
   im.thumbnail((690,360));sheet.paste(im,(j*720,i*400),im);d.text((j*720+10,i*400+365),s+' '+folder,fill='#215d48')
 sheet.save(SRC/'export-contact.jpg',quality=95)
