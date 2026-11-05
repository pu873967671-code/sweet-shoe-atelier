#!/usr/bin/env python3
"""Soften retained fitting skin paintings, preserving each camera and masks.

PIL-only, deterministic offline finish. Immutable input copies live beside this
script in source-skin; shoe/upper/occlusion pixels are never regenerated here.
The result removes source veins and ankle-bone values, rounds small contour
corners, and retains broad warm shading. No generated-art claim is made.
"""
from pathlib import Path
import argparse
import json
import shutil
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent / 'source-skin'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, default=ROOT / 'assets/fitting2d')
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
SOURCE.mkdir(parents=True, exist_ok=True)
PALETTE = [(0, '#e9b9a7'), (.19, '#f4cbb4'), (.36, '#ffdfc7'),
           (.57, '#ffe0ca'), (.76, '#f5c9b1'), (.91, '#e8b6a3'), (1, '#dda998')]
STOPS = [(t, tuple(bytes.fromhex(c[1:]))) for t, c in PALETTE]


def colour(x):
    t = max(0, min(1, (x - 475) / 375))
    for (a, left), (b, right) in zip(STOPS, STOPS[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            return tuple(round(l + (r - l) * f) for l, r in zip(left, right))
    return STOPS[-1][1]


# One continuous plane follows the shin into the sloping instep. It cannot
# retain source creases, vein pixels, repair rectangles or malleolus spots.
strip = Image.new('RGB', (1600, 1))
strip.putdata([colour(x) for x in range(strip.width)])
paint = Image.new('RGB', (1024, 1024))
for y in range(1024):
    shift = round(max(0, y - 400) * .36)
    paint.paste(strip.crop((shift, 0, shift + 1024, 1)), (0, y))

report = {'styles': [], 'rounded_contours': True, 'source_detail_retained': False, 'geometry': {}}
for path in sorted((ROOT / 'assets/fitting2d').glob('*_legs.webp')):
    original = SOURCE / path.name
    if not original.exists():
        shutil.copy2(path, original)
    source = Image.open(original).convert('RGBA')
    assert source.size == paint.size, path
    alpha = source.getchannel('A')
    # A broad blur locates a continuous outline; a narrow coverage ramp then
    # restores crisp antialiasing instead of leaving a translucent halo.
    rounded = alpha.filter(ImageFilter.GaussianBlur(4)).point(
        [max(0, min(255, round((v - 112) * 255 / 32))) for v in range(256)])
    result = paint.copy().convert('RGBA')
    result.putalpha(rounded)
    target = args.out / path.name
    temporary = target.with_suffix('.webp.tmp')
    try:
        result.save(temporary, format='WEBP', lossless=True, method=6)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    heel = path.stem.removesuffix('_legs')
    report['styles'].append(heel)
    # Art acceptance data measures actual coverage rather than copying renderer
    # arithmetic: source-camera bounds, disconnected runs and rounding distance.
    old = alpha.point(lambda v: 255 if v > 127 else 0).tobytes()
    new = rounded.point(lambda v: 255 if v > 127 else 0).tobytes()
    changed = sum(a != b for a, b in zip(old[400*1024:], new[400*1024:]))
    original_area = old[400*1024:].count(255)
    maximum_shift = 0
    old_disconnected = new_disconnected = 0
    for y in range(400, 1024):
        a, b = old[y*1024:(y+1)*1024], new[y*1024:(y+1)*1024]
        aruns = a.count(b'\x00\xff') + bool(a[0])
        bruns = b.count(b'\x00\xff') + bool(b[0])
        old_disconnected += aruns > 1
        new_disconnected += bruns > 1
        if aruns == bruns == 1:
            maximum_shift = max(maximum_shift, abs(a.find(b'\xff')-b.find(b'\xff')),
                                abs(a.rfind(b'\xff')-b.rfind(b'\xff')))
    report['geometry'][heel] = {
        'source_bbox': alpha.getbbox(), 'rounded_bbox': rounded.getbbox(),
        'changed_lower_coverage_pixels': changed,
        'changed_lower_coverage_percent': round(changed * 100 / original_area, 3),
        'maximum_contiguous_row_edge_shift_px': maximum_shift,
        'source_disconnected_lower_rows': old_disconnected,
        'rounded_disconnected_lower_rows': new_disconnected,
    }
assert len(report['styles']) == 17, report
report_path = ROOT / 'qa/soft-skin-report.json'
report_path.write_text(json.dumps(report, indent=2) + '\n')

# Native-size crops make any outline fringe or repeated anatomy detail obvious.
sheet = Image.new('RGB', (1200, 900), '#f4fff7')
draw = ImageDraw.Draw(sheet)
for i, heel in enumerate(['flat', 'kitten', 'stiletto9', 'slingback']):
    skin = Image.open(args.out / (heel + '_legs.webp')).convert('RGBA')
    shoe = Image.open(ROOT / 'assets/fitting2d' / (heel + '_shoe.webp')).convert('RGBA')
    occlusion = Image.open(ROOT / 'assets/fitting2d' / (heel + '_occlusion.webp')).getchannel('A')
    from PIL import ImageChops
    skin.putalpha(ImageChops.subtract(skin.getchannel('A'), occlusion))
    skin.alpha_composite(shoe)
    for dark in (False, True):
        tile = Image.new('RGBA', (300, 420), '#223b36' if dark else '#f4fff7')
        view = skin.copy()
        view.thumbnail((300, 400), Image.Resampling.LANCZOS)
        tile.alpha_composite(view, ((300 - view.width) // 2, 0))
        x, y = i * 300, 450 if dark else 0
        sheet.paste(tile.convert('RGB'), (x, y))
        draw.text((x + 10, y + 410), heel, fill='white' if dark else '#31584a')
sheet.save(ROOT / 'qa/soft-skin-contact.jpg', quality=96)
print('PASS: softened17 camera-matched skin layers; no source veins/bone shading; crisp rounded alpha')
