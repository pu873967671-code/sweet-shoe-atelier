#!/usr/bin/env python3
"""Audit worn mattes: per variant, count visible undyed satin next to the dye
and uncovered sock green-key fringe, before (baseline commit) and after.
Run from the repository root: python3 dev/audit-worn-mask-coverage.py
"""
import importlib.util,sys,numpy as np
from PIL import Image
spec=importlib.util.spec_from_file_location('rep','dev/repair-worn-mask-coverage.py');rep=importlib.util.module_from_spec(spec);spec.loader.exec_module(rep)
def leaks(v,which):
    base=v.split('_')[0];W=rep.WORN
    P=np.asarray(Image.open(W/f'{v}.webp').convert('RGBA')).astype(np.int32);shape=P.shape
    dx,dy=rep.SPRITES[base]['x']-rep.SPRITES[v]['x'],rep.SPRITES[base]['y']-rep.SPRITES[v]['y']
    get=rep.baseline if which=='before' else rep.current
    M=get(f'{v}_mask')[...,3].astype(int);K=get(f'{v}_sock');K=K[...,3].astype(int) if K is not None else np.zeros(shape[:2],int)
    N=rep.aligned(get(f'{base}_sole'),dx,dy,shape)[...,3].astype(int)
    L=rep.aligned(rep.current(f'{base}_legs'),dx,dy,shape)[...,3].astype(int);C=rep.current(f'{v}_clear')[...,3]
    r,g,b,a=(P[...,i] for i in range(4));lum=r*.299+g*.587+b*.114;spread=np.maximum(r,np.maximum(g,b))-np.minimum(r,np.minimum(g,b))
    orn=rep.dilate(rep.thick_parts((rep.aligned(rep.baseline(f'{base}_sole'),dx,dy,shape)[...,3]>=128)&(spread<=24)&(lum>=150),rep.THICK),3)
    pz=rep.piping_zone(P,L,rep.baseline(f"{v}_mask")[...,3]>=128,base in rep.SPLIT_BASES,rep.piping_width(base))
    # visible undyed share of a pixel = 1 - dye - nodye - legs - sock (clamped)
    vis=np.clip(255-M-N-L-K,0,255)
    satin=(a>200)&(spread<=24)&(lum>=105)&~orn&~pz&(C<128)
    near=rep.dilate(M>=200,2)
    leak=satin&near&(vis>=96)
    green=(a>32)&(g>r+12)&(g>b+4)&(L<128)&(C<128)&(M<128)&(N<128)&(K<128) if v.count('_') else np.zeros(shape[:2],bool)
    return int(leak.sum()),int(green.sum())
tot=[0,0,0,0]
for v in sorted(rep.SPRITES):
    b=leaks(v,'before');a=leaks(v,'after')
    tot=[t+x for t,x in zip(tot,b+a)]
    print(f'{v:22s} undyed-satin {b[0]:5d} -> {a[0]:4d}   sock-fringe {b[1]:4d} -> {a[1]:4d}')
print('TOTAL undyed-satin',tot[0],'->',tot[2],' sock-fringe',tot[1],'->',tot[3])
