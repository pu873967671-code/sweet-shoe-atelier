#!/usr/bin/env python3
"""Restore original satin within legacy ribbon silhouettes.

The difference extractor omitted highlights and admitted warm shoe pixels that
were not in the tint mask. Re-read the retained aligned source painting, fill
only enclosed extraction holes, and give every satin pixel the same tint alpha.
External contour, authored camera frames and original source folds are retained.
Run after legacy, thin-height and platform ornament exporters. No shoe/skin base
or runtime code is changed. Immutable inputs make this finish repeatable.
"""
from pathlib import Path
import json
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).with_name('product-ribbon-source')
OUT = ROOT / 'qa/ribbon-satin'
SRC.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
records = json.loads((ROOT / 'dev/accessory-edits/extraction-report.json').read_text())['layers']
STYLES = ['flat', 'block', 'kitten', 'wedge', 'stiletto6', 'stiletto9', 'platform']


def atomic(im, path):
    temp = path.with_name('.' + path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        im.save(temp, format='WEBP', lossless=True, exact=True, method=6)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def retained(folder, heel, suffix=''):
    name = f'{heel}_strap_ribbon{suffix}.webp'
    path = ROOT / f'assets/{folder}/accessories' / name
    original = SRC / (folder + '-' + name)
    if not original.exists():
        original.write_bytes(path.read_bytes())
    return np.array(Image.open(original).convert('RGBA'))


def restored_alpha(old):
    """Fill enclosed extraction gaps without resampling the external contour."""
    alpha = old.copy()
    solid = Image.fromarray(((alpha > 100) * 255).astype('uint8')).copy()
    ImageDraw.floodfill(solid, (0, 0), 128)
    fill = Image.fromarray(((np.array(solid) != 128) * 255).astype('uint8'))
    # Only the fully enclosed interior changes coverage. Keep the original
    # antialiased external silhouette and every source-camera anchor.
    interior = np.array(fill.filter(ImageFilter.MinFilter(5))) > 0
    repaired = int(np.count_nonzero(interior & (alpha < 250)))
    alpha[interior] = 255
    assert np.array_equal(alpha[~interior], old[~interior])
    assert Image.fromarray(alpha).getbbox() == Image.fromarray(old).getbbox()
    return alpha, repaired


def source_satin(heel):
    old = retained('shoe2d', heel)
    record = next(r for r in records if r['name'] == heel + '_strap_ribbon')
    warp = tuple(v for row in record['warp'] for v in row)
    source = Image.open(ROOT / record['source']).convert('RGBA').resize((1024, 640), Image.Resampling.LANCZOS)
    source = source.transform((1024, 640), Image.Transform.AFFINE, warp, Image.Resampling.BICUBIC)
    rgb = np.array(source)[:, :, :3].astype(float)
    gray = np.clip(rgb @ np.array([.2126, .7152, .0722]) * 1.2, 0, 255).astype('uint8')
    alpha, repaired = restored_alpha(old[:, :, 3])
    out = np.zeros_like(old)
    out[:, :, :3] = gray[:, :, None]
    out[:, :, 3] = alpha
    out[alpha == 0, :3] = 0
    assert Image.fromarray(alpha).getbbox() == Image.fromarray(old[:, :, 3]).getbbox()
    return out, repaired


def remap(a, shift):
    yy, xx = np.indices(a.shape[:2])
    sy = yy - shift[None, :]
    lo = np.floor(sy).astype(int)
    hi = lo + 1
    weight = (sy - lo)[:, :, None]
    lo = np.clip(lo, 0, a.shape[0] - 1)
    hi = np.clip(hi, 0, a.shape[0] - 1)
    out = np.clip(a[lo, xx] * (1 - weight) + a[hi, xx] * weight, 0, 255).astype('uint8')
    out[(sy < 0) | (sy > a.shape[0] - 1)] = 0
    return out


paintings = {}
repairs = {}
for heel in STYLES[:4]:
    paintings[heel], repairs[heel] = source_satin(heel)
x = np.arange(1024)
for height in (6, 9):
    paintings['stiletto' + str(height)] = remap(paintings['kitten'], np.interp(x, [0, 285, 594, 855, 1024], [15, 15 if height == 6 else 20, 14, -8 if height == 6 else -2, 0]))
paintings['platform'] = remap(paintings['block'], -52 * (1 - np.clip((x - 300) / 550, 0, 1)))
report = {'status': 'PASS', 'originalSourceReextraction': True, 'baseSkinAndCameraUntouched': True, 'styles': []}
sheet = Image.new('RGB', (1600, len(STYLES) * 300), '#233b34')

for row, heel in enumerate(STYLES):
    before = Image.fromarray(retained('shoe2d', heel))
    a = paintings[heel]
    # Height/platform exporters use different interpolation kernels. Preserve
    # each camera's own retained edge alpha, rather than resampling that edge
    # with the satin RGB: even subpixel fringes and mount extrema stay fixed.
    a[:, :, 3], repairs[heel] = restored_alpha(np.array(before)[:, :, 3])
    a[a[:, :, 3] == 0, :3] = 0
    after = Image.fromarray(a)
    tint = np.full_like(a, 255)
    tint[:, :, 3] = a[:, :, 3]
    path = ROOT / f'assets/shoe2d/accessories/{heel}_strap_ribbon.webp'
    atomic(after, path)
    atomic(Image.fromarray(tint), path.with_name(path.stem + '_tint.webp'))
    assert np.array_equal(a[:, :, 0], a[:, :, 1]) and np.array_equal(a[:, :, 1], a[:, :, 2]), heel
    assert not after.getchannel('A').crop((0, 530, 1024, 640)).getbbox(), heel + ': ground clearance'
    # Worn artwork is already neutral continuous satin; match the tiny omitted
    # mask edge pixels without modifying a single original painting pixel.
    worn = retained('fitting2d', heel)
    worn_tint = np.full_like(worn, 255)
    worn_tint[:, :, 3] = worn[:, :, 3]
    worn_path = ROOT / f'assets/fitting2d/accessories/{heel}_strap_ribbon_tint.webp'
    retained('fitting2d', heel, '_tint')
    atomic(Image.fromarray(worn_tint), worn_path)
    assert Image.open(worn_path).getchannel('A').tobytes() == Image.fromarray(worn[:, :, 3]).tobytes()
    report['styles'].append({'style': heel, 'sourceInteriorPixelsRepaired': repairs[heel], 'externalContourAlphaExact': True, 'productPaintingAndTintAlphaExact': True, 'neutralSatinEveryVisiblePixel': True, 'wornPaintingExact': True, 'wornTintAlphaExact': True, 'groundClearance': True})
    # Source-size before/after, with the actual ribbon mounted over its shoe.
    base = Image.open(ROOT / f'assets/shoe2d/{heel}_base.webp').convert('RGBA')
    for col, (bg, im) in enumerate([('#fff1e7', before), ('#fff1e7', after), ('#233b34', before), ('#233b34', after)]):
        canvas = Image.new('RGBA', base.size, bg)
        canvas.alpha_composite(base)
        canvas.alpha_composite(im)
        tile = canvas.crop((400, 190, 900, 515)).resize((400, 260), Image.Resampling.LANCZOS)
        sheet.paste(tile, (col * 400, row * 300))
        ImageDraw.Draw(sheet).text((col * 400 + 8, row * 300 + 270), heel + (' before' if col % 2 == 0 else ' after'), fill='#f67eaf')
    native = Image.new('RGBA', after.size, '#233b34')
    native.alpha_composite(base)
    native.alpha_composite(after)
    native.crop((400, 190, 900, 515)).resize((1500, 975)).convert('RGB').save(OUT / f'{heel}-native-after.jpg', quality=96)

sheet.save(OUT / 'before-after.jpg', quality=96)
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS: seven original product ribbon paintings, shared satin alpha; seven exact worn paintings with complete tint masks')
