#!/usr/bin/env python3
"""Extract two genuine camera-matched satin bows onto immutable slingbacks.

Only the hand-reviewed bow contour uses edited pixels. The accepted body,
heel, outsole and fitting anatomy remain unchanged everywhere else.
"""
from pathlib import Path
import json
import shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'dev/bowsling-source'
CONTOURS = {
    'product': [(232,410),(238,390),(253,371),(274,349),(299,327),(317,318),(329,319),(343,331),(358,349),(369,369),(375,381),(394,373),(411,374),(417,384),(448,380),(483,381),(515,388),(541,399),(555,407),(548,432),(533,461),(516,491),(502,504),(522,523),(478,525),(450,528),(438,518),(424,495),(411,467),(400,437),(398,425),(376,420),(359,414),(342,428),(330,443),(315,461),(299,447),(286,435),(267,430),(248,423),(236,419)],
    'fitting': [(251,817),(254,804),(269,783),(292,765),(321,747),(337,741),(345,744),(357,759),(368,782),(373,800),(388,798),(400,801),(410,797),(440,795),(469,796),(493,797),(515,804),(531,814),(530,832),(520,860),(506,882),(499,890),(494,903),(497,909),(477,914),(455,927),(433,938),(421,922),(410,899),(401,871),(392,846),(369,840),(349,831),(329,840),(308,845),(282,849),(254,851),(245,853),(257,836)]
}

def rgba(path):
    return np.array(Image.open(path).convert('RGBA'))

def save(path, pixels):
    Image.fromarray(np.clip(pixels, 0, 255).astype('uint8')).save(path, lossless=True, method=6, exact=True)

metadata = {}
for view, folder, part in [('product', 'shoe2d', 'base'), ('fitting', 'fitting2d', 'shoe')]:
    original = rgba(ROOT / f'assets/{folder}/slingback_{part}.webp')
    generated = Image.open(SRC / f'{view}.png').convert('RGBA')
    size = (original.shape[1], original.shape[0])
    if view == 'product':
        bounds = generated.getchannel('A').point(lambda v: 255 if v > 127 else 0).getbbox()
        crop = generated.crop(bounds).resize((833, 490), Image.Resampling.LANCZOS)
        generated = Image.new('RGBA', size)
        generated.paste(crop, (96, 51))
    else:
        generated = generated.resize(size, Image.Resampling.LANCZOS)
    generated.save(SRC / f'{view}-normalized.png')
    generated = np.array(generated)
    mask = Image.new('L', size)
    ImageDraw.Draw(mask).polygon(CONTOURS[view], fill=255)
    alpha = cv2.GaussianBlur(np.array(mask).astype('float32'), (0, 0), .65)
    alpha[alpha < 1] = 0
    alpha *= generated[:, :, 3] / 255
    bow = generated.copy()
    bow[:, :, 3] = alpha.astype('uint8')
    base = Image.fromarray(original)
    base.alpha_composite(Image.fromarray(bow))
    output = np.array(base)
    # PNG composition need not preserve invisible RGB; restore it explicitly.
    outside = alpha == 0
    output[outside] = original[outside]
    save(ROOT / f'assets/{folder}/bowsling_{part}.webp', output)
    save(SRC / f'{view}-bow.webp', bow)
    assert np.array_equal(output[outside], original[outside])
    assert np.array_equal(rgba(ROOT / f'assets/{folder}/bowsling_{part}.webp')[outside], original[outside])
    source_upper = rgba(ROOT / f'assets/{folder}/slingback_upper.webp')
    blend = alpha / 255
    upper = source_upper.copy()
    upper[:, :, 3] = np.maximum(source_upper[:, :, 3], alpha).astype('uint8')
    upper[:, :, :3] = 255
    upper[:, :, 3] = np.minimum(upper[:, :, 3], output[:, :, 3])
    save(ROOT / f'assets/{folder}/bowsling_upper.webp', upper)
    luminance = cv2.GaussianBlur(generated[:, :, :3].astype('float32') @ np.array([.2126, .7152, .0722], np.float32), (0, 0), 1.1)
    for layer, rgb, strength in [('shadow', 0, np.clip((242-luminance)/155, 0, .65)), ('highlight', 255, np.clip((luminance-205)/65, 0, .6))]:
        old = rgba(ROOT / f'assets/{folder}/slingback_{layer}.webp')
        old[:, :, 3] = np.minimum(old[:, :, 3]*(1-blend) + strength*alpha, output[:, :, 3]).astype('uint8')
        old[:, :, :3] = rgb
        save(ROOT / f'assets/{folder}/bowsling_{layer}.webp', old)
    for layer in (['binding', 'insole', 'sole'] if view == 'product' else ['legs', 'occlusion']):
        target = ROOT / f'assets/{folder}/bowsling_{layer}.webp'
        origin = ROOT / f'assets/{folder}/slingback_{layer}.webp'
        if view == 'product' and layer in ['binding', 'insole']:
            old = rgba(origin)
            old[:, :, 3] = (old[:, :, 3]*(1-blend)).astype('uint8')
            save(target, old)
        else:
            shutil.copyfile(origin, target)
    metadata[view] = {'frame': list(size), 'base': 'slingback', 'bowContour': CONTOURS[view], 'outsideBowExactRGBA': True, 'groundY': 540 if view == 'product' else 964, 'toeX': 96 if view == 'product' else 171, 'skin': 'exact accepted slingback' if view == 'fitting' else None}

(SRC / 'anchors.json').write_text(json.dumps(metadata, indent=2)+'\n')
(SRC / 'export.json').write_text(json.dumps(metadata, indent=2)+'\n')
sheet = Image.new('RGB', (1440, 1100), '#edfff7')
draw = ImageDraw.Draw(sheet)
for col, (folder, part) in enumerate([('shoe2d', 'base'), ('fitting2d', 'shoe')]):
    for row, bg in enumerate(['#fff4ed', '#233c43']):
        im = Image.open(ROOT / f'assets/{folder}/bowsling_{part}.webp').convert('RGBA')
        if col:
            legs = Image.open(ROOT / 'assets/fitting2d/bowsling_legs.webp').convert('RGBA')
            legs.putalpha(ImageChops.subtract(legs.getchannel('A'), Image.open(ROOT / 'assets/fitting2d/bowsling_occlusion.webp').getchannel('A')))
            legs.alpha_composite(im)
            im = legs
        im.thumbnail((690, 510))
        tile = Image.new('RGB', (720, 550), bg)
        tile.paste(im, ((720-im.width)//2, 0), im)
        sheet.paste(tile, (col*720, row*550))
        draw.text((col*720+12, row*550+525), folder+' / source bow / unchanged shoe and calf', fill='#f680ae')
sheet.save(SRC / 'export-contact.jpg', quality=95)
print(json.dumps(metadata, indent=2))
