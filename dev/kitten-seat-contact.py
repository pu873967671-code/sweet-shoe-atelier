#!/usr/bin/env python3
"""Kitten review: actual pair/reference, native 3x counters, original sole evidence."""
import argparse
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=ROOT/'qa/kitten-0507/after')
parser.add_argument('--output', type=Path)
args = parser.parse_args()
QA = args.source.resolve()
BG, INK = '#f7f1eb', '#423642'
sheet = Image.new('RGB', (1900, 2920), BG)
d = ImageDraw.Draw(sheet)
face = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(face, 22)
title = ImageFont.truetype(face, 30)

def flatten(im):
    bg = Image.new('RGBA', im.size, BG)
    bg.alpha_composite(im.convert('RGBA'))
    return bg.convert('RGB')

def tile(path, box, label):
    x, y, w, h = box
    d.text((x, y), label, font=font, fill=INK)
    im = flatten(Image.open(path))
    im.thumbnail((w, h-32), Image.Resampling.LANCZOS)
    sheet.paste(im, (x+(w-im.width)//2, y+32+(h-32-im.height)//2))

d.text((20, 15), 'Kitten | independent 3cm fitting / developer visual review', font=title, fill=INK)
d.text((20, 56), 'Actual /usr/bin/chromium. Whole-source placement, raised-heel v2 rear, rigid original shoes.', font=font, fill=INK)
tile(QA/'kitten-white-390.png', (20, 100, 235, 470), '390 x 844')
tile(QA/'kitten-white-1920.png', (280, 100, 650, 470), '1920 x 1080')
tile(QA/'kitten-white-1920-pair.png', (950, 100, 565, 470), 'Actual fitting pair')
tile(ROOT/'assets/src-user-legs-20261029/pair-reference-user.png', (1535, 100, 345, 470), 'Pair reference')
shoe = Image.open(QA/'kitten-product-1920.png').convert('RGBA')
for col, side in enumerate(['front', 'rear']):
    x = 20+col*940
    for kind in ['white', 'bare', 'black']:
        im = shoe.copy()
        foot = Image.open(QA/f'kitten-{kind}-{side}-native.png').convert('RGBA')
        im.alpha_composite(foot.crop((0, 1500, 1024, 2140)))
        im.save(QA/f'{side}-{kind}-shoe-native.png')
    tile(QA/f'{side}-white-shoe-native.png', (x, 590, 920, 530), f'{side.title()} / white / original rigid shoe')
    for idx, kind in enumerate(['white', 'bare']):
        im = flatten(Image.open(QA/f'{side}-{kind}-shoe-native.png').crop((790, 0, 960, 225)))
        im = im.resize((510, 675), Image.Resampling.LANCZOS)
        im.save(QA/f'{side}-{kind}-counter-3x.png')
        cx = x+(0 if idx == 0 else 470)
        d.text((cx, 1140), f'{side} / {kind} counter / 3x', font=font, fill=INK)
        sheet.paste(im.crop((35, 0, 505, 675)), (cx, 1175))
    im = flatten(Image.open(QA/f'{side}-white-shoe-native.png').crop((320, 280, 740, 450)))
    im = im.resize((840, 340), Image.Resampling.LANCZOS)
    im.save(QA/f'{side}-white-instep-2x.png')
    d.text((x, 1880), f'{side} / white instep and collar / 2x', font=font, fill=INK)
    sheet.paste(im, (x+35, 1915))
tile(ROOT/'qa/kitten-0507/independent-sole-overlay.jpg', (20, 2280, 1860, 570),
     'Full unoccluded source sole vs original visible insole edge: cyan insole, pink source alpha')
d.text((20, 2870), 'Visible-edge residuals are diagnostics. Native/browser images remain the artistic acceptance evidence.', font=font, fill=INK)
out = args.output or ROOT/'qa/contact'/f'{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.jpg'
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out, quality=94, optimize=True)
print(out)
