#!/usr/bin/env python3
"""Cover the confirmed outer-counter cloth missed by thin-pump product masks.

Apply after build-thin-heels-assets.py, before build-pearlpump-assets.py. Only
product effect/binding masks change; base art/skin/soles/ornaments stay exact.
"""
from pathlib import Path
import json
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def read(p):return np.array(Image.open(p).convert('RGBA'))
report={}
for height in [6,9]:
 stem=ROOT/f'assets/shoe2d/stiletto{height}_';base=read(str(stem)+'base.webp');old=read(str(stem)+'upper.webp');Y,X=np.indices(old.shape[:2])
 # The cream stitched roll curves left. Everything to its right beyond these
 # reviewed source landmarks is satin, including the narrow right silhouette.
 start=867 if height==6 else 852
 boundary=np.interp(X,[start,start+5,start+10,1024],[92,82,0,0])
 region=(X>=start)&(Y>=boundary)&(Y<250)
 add=cv2.GaussianBlur(region.astype('float32'),(0,0),.5)*base[:,:,3]
 upper=np.maximum(old[:,:,3],add).clip(0,255).astype('uint8');increase=upper.astype(float)-old[:,:,3]
 assert not np.any(increase[X<start-2]),'only outer counter may change'
 def write(part,rgb,alpha):
  a=np.zeros_like(base);a[:,:,:3]=rgb;a[:,:,3]=np.clip(alpha,0,255).astype('uint8');Image.fromarray(a).save(str(stem)+part+'.webp',lossless=True,method=6)
 write('upper',255,upper)
 lum=cv2.GaussianBlur(base[:,:,:3]@np.array([.2126,.7152,.0722]),(0,0),4)
 for part,rgb,weight in [('shadow',0,np.clip((242-lum)/155,0,.65)),('highlight',255,np.clip((lum-205)/65,0,.6))]:
  a=read(str(stem)+part+'.webp');new=a[:,:,3].astype(float)+weight*increase;write(part,rgb,new)
 # The former interpolation seam through satin must not restore neutral cloth.
 binding=read(str(stem)+'binding.webp');binding[:,:,3]=(binding[:,:,3]*(1-add/255)).clip(0,255).astype('uint8');Image.fromarray(binding).save(str(stem)+'binding.webp',lossless=True,method=6)
 report[str(height)]={'changedUpperPixels':int(np.count_nonzero(increase)),'region':[start,0,1024,250],'baseUnchanged':True,'skinUnchanged':True}
print(json.dumps(report,indent=2))
