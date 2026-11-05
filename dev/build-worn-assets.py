#!/usr/bin/env python3
"""Precompute ivory shoe masks; the browser never reads image pixels.
Warm skin and natural soles remain outside the mask. Re-run when leg art changes.
"""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
for heel in ['flat','block','kitten','wedge']:
    source=Image.open(ROOT/f'assets/legs/leg_{heel}.webp').convert('RGBA')
    mask=Image.new('RGBA',source.size)
    pixels=[]
    for r,g,b,a in source.getdata():
        # White satin is neutral; skin and wooden soles have a strong warm chroma.
        coverage=max(0,min(1,(24-(r-b))/8,(20-(g-b))/8))
        pixels.append((255,255,255,round(a*coverage)))
    mask.putdata(pixels)
    mask.save(ROOT/f'assets/legs/mask_{heel}.webp',lossless=True)
    print(heel,source.size)

# Continue the ankle into a softly tapered mid-calf, precomputed for cross-origin-safe drawing.
for heel, (left, right) in {'flat':(750,1008),'block':(665,1024),'kitten':(658,1004),'wedge':(770,1088)}.items():
    source=Image.open(ROOT/f'assets/legs/leg_{heel}.webp').convert('RGBA')
    strip=source.crop((left,0,right,2))
    calf=Image.new('RGBA',(1200,1200))
    for y in range(1200):
        t=y/1199
        width=round((right-left)*(1+.48*(1-t)**.8))
        center=(left+right)/2-22*(1-t)
        calf.paste(strip.resize((width,1),Image.Resampling.BICUBIC),(round(center-width/2),y))
    calf.save(ROOT/f'assets/legs/calf_{heel}.webp',lossless=True)
