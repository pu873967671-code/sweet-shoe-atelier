#!/usr/bin/env python3
"""Trim Grand ribbon tails from the retained accepted paintings.

The piecewise contours are hand-placed in each product camera: the raised
middle of each tail is a V-cut, not a straight clipped edge. Render at 4x for
smooth antialiasing and apply exactly the same coverage to paint and dye.
The worn view projects these same assets. Run after other Grand repairs.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'dev/fitting-polish/grand-tail-source'
DEST = ROOT / 'assets/shoe2d/accessories'
# Bottom boundaries, left to right in the 1024 x 640 product camera.
CUTS = {
    'flat': [(0, 340), (910, 340), (933, 317), (960, 341), (964, 321), (972, 302), (992, 316), (1024, 316)],
    'block': [(0, 295), (918, 295), (930, 278), (943, 292), (952, 272), (970, 253), (1004, 279), (1024, 279)],
    'wedge': [(0, 291), (910, 291), (935, 266), (960, 292), (965, 282), (975, 264), (1000, 286), (1024, 286)],
    'platform': [(0, 295), (918, 295), (930, 278), (943, 292), (952, 272), (970, 253), (1004, 279), (1024, 279)],
}
SCALE = 4
for family, boundary in CUTS.items():
    paint = Image.open(SOURCE / f'{family}_decoration_big.webp').convert('RGBA')
    mask = Image.new('L', (1024 * SCALE, 640 * SCALE), 0)
    points = [(0, 0), (1024, 0)] + list(reversed(boundary))
    ImageDraw.Draw(mask).polygon([(x*SCALE, y*SCALE) for x, y in points], fill=255)
    mask = mask.resize((1024, 640), Image.Resampling.LANCZOS)
    alpha = ImageChops.multiply(paint.getchannel('A'), mask)
    paint.putalpha(alpha)
    paint.save(DEST / f'{family}_decoration_big.webp', lossless=True, method=6)
    tint = Image.new('RGBA', paint.size, (255, 255, 255, 0))
    tint.putalpha(alpha)
    tint.save(DEST / f'{family}_decoration_big_tint.webp', lossless=True, method=6)
