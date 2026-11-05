#!/usr/bin/env python3
"""Final fixed-frame pearl-strand ROI cleanup after build-fitting-accessories.
The accepted painted strand is preserved pixel for pixel. Collar and toe binding
fragments outside its reviewed diagonal instep band are transparent.
"""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
for heel in ['flat','kitten','block','wedge']:
    path=ROOT/'assets/fitting2d/accessories'/f'{heel}_strap_pearl.webp'
    a=np.array(Image.open(path).convert('RGBA'));yy,xx=np.indices(a.shape[:2])
    strand=(xx>=360)&(xx<(620 if heel=='flat' else 650))&(yy>610)&(yy<815)
    removed=int(np.count_nonzero((a[:,:,3]>0)&~strand))
    a[:,:,3][~strand]=0
    Image.fromarray(a).save(path,lossless=True)
    print(f'{heel}: removed {removed} residue pixels; strand frame unchanged')
