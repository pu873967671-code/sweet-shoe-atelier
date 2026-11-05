#!/usr/bin/env python3
"""Seat retained painted bands on their camera's far collar; Pillow only.

The former height warp left the curled far tip suspended outside the shoe.
Tuck its far third behind the original collar silhouette, and mend
the extraction slit in the satin. Jewellery, near mount and body stay exact.
Immutable inputs make this finish safe to repeat after source exporters.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name('product-thin-source')
SOURCE.mkdir(exist_ok=True)
OUT = ROOT / 'qa/product-thin-mounts'
OUT.mkdir(parents=True, exist_ok=True)
STYLES = ['block', 'kitten', 'stiletto6', 'stiletto9', 'platform']
report = {'styles': [], 'bodyAndWornUntouched': True}
sheet = Image.new('RGB', (1600, len(STYLES) * 360), '#243d3a')

for row, heel in enumerate(STYLES):
    base = Image.open(ROOT / f'assets/shoe2d/{heel}_base.webp').convert('RGBA')
    files = {}
    for suffix in ['', '_tint']:
        name = f'{heel}_strap_thin{suffix}.webp'
        path = ROOT / 'assets/shoe2d/accessories' / name
        original = SOURCE / name
        if not original.exists():
            original.write_bytes(path.read_bytes())
        files[suffix] = Image.open(original).convert('RGBA')
    before = files['']
    alpha = before.getchannel('A')
    left = alpha.getbbox()[0]
    collar = [next((y for y in range(640) if base.getpixel((x, y))[3] > 200), 640) for x in range(1024)]
    # Tuck the far portion behind its real silhouette. This is the
    # authored far-side occlusion, not a screen-space clip or shoe resize.
    end = 650
    after = {}
    repaired = 0
    for suffix, source in files.items():
        result = source.copy()
        pixels = result.load()
        # Rejoin only short internal extraction gaps, using neighbouring
        # painted satin; never invent a rectangular patch or change buckle.
        for y in range(150, 400):
            xs = [x for x in range(525, end) if pixels[x, y][3] > 200]
            for x0, x1 in zip(xs, xs[1:]):
                if 1 < x1-x0 <= 28:
                    a, b = pixels[x0, y], pixels[x1, y]
                    for x in range(x0+1, x1):
                        t = (x-x0)/(x1-x0)
                        pixels[x, y] = tuple(round(a[c]*(1-t)+b[c]*t) for c in range(4))
                        if not suffix:
                            repaired += 1
        # Far tip lies behind the rolled collar: hide the curled dangling
        # underside; source alpha preserves the sewn overlap at the lip.
        for x in range(left, end):
            for y in range(150, 400):
                r, g, b, a = pixels[x, y]
                # Original collar alpha supplies antialiasing and contact.
                pixels[x, y] = (r, g, b, round(a*base.getpixel((x,y))[3]/255))
        assert result.crop((650, 0, 1024, 640)).tobytes() == source.crop((650, 0, 1024, 640)).tobytes()
        path = ROOT / f'assets/shoe2d/accessories/{heel}_strap_thin{suffix}.webp'
        temp = path.with_suffix('.tmp.webp')
        result.save(temp, lossless=True, exact=True)
        temp.replace(path)
        after[suffix] = result
    # Both the paint and its fabric mask must reach the far lip.
    contact = []
    for suffix in ['', '_tint']:
        a = after[suffix].getchannel('A')
        count = sum(a.getpixel((x, collar[x]+offset)) > 100 for x in range(left, end) for offset in range(0, 4))
        assert count >= 12, (heel, suffix, 'missing sewn collar contact', count)
        contact.append(count)
    report['styles'].append({'style': heel, 'collarContacts': contact, 'slitPixelsRepaired': repaired, 'nearMountExactFromX': 650})
    for col, (background, layer) in enumerate([('#f3fff8', before), ('#f3fff8', after['']), ('#243d3a', before), ('#243d3a', after[''])]):
        model = Image.new('RGBA', base.size, background)
        model.alpha_composite(base)
        model.alpha_composite(layer)
        crop = model.crop((460, 130, 820, 430)).resize((400, 333), Image.Resampling.LANCZOS)
        sheet.paste(crop, (col*400, row*360))
        ImageDraw.Draw(sheet).text((col*400+10, row*360+338), heel+' '+('before' if col%2 == 0 else 'after'), fill='#f77eaf')

sheet.save(OUT / 'before-after.jpg', quality=96)
(OUT / 'report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
