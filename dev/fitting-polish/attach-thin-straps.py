#!/usr/bin/env python3
"""Seat the genuine worn 6/9cm satin bands against their own outer binding.

The height remap shortened these two bands before the outer quarter. Preserve
the original inner attachment and all pixels outside the authored seam ROI;
stretch only existing painted satin through the gap and tuck it at the original
shoe alpha. Run after thin-height accessory export. Pillow only, idempotent.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter
import json

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).with_name('strap-seam-source')
OUT = ROOT / 'qa/strap-seam'
OUT.mkdir(parents=True, exist_ok=True)
ROI = (510, 570, 710, 750)
report = {'styles': [], 'outsideRoiExact': True}
sheet = Image.new('RGB', (1600, 1040), '#f3fff8')
draw = ImageDraw.Draw(sheet)

for row, heel in enumerate(('stiletto6', 'stiletto9')):
    shoe = Image.open(ROOT / f'assets/fitting2d/{heel}_shoe.webp').convert('RGBA')
    legs = Image.open(ROOT / f'assets/fitting2d/{heel}_legs.webp').convert('RGBA')
    # The ivory binding is already in the immutable shoe painting. Never draw
    # satin on it: its unmodified edge sits in front of the new sewn endpoint.
    cutoff = shoe.getchannel('A').point(lambda a: 0 if a > 110 else 255)
    original = {}
    after = {}
    changed = {}
    for suffix in ('', '_tint'):
        name = heel + '_strap_thin' + suffix + '.webp'
        before = Image.open(SRC / name).convert('RGBA')
        result = before.copy()
        patch = before.crop((510, 570, 640, 750)).resize((170, 180), Image.Resampling.BICUBIC)
        region = Image.new('RGBA', (200, 180))
        region.paste(patch, (0, 0))
        region.putalpha(ImageChops.multiply(region.getchannel('A'), cutoff.crop(ROI)))
        result.paste(region, (510, 570))
        # Exact outside-ROI preservation, including fully transparent RGB.
        for box in ((0, 0, 1024, 570), (0, 750, 1024, 1024),
                    (0, 570, 510, 750), (710, 570, 1024, 750)):
            assert result.crop(box).tobytes() == before.crop(box).tobytes(), (heel, suffix, box)
        path = ROOT / 'assets/fitting2d/accessories' / name
        result.save(path, lossless=True, exact=True)
        encoded = Image.open(path).convert('RGBA')
        assert encoded.tobytes() == result.tobytes()
        original[suffix] = before
        after[suffix] = result
        changed[suffix or 'paint'] = sum(a != b for a, b in zip(before.getchannel('A').getdata(), result.getchannel('A').getdata()))
    # Verify contact against actual original binding, allowing antialiasing.
    near_shoe = shoe.getchannel('A').filter(ImageFilter.MaxFilter(5))
    before_contact = ImageChops.multiply(original[''].getchannel('A'), near_shoe).getbbox()
    contact = ImageChops.multiply(after[''].getchannel('A'), near_shoe).getbbox()
    assert contact, heel + ' sewn endpoint does not touch binding'
    report['styles'].append({'style': heel, 'roi': list(ROI), 'changedAlphaPixels': changed,
                             'beforeContact': before_contact, 'afterContact': contact,
                             'outsideRoiExact': True})
    for col, (background, state) in enumerate((('#f3fff8', 'before'), ('#f3fff8', 'after'),
                                               ('#243d3a', 'before'), ('#243d3a', 'after'))):
        layer = original[''] if state == 'before' else after['']
        model = Image.new('RGBA', (1024, 1024), background)
        model.alpha_composite(legs)
        model.alpha_composite(shoe)
        model.alpha_composite(layer)
        crop = model.crop((350, 530, 810, 825)).resize((400, 460), Image.Resampling.LANCZOS)
        sheet.paste(crop, (col * 400, row * 520))
        draw.text((col * 400 + 10, row * 520 + 474), heel + ' ' + state, fill='#fd78a6')
sheet.save(OUT / 'before-after.jpg', quality=96)
(OUT / 'report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
