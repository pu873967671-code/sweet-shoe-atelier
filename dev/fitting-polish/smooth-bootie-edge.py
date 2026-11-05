#!/usr/bin/env python3
"""Smooth the fitted bootie's front shaft edge without moving its mounts.

Works on a retained pre-polish kit and applies the same subpixel local warp to
paint and finish masks. All other pixels, including collar and sole, stay put.
"""
from pathlib import Path
import math
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'dev/fitting-polish/bootie-edge-source'
DEST = ROOT / 'assets/fitting2d'
shoe = Image.open(SOURCE / 'bootie_shoe.webp').convert('RGBA')
a = shoe.getchannel('A')
edges = []
for y in range(1024):
    edges.append(next((x for x in range(100, 600) if a.getpixel((x,y)) >= 128), 0))
# Smooth only where the closed shaft flows into the instep. Fade the warp
# into the untouched collar and toe, and feather the silhouette by one pixel.
def weight(y):
    return max(0, min(1, (y-420)/24, (835-y)/30))
def smooth(y):
    samples = [(edges[i], math.exp(-((i-y)/6)**2/2)) for i in range(max(0,y-18), min(1024,y+19)) if edges[i]]
    return sum(x*w for x,w in samples)/sum(w for _,w in samples)
shifts = [weight(y)*(smooth(y)-edges[y]) if edges[y] and weight(y) else 0 for y in range(1024)]
for part in ('shoe','upper','shadow','highlight'):
    im = Image.open(SOURCE / f'bootie_{part}.webp').convert('RGBA')
    src, out = im.load(), im.copy()
    dst = out.load()
    for y in range(421,835):
        edge = edges[y]
        if not edge: continue
        shift = shifts[y]
        for x in range(max(0,edge-5), min(1024,edge+18)):
            # Fade the displacement into the existing painted interior.
            taper = max(0, min(1, (edge+17-x)/12))
            sx = x-shift*taper
            x0 = math.floor(sx); f = sx-x0
            c0,c1 = src[x0,y],src[x0+1,y]
            alpha = c0[3]*(1-f)+c1[3]*f
            if alpha:
                rgb = [round((c0[k]*c0[3]*(1-f)+c1[k]*c1[3]*f)/alpha) for k in range(3)]
                dst[x,y] = (*rgb,round(alpha))
            else: dst[x,y] = (0,0,0,0)
    # A one-pixel horizontal feather removes the last stair steps at the
    # silhouette. Premultiplied sampling avoids a dark fringe in shoe paint.
    feather = out.copy(); fp = feather.load()
    for y in range(421,835):
        edge = edges[y]
        if not edge: continue
        for x in range(max(1,edge-4), min(1023,edge+5)):
            samples = [(dst[x-1,y],.25), (dst[x,y],.5), (dst[x+1,y],.25)]
            alpha = sum(c[3]*w for c,w in samples)
            if alpha:
                rgb = [round(sum(c[k]*c[3]*w for c,w in samples)/alpha) for k in range(3)]
                fp[x,y] = (*rgb, round(alpha))
            else: fp[x,y] = (0,0,0,0)
    out = feather
    # Keep the packaged painted shoe's accepted q95; masks remain lossless.
    out.save(DEST / f'bootie_{part}.webp', 'WEBP', quality=95, method=6, lossless=part!='shoe')
