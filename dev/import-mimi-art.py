#!/usr/bin/env python3
"""Import the reviewed generated Mimi sheets; offline Pillow/NumPy only.

Source PNGs and prompts stay under dev/, outside the runtime upload. Existing
alpha is preserved; RGB green-screen sources are keyed before pose extraction.
Head-centred canvases keep the portrait bust stable across wide hand gestures.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'dev/character-sources'
SOURCE.mkdir(exist_ok=True)


def clean(im):
    a = np.array(im.convert('RGBA')).astype(float)
    if im.mode != 'RGBA' or a[:, :, 3].min() == 255:
        rgb = a[:, :, :3]
        border = np.concatenate([rgb[:8].reshape(-1, 3), rgb[-8:].reshape(-1, 3)])
        bg = np.median(border, axis=0)
        distance = np.linalg.norm(rgb - bg, axis=2)
        alpha = np.clip((distance - 48) / 76, 0, 1)
        # Remove the green contribution from mixed edge pixels, retaining mint.
        mixed = (alpha > 0) & (alpha < 1)
        rgb[mixed] = (rgb[mixed] - (1-alpha[mixed, None])*bg) / alpha[mixed, None]
        a[:, :, :3] = rgb.clip(0, 255)
        a[:, :, 3] = alpha * 255
    # Drop isolated matte speckles without changing the solid character pixels.
    alpha_image = Image.fromarray(a[:, :, 3].astype('uint8'), 'L')
    neighbourhood = np.array(alpha_image.filter(ImageFilter.MedianFilter(3)))
    a[:, :, 3][neighbourhood < 8] = 0
    return Image.fromarray(a.clip(0, 255).astype('uint8'), 'RGBA')


# These reviewed source-column intervals follow the actual empty gaps, not
# equal thirds. In particular, surprise must never include present's ponytail.
SHEETS = [
    ('a', [('wave', 145, 540, 335), ('point', 670, 1160, 855),
           ('cheer', 1245, 1695, 1470)]),
    ('b', [('think', 125, 455, 270), ('surprise', 545, 885, 697),
           ('present', 965, 1530, 1135)]),
]
CANVAS = (800, 1000)
BODY_HEIGHT = 960
HEAD_HEIGHT = 240
# Reviewed crown-to-chin landmarks; normalize head and lower body separately.
# The two source sheets have slightly different head/body proportions.
CHIN = dict(wave=233, point=246, cheer=250, think=255, surprise=253, present=252)
HEAD_X = 400
TOP = 20
report = {'canvas': CANVAS, 'body_height': BODY_HEIGHT, 'head_height': HEAD_HEIGHT, 'head_x': HEAD_X, 'poses': {}}

for suffix, poses in SHEETS:
    path = SOURCE / ('mimi-refresh-' + suffix + '.png')
    source = clean(Image.open(path))
    for pose, x0, x1, head in poses:
        crop = source.crop((x0, 0, x1, source.height))
        # Remove weak keyed edge specks before deriving the real character box.
        # All bounds are source-owned, keeping the whole finger/ponytail intact.
        box = crop.getchannel('A').point(lambda a: 255 if a > 40 else 0).getbbox()
        assert box, pose
        left, top, right, bottom = box
        art = crop.crop(box)
        head_height = CHIN[pose] - top
        scale = HEAD_HEIGHT / head_height
        width = round(art.width * scale)
        normalized = Image.new('RGBA', (width, BODY_HEIGHT))
        normalized.alpha_composite(art.crop((0, 0, art.width, head_height)).resize(
            (width, HEAD_HEIGHT), Image.Resampling.LANCZOS), (0, 0))
        normalized.alpha_composite(art.crop((0, head_height, art.width, art.height)).resize(
            (width, BODY_HEIGHT - HEAD_HEIGHT), Image.Resampling.LANCZOS), (0, HEAD_HEIGHT))
        art = normalized
        x = round(HEAD_X - (head - x0 - left) * scale)
        assert x >= 8 and x + art.width <= CANVAS[0] - 8, (pose, x, art.size)
        canvas = Image.new('RGBA', CANVAS)
        canvas.alpha_composite(art, (x, TOP))
        out = ROOT / 'assets/mentor' / ('mentor_' + pose + '.webp')
        canvas.save(out, 'WEBP', quality=90, method=6, exact=True)
        # The neutral source is the same anchored full body, so every consumer
        # (chapter portraits, mobile bust, story and dialogue) shares framing.
        if pose == 'think':
            canvas.save(ROOT / 'assets/mentor_neutral.webp', 'WEBP', quality=90, method=6, exact=True)
        report['poses'][pose] = {'source': path.name, 'source_columns': [x0, x1],
                                 'source_bbox': box, 'source_chin_y': CHIN[pose], 'head_scale': round(scale, 5),
                                 'alpha_bbox': canvas.getchannel('A').getbbox()}
(ROOT / 'dev/mimi-framing.json').write_text(json.dumps(report, indent=2) + '\n')
print('Imported six Mimi poses: shared 800x1000 canvas, 960px body height, 240px head, centred head')
