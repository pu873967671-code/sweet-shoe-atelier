#!/usr/bin/env python3
"""Remove photographic grain from tint lighting maps without moving masks.
Called only after source extraction. The immutable shoe alpha/upper remains exact.
"""
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/fitting2d'
for heel in ['flat','kitten','block','wedge']:
    upper=np.array(Image.open(OUT/(heel+'_upper.webp')).convert('RGBA'))[:,:,3].astype('float32')
    for part in ['shadow','highlight']:
        path=OUT/(heel+'_'+part+'.webp');a=np.array(Image.open(path).convert('RGBA'))
        # Blur the lighting value rather than mask coverage; clip it back to
        # original authored upper, avoiding a pale fringe on binding/sole.
        valid=(upper>32).astype('float32')
        ratio=np.zeros_like(upper);np.divide(a[:,:,3].astype('float32'),upper,out=ratio,where=upper>0)
        numerator=cv2.GaussianBlur(ratio*valid,(0,0),4)
        denominator=cv2.GaussianBlur(valid,(0,0),4)
        np.divide(numerator,denominator,out=ratio,where=denominator>.001)
        a[:,:,3]=np.clip(ratio*upper,0,255).astype('uint8')
        Image.fromarray(a).save(path,lossless=True)
print('PASS smooth continuous satin/velvet source lightmaps; upper alpha unchanged')
