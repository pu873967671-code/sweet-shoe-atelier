#!/usr/bin/env python3
"""Offline luminance maps: runtime recolouring works even on tainted canvases."""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/tones';OUT.mkdir(exist_ok=True)
files=list((ROOT/'assets').glob('shoe_*.webp'))+list((ROOT/'assets/angles').glob('*_shade.webp'))+list((ROOT/'assets/poses').glob('*_shade.webp'))+list((ROOT/'assets/legs').glob('leg_*.webp'))
for path in files:
 im=Image.open(path).convert('RGBA');a=np.array(im);lum=(a[:,:,:3].astype(float)*[.2126,.7152,.0722]).sum(2)/255
 alpha=a[:,:,3]
 if path.parent.name=='legs':alpha=np.array(Image.open(path.with_name(path.name.replace('leg_','mask_'))).convert('RGBA'))[:,:,3]
 factor=.5+.65*lum
 for suffix,values in [('tone',np.minimum(factor,1)),('gleam',np.minimum(1,np.maximum(lum-.8,0)*250/255+np.maximum(factor-1,0)))]:
  pixels=np.zeros_like(a);pixels[:,:,:3]=np.uint8(np.round(values[:,:,None]*255));pixels[:,:,3]=alpha
  Image.fromarray(pixels).save(OUT/(path.stem+'_'+suffix+'.webp'),lossless=True)
print('Built',len(files)*2,'luminance maps')
