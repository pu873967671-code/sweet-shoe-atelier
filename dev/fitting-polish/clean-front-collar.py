#!/usr/bin/env python3
"""Remove raw source-skin slivers from the painted front collar aperture.
Run after build-skin.py and derivative exports. Exterior shoe/leg silhouettes,
upper calf and all pixels outside this tiny inner opening remain unchanged.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/fitting2d'
Y,X=np.indices((1024,1024));report={}
DERIVATIVES={'flat':['maryjane','ballet'],'kitten':['slingback']}
# Authored inner piping boundaries at the accepted source camera. The original
# colour-key extraction left rectangular skin fragments above this smooth line.
XS=[310,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600,610]
CURVES={
 'flat':[815,824,834,842,848,853,857,860,861,861,857,852,842,827,807,780,766],
 'block':[812,820,830,837,843,848,852,854,855,853,849,841,826,806,779,748,733],
 'kitten':[797,805,818,828,834,841,844,849,850,850,848,842,833,819,800,777,763],
 'wedge':[797,804,814,820,827,833,838,843,846,847,846,841,832,817,794,764,747]}
for heel in ['flat','block','kitten','wedge']:
 src=np.array(Image.open(ROOT/f'dev/fitting-source/{heel}.png').convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
 leg=np.array(Image.open(OUT/f'{heel}_legs.webp').convert('RGBA'));r,g,b=src[:,:,:3].astype(float).transpose(2,0,1)
 seed=((r-g>24)&(r-b>41)&(src[:,:,3]>64))|(leg[:,:,3]>200)
 seed=cv2.morphologyEx(seed.astype('uint8'),cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
 region=(X>=310)&(X<=610)&(Y>675)&(Y<np.interp(X,XS,CURVES[heel]))
 mask=seed*region
 # Feather only the authored collar line, avoiding a staircase at native scale.
 coverage=cv2.GaussianBlur(mask.astype('float32'),(0,0),.65)
 coverage[~((X>=308)&(X<=612)&(Y>673)&(Y<880))]=0
 rgb=leg[630:900,260:640,:3].copy();alpha=leg[630:900,260:640,3]
 rgb=cv2.inpaint(rgb,(alpha<200).astype('uint8'),7,cv2.INPAINT_TELEA)
 cel=leg[:,:,:3].copy();cel[630:900,260:640]=rgb;cel[leg[:,:,3]>200]=leg[:,:,:3][leg[:,:,3]>200]
 parts=['shoe','upper','shadow','highlight','occlusion','legs']
 before={p:np.array(Image.open(OUT/f'{heel}_{p}.webp').convert('RGBA')) for p in parts}
 after={p:a.copy() for p,a in before.items()}
 # Continue the same source-matched cel skin underneath the full inner opening.
 grow=coverage*src[:,:,3];changed=grow>after['legs'][:,:,3]
 after['legs'][:,:,:3][changed]=cel[changed]
 after['legs'][:,:,3]=np.maximum(after['legs'][:,:,3],grow).astype('uint8')
 for part in parts[:-1]:after[part][:,:,3]=(after[part][:,:,3]*(1-coverage)).astype('uint8')
 affected=coverage>0
 for part in parts:
  assert np.array_equal(before[part][~affected],after[part][~affected]),(heel,part,'outside aperture')
  Image.fromarray(after[part]).save(OUT/f'{heel}_{part}.webp',lossless=True)
 for style in DERIVATIVES.get(heel,[]):
  for part in parts:
   path=OUT/f'{style}_{part}.webp'
   if not path.exists():continue
   a=np.array(Image.open(path).convert('RGBA'));inherited=affected&np.all(a==before[part],axis=2);a[inherited]=after[part][inherited]
   Image.fromarray(a).save(path,lossless=True)
 report[heel]={'aperturePixels':int(affected.sum()),'outsideApertureChanged':False,'calfChanged':False}
print(json.dumps(report,indent=2))
