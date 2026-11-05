#!/usr/bin/env python3
"""White-key the approved stiletto6 rear source, without editing its painting.

The connected warm skin component supplies the actual contour. Neutral ground
shadow is excluded. Only the two-pixel contour fringe takes its RGB from the
nearest opaque skin sample, removing the source white premultiplication.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/src-user-legs-20261029/candidates/leg-rear-heel-candidate-v2.png'
OUT = ROOT / 'dev/stiletto6-fit'


def key_rear(source):
    image = source.convert('RGB') if isinstance(source, Image.Image) else Image.open(source).convert('RGB')
    rgb = np.asarray(image).astype(float)
    # Skin is warm even in highlight; the white backdrop and grey painted
    # floor shadow are neutral. Mid-edge chroma tracks the painted contour.
    threshold = np.full(rgb.shape[:2], 12.)
    threshold[1245:] = 28.  # Ground shadow has weak warm colour only beside toes.
    warm = (rgb[:, :, 0] - rgb[:, :, 2] > threshold) & (rgb[:, :, 0] - rgb[:, :, 1] > 3)
    labels, count = ndimage.label(warm)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    skin = ndimage.binary_fill_holes(labels == sizes.argmax())
    matte = ndimage.gaussian_filter(skin.astype(float), .55)
    matte = np.clip((matte - .08) / .84, 0, 1)
    # Preserve source RGB in the opaque body. Edge RGB uses the adjacent
    # uncontaminated skin, so alpha never brings a white rim onto dark rooms.
    core = ndimage.binary_erosion(skin, iterations=2, border_value=1)
    indices = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
    nearest = rgb[tuple(indices)]
    fringe = (matte > 0) & ~core
    rgb[fringe] = nearest[fringe]
    rgb[matte == 0] = 0
    rgba = np.dstack((np.rint(rgb).astype('uint8'), np.rint(matte * 255).astype('uint8')))
    return Image.fromarray(rgba)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    image = key_rear(SOURCE)
    image.save(OUT / 'rear-keyed.png')
    preview = Image.new('RGB', (1152, 1080), '#f6f0eb')
    draw = ImageDraw.Draw(preview)
    for col, color in enumerate(['#f6f0eb', '#24202c']):
        p = image.copy(); p.thumbnail((560, 1010), Image.Resampling.LANCZOS)
        bg = Image.new('RGBA', (576, 1040), color)
        bg.alpha_composite(p, ((576-p.width)//2, 0))
        preview.paste(bg.convert('RGB'), (col*576, 40))
        draw.text((col*576+12, 12), 'Approved rear heel / '+('light' if col==0 else 'dark'), fill='#473c43')
    preview.save(OUT / 'rear-key-preview.jpg', quality=94)
    assert before == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    (OUT / 'rear-key-provenance.json').write_text(json.dumps(dict(source=str(SOURCE.relative_to(ROOT)), sha256=before,
        bounds=image.getbbox(), edge_softness_source_px=1.5, source_unchanged=True,
        landmarks=dict(heel=[522,1115], arch=[453,1154], ball=[376,1275], toe=[290,1314])), indent=2)+'\n')
    print(OUT / 'rear-keyed.png')

if __name__ == '__main__':
    main()
