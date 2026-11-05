#!/usr/bin/env python3
"""Fixed-frame extraction; source skin is shared, edits supply shoe pixels only."""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/fitting-source';OUT=ROOT/'assets/fitting2d';OUT.mkdir(exist_ok=True)
SIZE=(1024,1024)
def save(rgb,alpha,name):
 a=np.clip(alpha,0,255).astype('uint8');out=np.zeros((1024,1024,4),dtype='uint8');out[:,:,:3]=rgb;out[:,:,3]=a;Image.fromarray(out).save(OUT/(name+'.webp'),lossless=True)
base=Image.open(SRC/'barefoot.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
# Keep exact skin coordinates, remove chromatic matte fringe offline.
b=np.array(base);bf=b.astype('float32');b[:,:,3][(bf[:,:,1]>bf[:,:,0]+15)&(bf[:,:,1]>bf[:,:,2]+15)]=0
# Smooth broad painted values to match the rounded game art rather than photo pores.
soft=np.array(Image.fromarray(b).filter(ImageFilter.GaussianBlur(1.2)));soft[:,:,3]=b[:,:,3];b=soft
Image.fromarray(b).save(OUT/'legs.webp',lossless=True)
for heel in ['flat','block','kitten','wedge']:
 im=Image.open(SRC/(heel+'.png')).convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS);a=np.array(im);rgb=a[:,:,:3].astype('float32');r,g,bl=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2];yy,xx=np.indices((1024,1024));alpha=a[:,:,3]
 # Neutral satin differs from warm porcelain skin. Structural support is below
 # the ankle; component filling preserves cream piping and internal shading.
 seed=((r-g<24)&(r-bl<58)&(yy>495)&(alpha>80)).astype('uint8')
 seed=cv2.morphologyEx(seed,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
 n,labels,stats,_=cv2.connectedComponentsWithStats(seed,8);idx=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]);mask=(labels==idx).astype('uint8')
 contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(mask,contours,-1,1,cv2.FILLED)
 # Include stitched cream binding, warm outsole, and woven wedge support by
 # growing into adjacent non-skin paint, then keep one continuous shoe shell.
 grow=cv2.dilate(mask,np.ones((19,19),np.uint8));non_skin=((r-g<31)&(r-bl<83))|((yy>840)&(r-g<55))
 mask=((grow>0)&non_skin&(alpha>0)).astype('uint8');mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(mask,contours,-1,1,cv2.FILLED)
 # The shoe is continuous below its reviewed collar: include warm soles and
 # woven support without colour-key bites. Keep the real transparent heel gap.
 top=np.where(mask>0,yy,1024).min(axis=0)
 mask=((yy>=top[None,:])&(alpha>0)).astype('uint8')
 silhouette=(alpha>100).astype('uint8')*255
 silhouette=cv2.morphologyEx(silhouette,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
 silhouette=cv2.GaussianBlur(silhouette,(0,0),.85)
 smoothmask=cv2.GaussianBlur(mask.astype('float32'),(0,0),.8)
 shoealpha=silhouette*smoothmask
 save(a[:,:,:3],shoealpha,heel+'_shoe')
 # Shoe silhouette removes only hidden skin or toes outside the edited shoe.
 # Upper calf is never masked, keeping its pixels identical across all types.
 occ=np.zeros_like(alpha)
 # Common barefoot toes otherwise peek through under the fitted sole. Below
 # the ankle, keep skin only inside the edited source's skin aperture.
 occ[yy>650]=np.maximum(255-silhouette[yy>650],shoealpha[yy>650])
 save(np.full((1024,1024,3),255),occ,heel+'_occlusion')
 upper=mask.copy();upper[(r-g>26)|(r-bl>57)]=0
 if heel=='wedge':
  # The forefoot sits below y815: a horizontal cut discarded its entire satin.
  # Follow the authored satin/espadrille seam instead, retaining the woven face.
  seam=np.interp(xx,[0,180,260,380,500,550,580,640,715,770,1024],[910,914,925,932,920,899,850,766,700,642,642])
  upper[yy>=seam]=0
  upper=cv2.morphologyEx(upper,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
  upper[yy>=seam]=0
 else:
  # Satin continues down the complete support. Warm shadow pixels are still
  # satin; colour thresholds must not punch cream islands in the heel face.
  support=((xx>640)&(yy>800))|((xx>700)&(yy>730))
  upper[support&(mask>0)]=1
  bottom=np.where(mask>0,yy,-1).max(axis=0)
  upper[yy>=bottom[None,:]-6]=0
 # Sole remains cream/tan; tint follows the neutral satin shell only.
 upper=cv2.morphologyEx(upper.astype('uint8'),cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
 # Fill tiny neutral-source pinholes, keeping the main ankle aperture intact.
 holes=cv2.bitwise_not(upper*255);n,labels,stats,_=cv2.connectedComponentsWithStats(holes,8)
 for component in range(1,n):
  if stats[component,cv2.CC_STAT_AREA]<180:upper[labels==component]=1
 ua=np.minimum(shoealpha,cv2.GaussianBlur(upper.astype('float32'),(0,0),.65)*255);white=np.full((1024,1024,3),255);save(white,ua,heel+'_upper')
 lum=rgb@np.array([.2126,.7152,.0722]);save(np.zeros_like(white),np.clip((235-lum)/110,0,.65)*ua,heel+'_shadow');save(white,np.clip((lum-190)/65,0,.8)*ua,heel+'_highlight')
print('PASS fixed1024x1024 common skin +4 neutral shoe masks exported')
