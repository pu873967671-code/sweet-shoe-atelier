#!/usr/bin/env python3
"""Feather the supplied Chantilly artwork into a repeatable local tile."""
from pathlib import Path
from PIL import Image, ImageChops

root = Path(__file__).resolve().parents[1]
source = Image.open(root / 'assets/materials/lace_tile.webp').convert('RGBA')
if source.size != (512, 512):
    raise ValueError('Expected a 512 × 512 lace source')
offset = ImageChops.offset(source, 256, 256)
mask = Image.new('L', source.size)
mask.putdata([round(255 * max(0, 1 - abs(x - 256) / 64, 1 - abs(y - 256) / 64))
              for y in range(512) for x in range(512)])
Image.composite(source, offset, mask).save(root / 'assets/materials/lace_seamless.webp', quality=80, method=6)
