#!/usr/bin/env python3
"""Restore extracted interior piping alpha; original RGB and exterior stay exact."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name('platform-binding-source')
OUT = ROOT / 'qa/session-2054-platform-binding'
OUT.mkdir(exist_ok=True)
parts = ['shoe', 'occlusion']
before = {part: Image.open(SOURCE/f'platform_{part}.webp').convert('RGBA') for part in parts}
after = {part: im.copy() for part, im in before.items()}
pixels = {part: im.load() for part, im in after.items()}
original = before['shoe'].load()
# The existing inner piping edge, in the immutable 1024px camera. No edge
# is drawn or moved: these samples locate its retained opaque painted run.
curve = [(480,822),(500,818),(520,811),(540,798),(560,777),(580,749),
         (600,717),(620,685),(640,653),(660,621),(680,588),(700,554),
         (720,518),(730,499),(735,489)]
changed = []
for x in range(480,736):
    left,right = next((a,b) for a,b in zip(curve,curve[1:]) if a[0] <= x <= b[0])
    expected = round(left[1]+(right[1]-left[1])*(x-left[0])/(right[0]-left[0]))
    top = next(y for y in range(expected-4,expected+5) if original[x,y][3] > 150)
    # The cloth below is already continuous. Fill only the enclosed alpha
    # extraction slit between its painted cream piping and that cloth.
    bottom = next(y for y in range(top+3,top+48) if all(original[x,y+n][3] > 240 for n in range(12)))
    for y in range(top+4,bottom):
        if original[x,y][3] >= 240:
            continue
        for part in parts:
            r,g,b,a = pixels[part][x,y]
            pixels[part][x,y] = (r,g,b,255)
        changed.append((x,y))

assert changed
bounds = [min(p[0] for p in changed),min(p[1] for p in changed),max(p[0] for p in changed)+1,max(p[1] for p in changed)+1]
report = {'status':'PASS','changedPixels':len(changed),'changedBounds':bounds,'layers':{}}
allowed = set(changed)
for part in parts:
    old,new = before[part],after[part]
    oldp,newp = old.load(),new.load()
    changed_part = 0
    for y in range(1024):
        for x in range(1024):
            a,b = oldp[x,y],newp[x,y]
            assert a[:3] == b[:3], ('RGB changed',part,x,y)
            if a != b:
                assert (x,y) in allowed and b[3] >= a[3], ('outside interior slit',part,x,y)
                changed_part += 1
    if part == 'shoe':
        # Restoring interior holes must preserve every occupied column's
        # first/last silhouette pixel, including toe and sole contacts.
        for x in range(1024):
            aa = [y for y in range(1024) if oldp[x,y][3] > 127]
            bb = [y for y in range(1024) if newp[x,y][3] > 127]
            assert ((aa[0],aa[-1]) if aa else None) == ((bb[0],bb[-1]) if bb else None), ('exterior moved',x)
    destination = ROOT/f'assets/fitting2d/platform_{part}.webp'
    new.save(destination,lossless=True,exact=True)
    assert Image.open(destination).convert('RGBA').tobytes() == new.tobytes()
    report['layers'][part] = {'changedPixels':changed_part,'rgbaSHA256':hashlib.sha256(new.tobytes()).hexdigest(),'allRGBExact':True,'allOutsidePixelsExact':True,'exteriorColumnBoundsExact':part=='shoe'}

sheet = Image.new('RGB',(1440,800),'#263a34')
draw = ImageDraw.Draw(sheet)
for i,phase in enumerate([before,after]):
    for j,(box,size) in enumerate([((470,760,580,835),(660,450)),((580,480,740,780),(330,618))]):
        im = phase['shoe'].crop(box)
        im = im.resize(size,Image.Resampling.NEAREST)
        sheet.paste(im,(i*720+j*350,35),im)
    draw.text((i*720+8,8),'BEFORE: extracted slits' if i==0 else 'AFTER: continuous original cream binding',fill='white')
sheet.save(OUT/'before-after.png')
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
