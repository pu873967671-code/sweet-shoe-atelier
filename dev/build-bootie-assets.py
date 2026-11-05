#!/usr/bin/env python3
"""Export the genuine ankle-boot edits into immutable product/worn layers.

Calf pixels reuse the accepted block leg exactly. Only the closed boot occludes
them. Toe ornaments reuse approved camera-specific paintings with fixed warps.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'dev/bootie-source'

def read(path, size=None):
    im = Image.open(path).convert('RGBA')
    return np.array(im.resize(size, Image.Resampling.LANCZOS) if size else im)

def blur(a, sigma=.6):
    return cv2.GaussianBlur(a.astype('float32'), (0, 0), sigma)

def save(folder, part, rgb, alpha):
    out = np.zeros((*alpha.shape, 4), np.uint8)
    out[:, :, :3] = rgb
    out[:, :, 3] = np.clip(alpha, 0, 255).astype('uint8')
    Image.fromarray(out).save(ROOT / f'assets/{folder}/bootie_{part}.webp', lossless=True, method=6)

metadata = {}
for view, folder, size, part in [('product', 'shoe2d', (1024, 640), 'base'),
                                ('fitting', 'fitting2d', (1024, 1024), 'shoe')]:
    src = read(SRC / (view + '.png'), size)
    if view == 'product':
        im = Image.open(SRC / 'product.png').convert('RGBA')
        yy, xx = np.where(np.array(im)[:, :, 3] > 127)
        bounds = (int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1))
        crop = im.crop(bounds).resize((833, 490), Image.Resampling.LANCZOS)
        im = Image.new('RGBA', size)
        im.paste(crop, (96, 51))
        src = np.array(im)
    rgb = src[:, :, :3]
    r, g, b = rgb.astype(float).transpose(2, 0, 1)
    alpha = src[:, :, 3].astype(float)
    Y, X = np.indices(alpha.shape)
    silhouette = np.minimum(alpha, blur(alpha > 100)*255)
    if view == 'product':
        shell = silhouette
        # Inner top opening and two-pixel stitched rim stay neutral. All shaft
        # panels, seams, toe and heel support receive the selected finish.
        rim = np.interp(X, [0, 570, 600, 650, 700, 750, 800, 850, 870, 1024],
                             [90, 88, 94, 95, 94, 91, 86, 79, 70, 70])
        lining = blur(Y < rim) * shell
        binding = blur((Y >= rim) & (Y < rim+2)) * shell
        bottom = np.where(shell > 100, Y, -1).max(axis=0)
        sole_band = Y >= bottom[None, :]-8
        sole = blur((r-b > 42) & (r-g > 14) & sole_band, .45) * shell
        upper = np.minimum(shell, np.maximum(0, shell-lining-binding-sole))
        save(folder, 'binding', 255, binding)
        save(folder, 'insole', 255, lining)
        save(folder, 'sole', 255, sole)
    else:
        # The neutral boot differs from warm skin; read its continuous top
        # contour once offline and keep every fabric fold below that contour.
        seed = ((r-g < 24) & (r-b < 57) & (alpha > 80) & (Y > 370)).astype('uint8')
        seed = cv2.morphologyEx(seed, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        top = np.where(seed, Y, 1024).min(axis=0)
        # Neutral highlights are not a geometric contour. The smooth authored
        # collar avoids a threshold-shaped stair edge against unchanged skin.
        valid = (top < 1024) & (np.arange(1024) >= 500) & (np.arange(1024) <= 725)
        top[valid] = np.interp(np.arange(1024)[valid],
                              [500, 520, 550, 600, 650, 680, 705, 725],
                              [397, 408, 415, 419, 418, 416, 409, 399]).astype(int)
        geometry = Y >= top[None, :]
        shell = silhouette * blur(geometry)
        # Whole boot down to its actual tan outsole; there is no open vamp.
        bottom = np.where(shell > 100, Y, -1).max(axis=0)
        sole_band = Y >= bottom[None, :]-8
        sole = blur((r-b > 45) & (r-g > 16) & sole_band, .45) * shell
        rim = blur((Y < top[None, :]+2) & geometry) * shell
        upper = np.minimum(shell, np.maximum(0, shell-sole-rim))
        legs = read(ROOT / 'assets/fitting2d/block_legs.webp')
        save(folder, 'legs', legs[:, :, :3], legs[:, :, 3])
        # Erase the old exposed foot everywhere below the new boot collar,
        # including outside the silhouette and in the real open heel arch.
        collar = np.interp(X, [0, 480, 500, 550, 600, 650, 700, 725, 1024],
                                  [390, 390, 400, 414, 418, 417, 410, 398, 390])
        occlusion = np.maximum(shell, blur(Y >= collar)*255)
        save(folder, 'occlusion', 255, occlusion)
    save(folder, part, rgb, shell)
    save(folder, 'upper', 255, upper)
    lum = blur(rgb @ np.array([.2126, .7152, .0722]), 4)
    save(folder, 'shadow', 0, np.clip((242-lum)/155, 0, .65)*upper)
    save(folder, 'highlight', 255, np.clip((lum-205)/65, 0, .6)*upper)
    Image.fromarray(np.dstack([rgb, shell]).clip(0,255).astype('uint8')).save(SRC / (view+'-normalized.png'))
    # Approved block ornaments already have the correct view direction. A
    # fixed translation places them farther down the closed boot's toe box.
    dx, dy = (0, 25) if view == 'product' else (0, -4)
    for name in ['charm_mini', 'charm_mini_tint', 'charm_pearl', 'charm_crystal']:
        path = ROOT / f'assets/{folder}/accessories/block_{name}.webp'
        ornament = read(path)
        matrix = np.array([[1, 0, dx], [0, 1, dy]], dtype='float32')
        mapped = cv2.warpAffine(ornament, matrix, size, flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_CONSTANT)
        Image.fromarray(mapped).save(path.with_name('bootie_'+name+'.webp'), lossless=True)
    metadata[view] = {'frame': list(size), 'source': view+'.png',
                      'skin': 'exact accepted block cel pixels' if view=='fitting' else None,
                      'toeOrnamentTranslation': [dx, dy],
                      'upperPixels': int((upper > 127).sum()),
                      'shellPixels': int((shell > 127).sum())}
(SRC / 'export.json').write_text(json.dumps(metadata, indent=2)+'\n')
sheet = Image.new('RGB', (1440, 800), '#edfff5')
d = ImageDraw.Draw(sheet)
for j, (folder, part) in enumerate([('shoe2d','base'), ('fitting2d','shoe')]):
    im = Image.open(ROOT / f'assets/{folder}/bootie_{part}.webp').convert('RGBA')
    if j:
        leg = Image.open(ROOT / 'assets/fitting2d/bootie_legs.webp').convert('RGBA')
        occ = Image.open(ROOT / 'assets/fitting2d/bootie_occlusion.webp').getchannel('A')
        leg.putalpha(ImageChops.subtract(leg.getchannel('A'), occ))
        leg.alpha_composite(im)
        im = leg
    im.thumbnail((700, 740))
    sheet.paste(im, (j*720, 0), im)
    d.text((j*720+12, 760), folder+' neutral ankle bootie', fill='#225e47')
sheet.save(SRC / 'export-contact.jpg', quality=95)
print(json.dumps(metadata, indent=2))
