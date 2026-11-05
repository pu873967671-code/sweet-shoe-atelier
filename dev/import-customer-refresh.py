#!/usr/bin/env python3
"""Key the user-authorized /workspace/work/gen cast24_ sheets offline.

Default writes candidates only. Use --apply after personally inspecting the
contact sheet. Runtime stays local, with the existing filenames and canvases.
Prompts are recorded in customer-refresh-prompts.json alongside this script.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['bride', 'buns', 'casual', 'pink', 'school', 'tea']
EXPRESSIONS = ['neutral', 'happy', 'sad']
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=ROOT / 'dev' / 'character-sources')
parser.add_argument('--apply', action='store_true')
parser.add_argument('--names', default=','.join(NAMES))
args = parser.parse_args()
OUT = ROOT / 'qa' / 'character-refresh-candidates'
OUT.mkdir(exist_ok=True)
names = args.names.split(',')
sheet = Image.new('RGB', (len(names) * 172, 3 * 218), '#eafaf3')
report = {'mode': 'applied' if args.apply else 'candidates', 'sources': [], 'artistic_acceptance': False}


def key(im):
    original = np.asarray(im.convert('RGBA'), dtype=np.float32)
    rgb = original[..., :3].copy()
    distance = np.sqrt(rgb[..., 0] ** 2 + (255 - rgb[..., 1]) ** 2 + rgb[..., 2] ** 2)
    alpha = np.clip((distance - 20) / 75, 0, 1)
    # A strong green primary cannot belong to the cream/mint/candy wardrobe.
    excess = rgb[..., 1] - np.maximum(rgb[..., 0], rgb[..., 2])
    alpha = np.minimum(alpha, np.clip((120 - excess) / 65, 0, 1))
    # Some image providers already extract the requested solid key background.
    # Preserve their alpha; never turn transparent black back into an opaque box.
    alpha = np.minimum(alpha, original[..., 3] / 255)
    # The provider's extractor can leave tiny saturated red/yellow key specks.
    # These colours are outside this softly lit pastel wardrobe; remove only
    # that extreme chroma rather than grading any face/hair/clothing pixels.
    red_speck = (rgb[..., 0] > 180) & (rgb[..., 1] < 72) & (rgb[..., 2] < 72)
    yellow_speck = (rgb[..., 0] > 180) & (rgb[..., 1] > 180) & (rgb[..., 2] < 85)
    alpha[red_speck | yellow_speck] = 0
    # Suppress chroma contamination only on extracted antialiasing pixels.
    edge = alpha < .999
    rgb[..., 1][edge] = np.minimum(rgb[..., 1][edge], np.maximum(rgb[..., 0], rgb[..., 2])[edge] + 8)
    alpha[alpha < .025] = 0
    result = Image.fromarray(np.uint8(np.dstack([rgb, alpha * 255])))
    # A one-source-pixel cleanup removes extractor dust without changing the
    # large painted silhouette; final art is downsampled roughly 2:1 afterwards.
    result.putalpha(result.getchannel('A').filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.MinFilter(3)))
    return result


for col, name in enumerate(names):
    assert name in NAMES, name
    source = args.source / f'cast24_{name}.png'
    art = key(Image.open(source))
    pieces = []
    for i in range(3):
        cell = art.crop((round(art.width * i / 3), 0, round(art.width * (i + 1) / 3), art.height))
        box = cell.getchannel('A').point(lambda a: 255 if a > 160 else 0).getbbox()
        assert box, (source, i, 'empty character')
        box = (max(0, box[0] - 3), max(0, box[1] - 3), min(cell.width, box[2] + 3), min(cell.height, box[3] + 3))
        pieces.append(cell.crop(box))
    scale = min(296 / max(p.width for p in pieces), 358 / max(p.height for p in pieces))
    paths = []
    for row, (expression, piece) in enumerate(zip(EXPRESSIONS, pieces)):
        piece = piece.resize((round(piece.width * scale), round(piece.height * scale)), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (302, 360))
        canvas.alpha_composite(piece, ((302 - piece.width) // 2, 1))
        filename = f'c_{name}_{expression}.webp'
        dest = OUT / filename
        canvas.save(dest, 'WEBP', quality=90, method=4, exact=True)
        if args.apply:
            (ROOT / 'assets' / filename).write_bytes(dest.read_bytes())
        preview = canvas.copy()
        preview.thumbnail((156, 184), Image.Resampling.LANCZOS)
        sheet.paste(preview, (col * 172 + (172 - preview.width) // 2, row * 218 + 8), preview)
        ImageDraw.Draw(sheet).text((col * 172 + 8, row * 218 + 196), f'{name}/{expression}', fill='#284d46')
        paths.append(str(dest.relative_to(ROOT)))
    report['sources'].append({'name': name, 'source': str(source), 'outputs': paths})
sheet.save(OUT / 'customer-expressions.jpg', quality=95)
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(f'{report["mode"]}: {len(names) * 3} character cutouts; {OUT / "customer-expressions.jpg"}')
