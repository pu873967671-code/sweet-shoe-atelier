#!/usr/bin/env python3
"""Deterministic fixed-camera platform kit from genuine gpt-image-2 edits.
Ornaments are the approved block perspective paintings remapped to new mounts.
"""
from pathlib import Path
import json,shutil
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/platform-source'
def read(p,size=None):
 im=Image.open(p).convert('RGBA');return np.array(im.resize(size,Image.Resampling.LANCZOS) if size else im)
def save(folder,part,rgb,alpha):
 a=np.clip(alpha,0,255).astype('uint8');out=np.zeros((*a.shape,4),np.uint8);out[:,:,:3]=rgb;out[:,:,3]=a;Image.fromarray(out).save(ROOT/f'assets/{folder}/platform_{part}.webp',lossless=True)
def close(mask,n=5):return cv2.morphologyEx(mask.astype('uint8'),cv2.MORPH_CLOSE,np.ones((n,n),np.uint8))
def blur(mask,sigma=.6):return cv2.GaussianBlur(mask.astype('float32'),(0,0),sigma)
def full(mask):
 contours,_=cv2.findContours(mask.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);out=np.zeros_like(mask,dtype='uint8');cv2.drawContours(out,contours,-1,1,cv2.FILLED);return out
meta={}
for view,folder,size,part in [('product','shoe2d',(1024,640),'base'),('fitting','fitting2d',(1024,1024),'shoe')]:
 src=read(SRC/(view+'.png'),size)
 if view=='product':
  im=Image.open(SRC/'product.png').convert('RGBA');a=np.array(im)[:,:,3];yy,xx=np.where(a>127);crop=im.crop((int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))).resize((833,490),Image.Resampling.LANCZOS);im=Image.new('RGBA',size);im.paste(crop,(96,51));src=np.array(im)
 rgb=src[:,:,:3];r,g,b=rgb.astype(float).transpose(2,0,1);alpha=src[:,:,3];Y,X=np.indices(alpha.shape)
 # Alpha fringe cleanup follows source exterior, retaining real open arch.
 silhouette=blur(close(alpha>110,3))
 if view=='product':shell=silhouette*255
 else:
  boundary=np.interp(X,[0,185,220,270,300,320,350,400,450,500,540,580,620,660,700,730,740,760,785,810,1024],[1024,875,845,810,792,780,800,820,829,826,812,773,718,660,590,520,450,470,515,590,590]);geometry=(Y>=boundary)|((r-g<24)&(r-b<58)&(Y>430)&(alpha>50));shell=silhouette*blur(geometry)*255
 shell[shell<3]=0;save(folder,part,rgb,shell)
 # Source warm piping, lining and tan outsole stay natural. Satin upper,
 # platform face and complete heel support receive a single continuous tint.
 if view=='product':
  collar=np.interp(X,[0,96,200,300,350,400,450,500,550,600,650,700,750,800,840,860,900,1024],[640,438,375,340,339,351,360,366,368,356,330,290,242,176,105,75,110,110])
  cloth=(Y>=collar+2)|(X<310)
 else:
  cloth=(Y>=boundary+np.where((X>310)&(X<745),2,0))|(X<310)
 bottom=np.where(shell>80,Y,-1).max(axis=0);cloth &= Y<bottom[None,:]-6
 ua=np.minimum(shell,blur(cloth)*255)
 # Broad lightmaps avoid pore/fabric-dot noise on plain velvet.
 lum=cv2.GaussianBlur(rgb@np.array([.2126,.7152,.0722]),(0,0),4)
 save(folder,'upper',255,ua);save(folder,'shadow',0,np.clip((242-lum)/155,0,.65)*ua);save(folder,'highlight',255,np.clip((lum-205)/65,0,.6)*ua)
 if view=='product':
  warm=np.maximum(0,shell-ua);lining=warm*(Y<390)*(X<850);sole=shell*(Y>=bottom[None,:]-7)
  binding=cv2.morphologyEx((ua>100).astype('uint8'),cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))*warm
  save(folder,'binding',255,binding);save(folder,'insole',255,lining);save(folder,'sole',255,sole)
 else:
  leg=read(ROOT/'assets/fitting2d/block_legs.webp');skin=silhouette*255*(1-blur(geometry))
  # Platform raises the forefoot collar40px; the newly exposed instep comes
  # from its genuine edit. Continue accepted cel skin, preserving upper400rows.
  srgb=cv2.bilateralFilter(rgb,17,35,15).astype('float32');sl=cv2.GaussianBlur(srgb@np.array([.2126,.7152,.0722],np.float32),(0,0),6);v=cv2.GaussianBlur(np.round(np.clip((sl-145)/94,0,1)*8)/8,(0,0),5);srgb=np.array([219,155,141])[None,None,:]+v[:,:,None]*np.array([36,75,65])[None,None,:]
  newleg=np.dstack([srgb,skin]).clip(0,255).astype('uint8');mix=np.clip((Y-400)/80,0,1);leg=(leg*(1-mix[:,:,None])+newleg*mix[:,:,None]).clip(0,255).astype('uint8');save(folder,'legs',leg[:,:,:3],leg[:,:,3])
  occ=shell.copy();occ[Y>650]=np.maximum(occ[Y>650],255-silhouette[Y>650]*255);save(folder,'occlusion',255,occ)
 Image.fromarray(np.dstack([rgb,shell]).clip(0,255).astype('uint8')).save(SRC/(view+'-normalized.png'))
 # Per-column source-coordinate mapping follows the new collar rather than
 # placing front-facing stickers. Both sprite and tint alpha share the warp.
 for p in (ROOT/f'assets/{folder}/accessories').glob('block_*.webp'):
  a=read(p);h,w=a.shape[:2];yy,xx=np.indices((h,w),dtype='float32')
  if view=='product':mapy=yy+52*(1-np.clip((xx-300)/550,0,1));mapx=xx
  else:
   mapy=yy+40;mapx=xx-5
   if any(k in p.name for k in ['strap_thin','strap_ribbon']):mapx-=10*(1-np.clip((xx-500)/170,0,1))
  mapped=cv2.remap(a,mapx.astype('float32'),mapy.astype('float32'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
  if view=='fitting' and any(k in p.name for k in ['strap_thin','strap_ribbon']):mapped[:,:,3]=(mapped[:,:,3].astype(float)*silhouette).clip(0,255).astype('uint8')
  Image.fromarray(mapped).save(p.with_name(p.name.replace('block_','platform_')),lossless=True)
 meta[view]={'frame':list(size),'source':view+'.png','skin':'exact accepted upper400rows; source-matched lower instep cel finish' if view=='fitting' else None,'ornamentWarp':{'x':0,'y':'-52*(1-clamp((x-300)/550,0,1))'} if view=='product' else {'x':5,'y':-40},'upperPixels':int((ua>127).sum()),'shellPixels':int((shell>127).sum())}
(SRC/'export.json').write_text(json.dumps(meta,indent=2))
sheet=Image.new('RGB',(1440,800),'#edfff5');d=ImageDraw.Draw(sheet)
for j,(folder,p) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 im=Image.open(ROOT/f'assets/{folder}/platform_{p}.webp').convert('RGBA')
 if j:leg=Image.open(ROOT/'assets/fitting2d/platform_legs.webp').convert('RGBA');occ=Image.open(ROOT/'assets/fitting2d/platform_occlusion.webp').convert('RGBA').getchannel('A');la=np.array(leg);la[:,:,3]=np.array(leg.getchannel('A'))*(1-np.array(occ)/255);leg=Image.fromarray(la);leg.alpha_composite(im);im=leg
 im.thumbnail((700,740));sheet.paste(im,(j*720,0),im);d.text((j*720+12,760),folder+' neutral platform',fill='#225e47')
sheet.save(SRC/'export-contact.jpg',quality=95)
print(json.dumps(meta,indent=2))
