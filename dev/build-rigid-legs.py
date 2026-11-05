#!/usr/bin/env python3
"""Export accepted painted skin, automatic product throat cut and cloth volume.
No generated shoe pixels enter runtime. Rebuild with Pillow + NumPy.
"""
from pathlib import Path
import argparse
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets/fitting-rigid'
OUT.mkdir(exist_ok=True)
W,H,OY=1024,640,1200

def alpha(path):
    return np.asarray(Image.open(path).convert('RGBA'))[:,:,3]

def cut_for(heel):
    base=alpha(ROOT/f'assets/shoe2d/{heel}_base.webp')
    ins=alpha(ROOT/f'assets/shoe2d/{heel}_insole.webp')
    bind=alpha(ROOT/f'assets/shoe2d/{heel}_binding.webp')
    bottom=np.full(W,-1.); top=np.full(W,-1.); thickness=np.full(W,-1.)
    for x in range(W):
        ys=np.flatnonzero(base[:,x]>128)
        if len(ys): top[x]=ys[0]
        ys=np.flatnonzero(ins[:,x]>128)
        if len(ys):
            bottom[x]=ys[-1]
            near=np.flatnonzero(bind[int(np.ceil((ys[0]+ys[-1])/2)):min(H,int(ys[-1]+13)),x]>110)
            if len(near): thickness[x]=ys[-1]+1-(int(np.ceil((ys[0]+ys[-1])/2))+near[0])
    cut=np.empty(W)
    for x in range(W):
        ts=thickness[max(0,x-30):x+31];ts=np.sort(ts[ts>=0]);t=ts[len(ts)//2] if len(ts) else 0
        cut[x]=bottom[x]+1-max(12,t) if bottom[x]>=0 else (H+1600 if top[x]<0 else top[x])
    med=cut.copy()
    for x in range(W):
        v=np.median(cut[np.clip(np.arange(x-7,x+8),0,W-1)])
        if abs(v-cut[x])<=40: med[x]=v
    smooth=med.copy()
    for x in range(W):
        k=np.arange(max(-18,-x),min(18,W-1-x)+1);v=med[x+k];keep=abs(v-med[x])<=30;k=k[keep];v=v[keep]
        w=(1-(abs(k)/19)**3)**3;sw=w.sum();sx=(w*k).sum();sy=(w*v).sum();sxx=(w*k*k).sum();sxy=(w*k*v).sum();den=sw*sxx-sx*sx
        smooth[x]=(sy*sxx-sx*sxy)/den if den>1e-6 else sy/sw
    return smooth

# Reuse the approved whole-foot paintings, with separately posed standing
# calves and each style's product-mask opening cut.
# Only leg pixels are shared: each rigid shoe remains its exact product art.
SOURCES = {
    'studpump': None,  # Authoritative hand-fixed user anatomy.
    'flat': None,  # Delegated below to the authoritative user-leg exporter.
    'maryjane': None,  # Authoritative hand-fixed user anatomy; integral strap retained.
    'stiletto9': ('gen5/studpump-leg-front.png', 'gen/stiletto9-leg-rear.png'),
    'stiletto6': None,  # Authoritative hand-fixed user anatomy.
    'kitten': None,  # Authoritative hand-fixed user anatomy.
}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--styles', nargs='+', choices=SOURCES, default=list(SOURCES))
args = parser.parse_args()

import runpy
for user_style in ('flat', 'stiletto6', 'kitten', 'studpump', 'maryjane'):
    if user_style in args.styles:
        runpy.run_path(str(ROOT/f'dev/build-user-{user_style}-legs.py'), run_name='__main__')

for heel in args.styles:
    if heel in ('flat', 'stiletto6', 'kitten', 'studpump', 'maryjane'):
        continue  # User-repaired sources supersede the old paintings.
    sources = SOURCES[heel]
    cut=cut_for(heel)
    for which, source_name in zip(['front','rear'], sources):
        source=ROOT/'qa/research-rigid'/source_name
        a=np.array(Image.open(source).convert('RGBA'))
        if heel == 'stiletto9' and which == 'rear':
            # The original standing camera stops at y176. Continue its matching
            # calf out of frame, including the taller PNG-share composition.
            # This accepted pump calf differs by <=1px here; blend above the
            # ankle only. The stiletto's own foot and shoe cut remain exact.
            donor=np.array(Image.open(ROOT/'qa/research-rigid/gen5/studpump-leg-rear.png').convert('RGBA'))
            t=np.clip((np.arange(320)-220)/100,0,1)
            t=(t*t*(3-2*t))[:,None,None]
            a[:320]=np.rint(donor[:320]*(1-t)+a[:320]*t).astype('uint8')
        y=np.arange(a.shape[0])[:,None]-OY
        coverage=np.clip(cut[None,:]-y,0,1)
        a[:,:,3]=np.rint(a[:,:,3]*coverage).astype('uint8')
        rgb=a[:,:,:3].astype(float)
        Y=(rgb*np.array([.2126,.7152,.0722])).sum(axis=2)/255
        t=np.clip((Y-.50)/.42,0,1.25)
        sh=np.minimum(t,1)**1.15
        for kind in ['skin','cloth','black']:
            out=a.copy()
            if kind=='cloth':
                # White needs the same readable ankle/instep volume as dark
                # cloth. Keep highlights below clipping and neutral shadows;
                # the former curve flattened most pale skin to solid white.
                light=158+88*np.clip((Y-.46)/.52,0,1)**1.35 if heel=='stiletto6' else 255*(.66+.34*sh)
                col=np.repeat(light[:,:,None],3,axis=2)
            elif kind=='black': col=np.array([38,35,46])[None,None,:]*(.42+.63*sh)[:,:,None]+np.array([150,140,170])[None,None,:]*np.maximum(0,t-.8)[:,:,None]/.45*.9
            else: col=rgb.copy()
            # Same gentle contact occlusion as accepted out4, applied offline.
            for reach,opacity,tone in [(2.5,.45,[11,10,16] if kind=='black' else [160,100,90]),(9,.18,[11,10,16] if kind=='black' else [185,120,107])]:
                weight=(np.exp(-np.maximum(0,cut[None,:]-y)/reach)*opacity)[:,:,None]
                if kind=='cloth': tone=[135,133,143] if heel=='stiletto6' else [v*1.5 for v in tone]
                col=col*(1-weight)+np.array(tone)[None,None,:]*weight
            out[:,:,:3]=np.clip(col,0,255).astype('uint8')
            target=OUT/f'{heel}_{which}_{kind}.webp'
            temporary=target.with_suffix('.tmp')
            Image.fromarray(out).save(temporary,format='WEBP',quality=92,method=6,exact=True)
            temporary.replace(target)
        print(heel,which,Image.fromarray(a).getbbox())

# The accepted Mary Jane strap mask is an immutable product-camera asset.
# Returned-anatomy rebuilds leave it byte-exact.
