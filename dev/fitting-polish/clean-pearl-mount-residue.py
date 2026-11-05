#!/usr/bin/env python3
"""Remove two detached skin slivers above the far-side worn pearl mount.

Run AFTER worn-accessory, crystal-repair and thin-height exporters. These three
reviewed source-coordinate rectangles stop immediately above the first actual
pearl. Preserve every RGBA pixel outside them; do not move any strand, shoe or
leg. Pillow only, idempotent; final encoded invariance is independently checked.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'qa/pearl-mount-residue'
OUT.mkdir(parents=True, exist_ok=True)
ROIS = {'kitten': (365, 620, 430, 683),
        'stiletto6': (365, 620, 430, 671),
        'stiletto9': (365, 620, 430, 671)}
report = {'status': 'PASS', 'checks': []}
sheet = Image.new('RGB', (1440, 1080), '#243d3a')
for row, (style, roi) in enumerate(ROIS.items()):
    path = ROOT / f'assets/fitting2d/accessories/{style}_strap_pearl.webp'
    before = Image.open(path).convert('RGBA')
    after = before.copy()
    after.paste((0, 0, 0, 0), roi)
    removed = sum(before.getchannel('A').crop(roi).histogram()[1:])
    assert after.getchannel('A').getbbox(), style + ' lost its pearls'
    after.save(path, lossless=True, exact=True)
    encoded = Image.open(path).convert('RGBA')
    assert encoded.tobytes() == after.tobytes(), style + ' encoded RGBA drift'
    x0, y0, x1, y1 = roi
    for box in ((0, 0, 1024, y0), (0, y1, 1024, 1024),
                (0, y0, x0, y1), (x1, y0, 1024, y1)):
        assert before.crop(box).tobytes() == encoded.crop(box).tobytes(), (style, box)
    assert encoded.getchannel('A').crop(roi).getbbox() is None
    report['checks'].append({'style': style, 'roi': roi, 'removedAlphaPixels': removed,
                              'outsideRgbaExact': True, 'encodedRgbaExact': True})
    for col, (background, painting) in enumerate((('#f3fff8', before), ('#f3fff8', after),
                                                  ('#243d3a', before), ('#243d3a', after))):
        tile = Image.new('RGBA', (1024, 1024), background)
        tile.alpha_composite(painting)
        tile = tile.crop((355, 620, 625, 820)).resize((360, 300), Image.Resampling.LANCZOS)
        sheet.paste(tile, (col * 360, row * 360))
        ImageDraw.Draw(sheet).text((col * 360 + 10, row * 360 + 315),
                                   style + (' before' if col % 2 == 0 else ' after'), fill='#fc8cb4')
sheet.save(OUT / 'before-after.jpg', quality=96)
(OUT / 'report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
