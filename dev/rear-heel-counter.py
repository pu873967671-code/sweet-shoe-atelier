#!/usr/bin/env python3
"""Paint review-only heel-counter candidates; never write runtime assets.

The two source paintings have the same small empty lining pocket. Retain the
painted heel, lower the pocket's rim to it, and open the space behind the front
ankle. All coordinates are native sprite pixels; only masks are supersampled.
No source image is resized, transformed, or resampled.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dev/qa-out/rear_heel'
CONFIG = {
    'flat': {'dx': 0, 'dy': 0, 'box': (302, 641, 343, 698)},
    'loafer': {'dx': 35, 'dy': -1, 'box': (337, 640, 378, 697)},
}
# Pixel hashes of the reviewed v1 PNGs, independent of PNG encoder metadata.
V1_PIXELS = {
    'flat': 'efee2b10d40f86e524d58b6251e138017275fff42c9ea93b8705739b992bc6d2',
    'loafer': '80ad04741843b3cf412ceafdb0e21a759ec900107da575efcff4a157e814a293',
}


def curve(points, steps=60):
    a, b, c, d = np.array(points, dtype=float)
    return [tuple((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d)
            for t in np.linspace(0, 1, steps)]


def paint(key, config, version='v2'):
    source = Image.open(ROOT / f'assets/worn/{key}.webp').convert('RGBA')
    legs = np.array(Image.open(ROOT / f'assets/worn/{key}_legs.webp').convert('RGBA'))
    dx, dy = config['dx'], config['dy']
    shift = lambda points: [(x+dx, y+dy) for x, y in points]
    # Keep v1 reproducible for the review sheet. V2 lowers the original lip
    # less and retains a convex wall around the heel, rather than shaving
    # the return to the v1 point against the foreground ankle.
    if version == 'v1':
        rim = curve([(307, 681), (313, 678), (318, 671), (321, 673)])
        back = curve([(321, 673), (325, 673), (327, 681), (331, 693)])
    else:
        rim = curve([(307, 681), (314, 678), (321, 666), (325, 668)])
        back = curve([(325, 668), (331, 668), (334, 680), (335, 693)])
    edge = rim + back
    scale = 8
    big = Image.new('L', (source.width*scale, source.height*scale))
    draw = ImageDraw.Draw(big)
    polygon = shift([(302, 641), (343, 641), (343, 698), (334, 698)] + list(reversed(edge)))
    draw.polygon([(round(x*scale), round(y*scale)) for x, y in polygon], fill=255)
    cut = np.array(big.resize(source.size, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.22)), dtype=float)/255
    x0, y0, x1, y1 = config['box']
    bounds = np.zeros(cut.shape); bounds[y0:y1, x0:x1] = 1
    cut *= bounds
    # Leg map protects every opaque skin pixel. At the former shoe contact,
    # its partial alpha restores the foreground ankle's soft painted outline.
    skin = legs[:, :, 3].astype(float)/255
    front = (legs[:, :, 0] > 220) & (legs[:, :, 3] > 0)
    cut *= 1-skin
    pixels = np.array(source)
    pixels[:, :, 3] = np.rint(pixels[:, :, 3]*(1-cut)).astype('uint8')
    candidate = Image.fromarray(pixels)
    allowed = bounds * (1-skin)
    allowed[front] = 0
    if version == 'v2':
        # The newly retained return includes a few original lining pixels.
        # Repaint only that tiny wedge as the cream counter's inner wall;
        # otherwise retaining volume would also retain a dark empty pocket.
        wall = Image.new('L', big.size)
        wall_points = shift([(321, 672), (322, 668), (325, 667),
                             (328, 669), (330, 674), (326, 677)])
        ImageDraw.Draw(wall).polygon(
            [(round(x*scale), round(y*scale)) for x, y in wall_points], fill=255)
        wall = wall.resize(source.size, Image.Resampling.LANCZOS)
        wall_ink = np.zeros_like(pixels)
        wall_ink[:, :, :3] = (230, 218, 198)
        wall_ink[:, :, 3] = np.rint(np.array(wall)*allowed).astype('uint8')
        candidate = Image.alpha_composite(candidate, Image.fromarray(wall_ink))
    # Hand-painted narrow piping: sampled cream, warm shadow and highlight
    # match the incumbent collar. Draw just the lowered return, not the leg.
    layer = Image.new('RGBA', big.size)
    pen = ImageDraw.Draw(layer)
    lip = shift(rim[12:] + back[:(25 if version == 'v1' else 38)])
    line = [(round(x*scale), round(y*scale)) for x, y in lip]
    pen.line(line, fill=(177, 163, 137, 255), width=round(2.0*scale))
    pen.line([(x, y+round(.5*scale)) for x, y in line], fill=(235, 230, 212, 255), width=round(1.15*scale))
    layer = layer.resize(source.size, Image.Resampling.LANCZOS)
    ink = np.array(layer)
    ink[:, :, 3] = np.rint(ink[:, :, 3]*allowed).astype('uint8')
    candidate = Image.alpha_composite(candidate, Image.fromarray(ink))
    # Transparent RGB remains the source RGB; outside the small box is exact.
    final = np.array(candidate)
    final[final[:, :, 3] == 0, :3] = pixels[final[:, :, 3] == 0, :3]
    final[bounds == 0] = np.array(source)[bounds == 0]
    candidate = Image.fromarray(final)
    return source, candidate


def compare(pairs):
    sheet = Image.new('RGB', (1260, 760), '#f5efe9')
    draw = ImageDraw.Draw(sheet)
    for row, (key, versions) in enumerate(pairs.items()):
        dx, dy = CONFIG[key]['dx'], CONFIG[key]['dy']
        box = (250+dx, 600+dy, 450+dx, 760+dy)
        for col, im in enumerate(versions):
            crop = im.crop(box).resize((400, 320), Image.Resampling.NEAREST)
            sheet.paste(crop, (10+col*420, row*380+40), crop)
            draw.text((10+col*420, row*380+14), f'{key}: {("BEFORE", "v1", "v2")[col]} / 2x', fill='#382b28')
    sheet.save(OUT / 'compare.jpg', quality=95)


def audit():
    refs = json.loads(re.search(r'const SPRITES=(.*?);',
                               (ROOT / 'js/worn-sprites.js').read_text()).group(1))
    keys = [key for key in refs if '_' not in key]
    assert len(keys) == 20
    sheet = Image.new('RGB', (1200, 1600), '#f5efe9')
    draw = ImageDraw.Draw(sheet)
    for i, key in enumerate(keys):
        im = Image.open(ROOT / f'assets/worn/{key}.webp').convert('RGBA')
        im.thumbnail((280, 280), Image.Resampling.LANCZOS)
        x, y = i % 4 * 300, i // 4 * 320
        sheet.paste(im, (x+10, y+30), im)
        draw.text((x+10, y+7), key + (' / PATCH' if key in CONFIG else ' / retain'), fill='#382b28')
    sheet.save(OUT / 'inspected-bases.jpg', quality=94)
    sheet = Image.new('RGB', (780, 660), '#f5efe9')
    draw = ImageDraw.Draw(sheet)
    for row, key in enumerate(CONFIG):
        dx = CONFIG[key]['dx']
        for col, suffix in enumerate(('', '_frill', '_lace')):
            im = Image.open(ROOT / f'assets/worn/{key}{suffix}.webp').convert('RGBA')
            crop = im.crop((270+dx, 600, 390+dx, 740)).resize((240, 280), Image.Resampling.NEAREST)
            sheet.paste(crop, (col*260+10, row*330+35), crop)
            draw.text((col*260+10, row*330+10), key+suffix, fill='#382b28')
    sheet.save(OUT / 'inspected-variants.jpg', quality=95)


def verify():
    report = {}
    for key, config in CONFIG.items():
        path = ROOT / f'assets/worn/{key}.webp'
        source = Image.open(path).convert('RGBA')
        result = Image.open(OUT / f'{key}_candidate.png')
        assert result.mode == 'RGBA' and result.size == source.size
        a, b = np.array(source), np.array(result)
        changed = np.any(a != b, axis=2)
        x0, y0, x1, y1 = config['box']
        outside = changed.copy(); outside[y0:y1, x0:x1] = False
        assert not outside.any(), f'{key}: edit escaped local box'
        legs = np.array(Image.open(ROOT / f'assets/worn/{key}_legs.webp').convert('RGBA'))
        front = (legs[:, :, 0] > 220) & (legs[:, :, 3] == 255)
        assert not changed[front].any(), f'{key}: foreground skin/outline changed'
        assert not changed[legs[:, :, 3] == 255].any(), f'{key}: opaque skin changed'
        assert not np.any((a[:, :, 3] == 0) & (b[:, :, 3] != 0)), f'{key}: transparent background painted'
        # The visibly empty pocket is removed, with no background-coloured fill.
        px, py = 326+config['dx'], 655+config['dy']
        assert a[py, px, 3] > 200 and b[py, px, 3] == 0, f'{key}: lining pocket remains'
        assert changed.sum() > 100
        _, previous = paint(key, config, 'v1')
        assert hashlib.sha256(previous.tobytes()).hexdigest() == V1_PIXELS[key], f'{key}: v1 comparison drift'
        old = np.array(previous)
        retained = int(np.count_nonzero((b[:, :, 3] > 200) & (old[:, :, 3] < 100)))
        assert retained >= 100, f'{key}: counter still shaved to a sliver'
        # Solid cross-section across the rounded back wall, below the new lip.
        # V1 has no wall at these points; the original counter does.
        dx, dy = config['dx'], config['dy']
        wall = b[675+dy, 326+dx:331+dx]
        assert np.all(wall[:, 3] > 200), f'{key}: broken/thin counter return'
        # The tiny retained lining wedge must read as cream wall, not brown.
        assert np.all(b[670+dy, 324+dx, :3] > 190), f'{key}: brown lining remnant'
        removed = int(np.maximum(a[:, :, 3].astype(int)-b[:, :, 3], 0).sum())
        old_removed = int(np.maximum(a[:, :, 3].astype(int)-old[:, :, 3], 0).sum())
        assert removed < old_removed, f'{key}: v2 removes more wall than v1'
        ys, xs = np.where(changed)
        report[key] = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'size': list(result.size), 'mode': result.mode,
                       'changed_pixels': int(changed.sum()),
                       'change_bbox': [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)],
                       'opaque_front_skin_unchanged': True, 'opaque_skin_unchanged': True,
                       'outside_patch_unchanged': True, 'transparent_background_preserved': True,
                       'empty_pocket_removed': True, 'v1_pixel_exact': True,
                       'additional_solid_counter_pixels_vs_v1': retained,
                       'rounded_wall_cross_section': True,
                       'retained_lining_repainted_as_cream_wall': True,
                       'removed_alpha_vs_v1': [removed, old_removed]}
    with Image.open(OUT / 'compare.jpg') as sheet:
        assert sheet.size == (1260, 760), 'comparison must have three 400px-wide 2x crops'
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='verify existing candidates only')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.verify:
        pairs = {}
        for key, config in CONFIG.items():
            source, v1 = paint(key, config, 'v1')
            _, v2 = paint(key, config)
            v2.save(OUT / f'{key}_candidate.png')
            pairs[key] = source, v1, v2
        compare(pairs)
    verify()
