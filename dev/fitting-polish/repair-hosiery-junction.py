#!/usr/bin/env python3
"""Local, deterministic REVIEW01:11 alpha repair; no camera/anatomy change.

Run after skin/style exporters. Retained inputs make reruns idempotent. Only the
tiny inner-instep bend and the ankle/counter join may change. Shoe, fabric,
ornament, toe/floor and the remainder of every skin silhouette stay exact.
"""
from pathlib import Path
import json
import math
import shutil
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'assets/fitting2d'
SOURCE = Path(__file__).resolve().parent / 'hosiery-junction-source'
OUT = ROOT / 'qa/hosiery-junction'
SOURCE.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
report = {'styles': [], 'camera_and_pair_unchanged': True}


def original(path):
    retained = SOURCE / path.name
    if not retained.exists():
        shutil.copy2(path, retained)
    return Image.open(retained).convert('RGBA')


def edge(alpha, y):
    row = [x for x in range(300, 550) if alpha.getpixel((x, y)) >= 128]
    if not row:
        return None
    x = min(row)
    before = alpha.getpixel((x-1, y))
    after = alpha.getpixel((x, y))
    return x-1+(128-before)/max(1, after-before)


def palette(x, y):
    stops = [(0, (233,185,167)), (.19,(244,203,180)), (.36,(255,223,199)),
             (.57,(255,224,202)), (.76,(245,201,177)), (.91,(232,182,163)),
             (1,(221,169,152))]
    t = max(0, min(1, (x+round(max(0,y-400)*.36)-475)/375))
    for (a,left),(b,right) in zip(stops,stops[1:]):
        if t <= b:
            f=(t-a)/(b-a)
            return tuple(round(l+(r-l)*f) for l,r in zip(left,right))
    return stops[-1][1]


for path in sorted(ART.glob('*_legs.webp')):
    heel = path.stem.removesuffix('_legs')
    skin = original(path)
    occ_path = ART / f'{heel}_occlusion.webp'
    occ = original(occ_path)
    shoe = Image.open(ART / f'{heel}_shoe.webp').convert('RGBA')
    before = skin.copy()
    a = skin.getchannel('A')
    before_a = a.copy()
    shoe_a = shoe.getchannel('A')
    old_occ = occ.getchannel('A')
    oc = old_occ.copy()
    edges = {y:edge(a,y) for y in range(580,761)}
    smoothed = {}
    for y in range(620,726):
        e = edges[y]
        if e is None:
            continue
        points = [(edges[yy],math.exp(-((yy-y)/12)**2/2))
                  for yy in range(y-30,y+31) if edges[yy] is not None]
        average = sum(v*w for v,w in points)/sum(w for _,w in points)
        fade = min(1,max(0,(y-620)/20),max(0,(725-y)/20))
        smoothed[y] = e+max(-3,min(3,average-e))*fade
    # Only sources with the inherited little slope ledge need reshaping.
    contour = bool(smoothed) and max(abs(smoothed[y]-edges[y]) for y in range(650,701)) > 1.05
    changed_contour = 0
    if contour:
        for y, target in smoothed.items():
            old = edges[y]
            delta = target-old
            for x in range(max(0,int(old)-7),min(1024,int(old)+8)):
                xx = x-delta
                lo = math.floor(xx)
                f = xx-lo
                value = round(before_a.getpixel((lo,y))*(1-f)+before_a.getpixel((lo+1,y))*f)
                if value != a.getpixel((x,y)):
                    a.putpixel((x,y),value)
                    changed_contour += 1
    joined = cleared = 0
    for y in range(410,631):
        xs = [x for x in range(650,831) if before_a.getpixel((x,y)) >= 128]
        if not xs:
            continue
        right = max(xs)
        # Find the actual camera's counter, within the existing ankle edge.
        nearby = [x for x in range(max(650,right-12),min(831,right+17))
                  if shoe_a.getpixel((x,y)) >= 128]
        if not nearby:
            continue
        contact = min(nearby)
        # Ignore extraction slivers in the cream piping: the final contact is
        # the first continuously opaque stretch of the actual counter.
        solid = [x for x in range(max(650,right-1),min(824,right+18))
                 if min(shoe_a.getpixel((xx,y)) for xx in range(x,x+7)) >= 240]
        if solid:
            contact = max(contact,min(solid))
        if contact > right and heel != 'bootie':
            # Continue skin/fabric two pixels beneath piping; shoe paints last.
            for x in range(right,contact+(3 if solid else 1)):
                if a.getpixel((x,y)) < 255:
                    a.putpixel((x,y),255)
                    joined += 1
        # A destructive occlusion mask must not create an uncovered seam where
        # the actual shoe is transparent. Restrict this to the narrow junction.
        for x in range(max(650,right-15),min(831,max(right,contact)+4)):
            value = 0 if heel != 'bootie' and shoe_a.getpixel((x,y)) < 250 and a.getpixel((x,y)) > 127 else oc.getpixel((x,y))
            if value != oc.getpixel((x,y)):
                oc.putpixel((x,y),value)
                cleared += 1
    # New edge pixels inherit the identical broad peach plane, never dark RGB
    # carried by fully transparent extraction pixels.
    for y in range(410,726):
        for x in range(300,835):
            if a.getpixel((x,y)) > before_a.getpixel((x,y)):
                skin.putpixel((x,y),(*palette(x,y),a.getpixel((x,y))))
    skin.putalpha(a)
    occ.putalpha(oc)
    for target,result in [(path,skin),(occ_path,occ)]:
        # Unchanged files retain their exact original compressed bytes.
        retained = SOURCE / target.name
        if ImageChops.difference(original(target),result).getbbox() is None:
            shutil.copy2(retained,target)
        else:
            tmp=target.with_suffix('.webp.tmp')
            result.save(tmp,format='WEBP',lossless=True,exact=True,method=6)
            tmp.replace(target)
    diff = ImageChops.difference(before.getchannel('A'),a)
    occ_diff = ImageChops.difference(old_occ,oc)
    assert all(diff.getpixel((x,y)) == 0 for x,y in [(547,0),(547,170),(519,350),(300,850)])
    report['styles'].append({'heel':heel,'contour_pixels':changed_contour,'filled_join_pixels':joined,
                             'occlusion_pixels':cleared,'skin_change_bounds':diff.getbbox(),
                             'occlusion_change_bounds':occ_diff.getbbox()})
    # Pixel-scale before/after on dark background exposes even a one-pixel gap.
    sheet=Image.new('RGB',(640,520),'#254737')
    for index,(s,o) in enumerate([(before,old_occ),(skin,oc)]):
        view=s.copy();view.putalpha(ImageChops.subtract(view.getchannel('A'),o))
        tile=Image.new('RGBA',(1024,1024),'#254737');tile.alpha_composite(view);tile.alpha_composite(shoe)
        sheet.paste(tile.crop((675,410,835,650)).resize((320,480)),(index*320,0))
    ImageDraw.Draw(sheet).text((8,492),heel+'  BEFORE                              AFTER',fill='white')
    sheet.save(OUT/f'{heel}-counter.png')

(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',len(report['styles']),'localized source-camera junctions; no pair/camera change')
