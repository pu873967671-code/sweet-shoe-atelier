#!/usr/bin/env python3
"""Remove the detached shoe-edge remnant from the wedge Grand satin."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[2]
source = root / 'dev/fitting-polish/wedge-grand-source'
target = root / 'assets/shoe2d/accessories'
cut = Image.new('L', (1024, 640))
draw = ImageDraw.Draw(cut)
draw.polygon([(890, 228), (910, 228), (911, 250), (911, 285),
              (912, 310), (915, 320), (890, 320)], fill=255)
for suffix in ['', '_tint']:
    name = 'wedge_decoration_big' + suffix + '.webp'
    image = Image.open(source / name).convert('RGBA')
    alpha = image.getchannel('A')
    alpha.paste(0, mask=cut)
    image.putalpha(alpha)
    image.save(target / name, format='WEBP', lossless=True, exact=True, method=6)
