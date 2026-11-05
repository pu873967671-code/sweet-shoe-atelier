#!/usr/bin/env python3
"""Extract baked collar skin for draw-only hosiery, retaining accepted artwork.

The shoe painting contains a few skin pixels on top of the independently
painted ankle. A sock behind that painting cannot cover them. These additive
semantic masks allow the same cloth to cover those pixels after shoe shading.
No accepted source layer is edited. Pillow and the local Node registry suffice.
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets/fitting2d'
OUT = ROOT / 'qa/hosiery-collars'
OUT.mkdir(exist_ok=True)
HEELS = json.loads(subprocess.check_output(
    ['node', '-e', "console.log(JSON.stringify(require('./game.js').opts.heel.map(([id])=>id)))"],
    cwd=ROOT, text=True))


def extract(heel):
    shoe, upper, legs = [Image.open(ASSETS / f'{heel}_{part}.webp').convert('RGBA')
                         for part in ['shoe', 'upper', 'legs']]
    result = Image.new('RGBA', shoe.size)
    # The accepted open-toe kit already has complete explicit skin/cream-shell
    # semantics. Never infer its warm cream lining as skin by hue alone.
    if heel == 'crystalsandal':
        return result, shoe, []
    sp, up, lp = shoe.load(), upper.load(), legs.load()
    near = legs.getchannel('A').filter(ImageFilter.MaxFilter(7)).load()
    seeds, allowed = [], set()
    for y in range(300, 900):
        for x in range(240, 900):
            r, g, b, a = sp[x, y]
            lr, lg, lb, la = lp[x, y]
            # Pink undertones distinguish skin from cream/gold binding. Seed
            # colours must also match the actual ankle directly underneath;
            # this keeps pearls, metallic buckles and satin ribbons fixed.
            warm = r-g > 12 and g-b > 4 and r-g > 1.2*(g-b)
            if a <= 15 or up[x, y][3] >= 40 or near[x, y] <= 20 or not warm:
                continue
            distance = max(abs(r-lr), abs(g-lg), abs(b-lb))
            if distance < 85:
                allowed.add((x, y))
            if la > 160 and distance < 29 and r-g > 18 and g-b > 5 and r-g > 1.4*(g-b):
                seeds.append((x, y))
    selected = set(seeds)
    queue = deque(seeds)
    while queue:
        x, y = queue.popleft()
        for dx, dy in [(-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)]:
            point = x+dx, y+dy
            if point in allowed and point not in selected:
                selected.add(point)
                queue.append(point)
    # Close a one-pixel extraction fringe, still inside skin-coloured paint
    # and outside the immutable dye/trim mask. No detached paint is introduced.
    fringe = {p for x, y in selected for p in [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]
              if p in allowed}
    selected.update(fringe)
    rp = result.load()
    for x, y in selected:
        rp[x, y] = (255, 255, 255, 255)
    return result, shoe, sorted(selected)


report = {'status': 'PASS', 'styles': {}, 'originalLayersUnchanged': True}
sheet = Image.new('RGB', (1400, ((len(HEELS)+4)//5)*400), '#263a34')
draw = ImageDraw.Draw(sheet)
for index, heel in enumerate(HEELS):
    originals = {part: hashlib.sha256((ASSETS/f'{heel}_{part}.webp').read_bytes()).hexdigest()
                 for part in ['shoe', 'upper', 'legs', 'occlusion']}
    mask, shoe, points = extract(heel)
    repeated, _, _ = extract(heel)
    assert repeated.tobytes() == mask.tobytes(), ('nondeterministic extraction', heel)
    path = ASSETS / f'{heel}_hosiery.webp'
    # A one-pixel transparent sentinel explicitly marks cameras with no
    # overpaint and lets runtime skip an unnecessary cloth/texture pass.
    encoded = mask if points else Image.new('RGBA', (1, 1))
    encoded.save(path, lossless=True, exact=True)
    assert Image.open(path).convert('RGBA').tobytes() == encoded.tobytes()
    assert all(hashlib.sha256((ASSETS/f'{heel}_{part}.webp').read_bytes()).hexdigest() == digest
               for part, digest in originals.items()), ('accepted source changed', heel)
    bounds = mask.getbbox()
    report['styles'][heel] = {'pixels': len(points), 'bounds': bounds,
                              'encodedSize': list(encoded.size),
                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                              'sourceSHA256': originals}
    bg = Image.new('RGBA', shoe.size, '#263a34')
    bg.alpha_composite(shoe)
    green = Image.new('RGBA', shoe.size, '#7aff9a')
    green.putalpha(mask.getchannel('A'))
    bg.alpha_composite(green)
    crop = bg.crop((620, 350, 850, 700))
    crop.thumbnail((250, 350), Image.Resampling.LANCZOS)
    x, y = (index % 5)*280, (index // 5)*400
    sheet.paste(crop.convert('RGB'), (x, y))
    draw.text((x+4, y+355), f'{heel}: {len(points)} skin pixels', fill='white')
sheet.save(OUT/'source-contact.jpg', quality=97)
(OUT/'source-report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'status': 'PASS', 'styles': len(HEELS),
                  'pixels': sum(row['pixels'] for row in report['styles'].values()),
                  'originalLayersUnchanged': True}))
