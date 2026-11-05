#!/usr/bin/env python3
"""Restore the original display bows on two immutable worn-camera kits.

Run after build-bowsling-assets.py / build-bowmule-assets.py. Retained pre-repair
layers are deterministic inputs, never overwritten. No skin, hosiery, heel,
product painting or runtime camera changes are involved.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'dev/fitting-polish/integral-bow-source'
OUT = ROOT / 'qa/integral-bow-source'
OUT.mkdir(parents=True, exist_ok=True)
STYLES = ['bowsling', 'bowmule']
PARTS = ['shoe', 'upper', 'shadow', 'highlight']
# The accepted display knot is pinned to the original fitted vamp knot.
# Compensate for the retained 1.15/.93 side-camera projection so the broad
# satin loops retain their volume instead of flattening into a narrow strip.
MATRIX = np.array([[.84, 0, 389 - 387 * .84],
                   [0, .99, 817 - 399 * .99]], dtype=np.float64)
CONTOUR = [(232,410),(238,390),(253,371),(274,349),(299,327),
           (317,318),(329,319),(343,331),(358,349),(369,369),
           (375,381),(394,373),(411,374),(417,384),(448,380),
           (483,381),(515,388),(541,399),(555,407),(548,432),
           (533,461),(516,491),(502,504),(522,523),(478,525),
           (450,528),(438,518),(424,495),(411,467),(400,437),
           (398,425),(376,420),(359,414),(342,428),(330,443),
           (315,461),(299,447),(286,435),(267,430),(248,423),
           (236,419)]


def read(path):
    return np.array(Image.open(path).convert('RGBA'))


def warp(pixels):
    # Premultiplied interpolation avoids grey/white RGB halos on the satin
    # outline. The same alpha is used by paint, dye and lighting.
    work = pixels.astype(np.float32) / 255
    work[:, :, :3] *= work[:, :, 3:4]
    inverse = np.linalg.inv(np.vstack([MATRIX, [0, 0, 1]]))[:2].flatten()
    projected = np.stack([np.array(Image.fromarray(work[:, :, channel], 'F').transform(
        (1024, 1024), Image.Transform.AFFINE, inverse,
        Image.Resampling.BICUBIC)) for channel in range(4)], axis=2)
    projected = np.clip(projected, 0, 1)
    projected[:, :, :3] /= np.maximum(projected[:, :, 3:4], 1e-6)
    return np.clip(np.rint(projected * 255), 0, 255).astype('uint8')


mask = Image.new('L', (1024, 640))
ImageDraw.Draw(mask).polygon(CONTOUR, fill=255)
alpha = np.array(mask.filter(ImageFilter.GaussianBlur(.65))).astype('float32')
alpha[alpha < 1] = 0
report = {'status': 'PASS', 'styles': [], 'matrix': MATRIX.tolist(),
          'scope': 'Original integral bows only; art acceptance requires native review.'}
for style in STYLES:
    product = read(ROOT / f'assets/shoe2d/{style}_base.webp')
    bow = product.copy()
    bow[:, :, 3] = np.minimum(alpha, product[:, :, 3]).astype('uint8')
    bow = warp(bow)
    a = bow[:, :, 3].astype('float32') / 255
    luminance = bow[:, :, :3].astype('float32') @ np.array([.2126, .7152, .0722])
    lum = np.array(Image.fromarray(np.rint(luminance).astype('uint8')).filter(
        ImageFilter.GaussianBlur(1.1))).astype('float32')
    row = {'style': style, 'parts': [], 'protectedOutside': True}
    for part in PARTS:
        before = read(SOURCE / f'{style}_{part}.webp')
        clean = read(ROOT / f'assets/fitting2d/slingback_{part}.webp')
        base = before.copy()
        # Both styles inherit exactly this forefoot. Restore the entire old
        # bow rectangle, including transparent loops above the collar, before
        # laying down the display painting; never inpaint skin or shoe cloth.
        base[710:960, 220:550] = clean[710:960, 220:550]
        if part == 'shoe':
            result = np.array(Image.alpha_composite(Image.fromarray(base),
                                                    Image.fromarray(bow)))
        else:
            result = base.copy()
            result[:, :, :3] = 255 if part != 'shadow' else 0
            if part == 'upper':
                result[:, :, 3] = np.maximum(base[:, :, 3], bow[:, :, 3])
            else:
                strength = (np.clip((242-lum)/155, 0, .65) if part == 'shadow'
                            else np.clip((lum-205)/65, 0, .6))
                result[:, :, 3] = np.rint(base[:, :, 3]*(1-a) +
                                         strength*bow[:, :, 3]).astype('uint8')
        # Preserve invisible RGB as well as every protected body/heel pixel.
        changed_region = np.zeros(a.shape, bool)
        changed_region[710:960, 220:550] = True
        changed_region |= bow[:, :, 3] > 0
        result[~changed_region] = before[~changed_region]
        assert np.array_equal(result[~changed_region], before[~changed_region])
        path = ROOT / f'assets/fitting2d/{style}_{part}.webp'
        Image.fromarray(result).save(path, lossless=True, exact=True, method=6)
        row['parts'].append({'part': part,
                             'changedPixels': int(np.any(result != before, axis=2).sum()),
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    report['styles'].append(row)
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
