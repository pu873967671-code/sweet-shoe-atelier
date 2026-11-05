#!/usr/bin/env python3
"""Export the REVIEW00:55 low-camera room edits; no runtime image service."""
from pathlib import Path
from PIL import Image, ImageOps
import hashlib
import json
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'dev/fitting-perspective-source'
report = {}
for scene in ['salon', 'mirror_lounge', 'car', 'vanity', 'balcony']:
    source = SOURCE / 'output' / (scene + '.png')
    image = Image.open(source).convert('RGB')
    assert image.size == (1536, 1024), (scene, image.size)
    destinations = [ROOT / ('assets/bg_fitting.webp' if scene == 'salon' else 'assets/scenes/close_' + scene + '.webp')]
    if scene == 'salon':
        destinations.append(ROOT / 'assets/scenes/close_salon.webp')
    for destination in destinations:
        image.save(destination, 'WEBP', quality=88, method=6)
    if scene != 'salon':
        thumb = ROOT / ('assets/scenes/scene_' + scene + '_thumb.webp')
        ImageOps.fit(image, (240, 160), method=Image.Resampling.LANCZOS).save(thumb, 'WEBP', quality=85, method=6)
        destinations.append(thumb)
    report[scene] = {'size': list(image.size), 'horizon': 0.40, 'platform': 'none in background; one shared runtime platform', 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'assets': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in destinations}}
(SOURCE / 'export.json').write_text(json.dumps(report, indent=2) + '\n')
print('Exported five low-camera room backgrounds and matching thumbnails')
