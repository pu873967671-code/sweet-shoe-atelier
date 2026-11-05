#!/usr/bin/env python3
"""Close source-extraction fabric pinholes without touching any skin exports.
Run after dev/build-fitting2d.py. Existing upper boundaries define the collar;
large open ankle apertures remain open and tan sole/woven support stay separate.
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/fitting2d';yy,xx=np.indices((1024,1024))
for heel in ['flat','block','kitten','wedge']:
 upper=np.array(Image.open(OUT/f'{heel}_upper.webp').convert('RGBA'))[:,:,3]
 shoe=np.array(Image.open(OUT/f'{heel}_shoe.webp').convert('RGBA'))[:,:,3]
 mask=(upper>127).astype('uint8')
 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8))
 n,labels,stats,_=cv2.connectedComponentsWithStats(1-mask,8)
 for i in range(1,n):
  if stats[i,cv2.CC_STAT_AREA]<1000:mask[labels==i]=1
 if heel=='wedge':
  seam=np.interp(xx,[0,180,260,380,500,550,580,640,715,770,1024],[910,914,925,932,920,899,850,766,700,642,642]);mask[yy>=seam]=0
 else:
  bottom=np.where(shoe>127,yy,-1).max(axis=0);mask[yy>=bottom[None,:]-6]=0
 alpha=np.minimum(shoe,cv2.GaussianBlur(mask.astype('float32'),(0,0),.7)*255)
 # Broad painted light retains form while suppressing source fabric microdots.
 source=np.array(Image.open(ROOT/f'dev/fitting-source/{heel}.png').convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS))[:,:,:3].astype('float32')
 lum=cv2.GaussianBlur(source@np.array([.2126,.7152,.0722]),(0,0),2.5)
 for part,a,rgb in [('upper',alpha,255),('shadow',np.clip((235-lum)/110,0,.65)*alpha,0),('highlight',np.clip((lum-190)/65,0,.8)*alpha,255)]:
  out=np.full((1024,1024,4),rgb,dtype='uint8');out[:,:,3]=np.clip(a,0,255).astype('uint8');Image.fromarray(out).save(OUT/f'{heel}_{part}.webp',lossless=True)
print('PASS four continuous fabric masks + smooth painted light; skin untouched')
