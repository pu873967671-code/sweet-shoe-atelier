#!/usr/bin/env python3
"""Prepare the independently painted pair for SOURCE REVIEW, never runtime.

The original painting and its generation prompt are immutable provenance.
Outputs stay under dev/: current fitted shoes, socks and ornaments use a
separate camera. Per-foot masks/anchors here are an explicit handoff, not an
assertion that all eighteen runtime heel cameras have been repainted.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'dev/paired-source-20261025'
KIT = SRC / 'candidate-kit'
KIT.mkdir(exist_ok=True)
source = SRC / 'pair-neutral-original.png'
im = Image.open(source).convert('RGBA')
original = np.asarray(im)
a = original.astype(float)
r, g, b = a[:, :, :3].transpose(2, 0, 1)
dominance = g - np.maximum(r, b)
matte = dominance > 15
# Estimate the neighbouring opaque paint before unmixing the pure green
# background. This preserves translucent contour coverage without leaving a
# green fringe or eroding it into detached pale flecks.
known = ((dominance < 8) & (original[:, :, 3] > 0)).astype(float)
def blur(values, radius):
    return np.asarray(Image.fromarray(np.rint(values).clip(0, 255).astype('uint8')).filter(ImageFilter.GaussianBlur(radius))).astype(float)
weights = blur(known * 255, 4) / 255
estimate = np.stack([blur(a[:, :, c] * known, 4) / np.maximum(weights, .001) for c in range(3)], axis=2)
fr, fg, fb = estimate.transpose(2, 0, 1)
coverage = np.ones_like(r)
coverage[matte] = np.clip(((r * fr + b * fb) / np.maximum(fr * fr + fb * fb, 1))[matte], 0, 1)
coverage[matte & (weights < .001)] = 0
coverage[coverage < .025] = 0
edge = matte & (coverage > 0)
for c in range(3):
    unmix = (a[:, :, c] - (1 - coverage) * (255 if c == 1 else 0)) / np.maximum(coverage, .001)
    a[:, :, c][edge] = unmix[edge]
a[edge, 1] = np.minimum(a[edge, 1], np.maximum(a[edge, 0], a[edge, 2]))
a[:, :, 3] *= coverage
a[a[:, :, 3] < 8] = 0
out = Image.fromarray(np.rint(a).clip(0, 255).astype('uint8'))
out.save(SRC / 'pair-neutral-alpha.webp', lossless=True, method=6, exact=True)
paint = np.asarray(out)
alpha = paint[:, :, 3]
opaque = (~matte) & (original[:, :, 3] >= 8)
assert np.array_equal(paint[opaque, :3], original[opaque, :3])
assert np.count_nonzero(alpha) > im.width * im.height * .12
assert np.count_nonzero(alpha == 0) > im.width * im.height * .25
assert np.any(alpha[0] > 127), 'calves must bleed above frame'
assert not np.any(alpha[-1] > 0), 'shoes must have bottom clearance'

# All curves are authored in immutable ORIGINAL 1254px camera coordinates.
# Raster partitions are binary at internal collar seams; visible outside alpha
# remains the antialiased painting. This allows exact RGBA reconstruction.
def curve_mask(start, segments):
    points = [start]
    for segment in segments:
        if len(segment) == 2:
            points.append(segment)
            continue
        p0 = np.array(points[-1]); p1, p2, p3 = [np.array(segment[i:i+2]) for i in (0, 2, 4)]
        for t in np.linspace(0, 1, 45)[1:]:
            p = (1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3
            points.append(tuple(p))
    mask = Image.new('L', im.size)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return np.asarray(mask) > 127

# The front leg hides part of the rear collar/ankle in the original painting.
# These are VISIBLE partitions, not invented hidden anatomy.
front_skin = curve_mask((788, -10), [
    (1095, -10), (1019, 243, 886, 490, 914, 609),
    (915, 626, 924, 641, 929, 652),
    (954, 679, 914, 760, 857, 856),
    (817, 918, 779, 993, 744, 1031),
    (703, 1073, 637, 1068, 571, 1056),
    (513, 1044, 478, 1029, 464, 1015),
    (455, 1006, 478, 996, 499, 981),
    (558, 907, 626, 737, 679, 603),
    (739, 459, 761, 218, 788, -10),
])
rear_skin = curve_mask((616, -10), [
    (791, -10), (784, 170, 749, 439, 681, 594),
    (642, 672, 594, 763, 553, 813),
    (517, 854, 439, 840, 397, 822),
    (388, 818, 390, 814, 402, 805),
    (459, 745, 516, 586, 546, 486),
    (583, 367, 591, 172, 616, -10),
]) & ~front_skin
# Front shoe region follows the occluding shoe/skin outline. Every non-skin
# pixel on its right/lower side belongs to that independently drawn shoe.
front_region = curve_mask((679, 603), [
    (1110, 603), (1100, 1235), (190, 1235), (211, 1080),
    (452, 1000), (499, 981), (558, 907, 626, 737, 679, 603),
])
# Reserve the bright painted collar lip at the hand-authored boundary.
# Interior skin highlights remain untouched.
yy = np.indices(alpha.shape)[0]
for skin in [front_skin, rear_skin]:
    core = np.asarray(Image.fromarray((skin * 255).astype('uint8')).filter(ImageFilter.MinFilter(19))) > 127
    lip = skin & ~core & (yy > 580) & ((r - g) < 24)
    skin[lip] = False
skin_union = front_skin | rear_skin
visible = alpha > 0
front_shoe = front_region & ~skin_union & visible
rear_shoe = ~front_region & ~skin_union & visible
# Protect blank canvas regions: every visible pixel belongs to exactly one
# region. Overlap and independent left/right shapes retain original pixels.
regions = {'front_legs': front_skin & visible, 'rear_legs': rear_skin & visible,
           'front_shoe': front_shoe, 'rear_shoe': rear_shoe}
assert np.all(sum(v.astype(int) for v in regions.values())[visible] == 1)

# Conservative dye interiors: original piping, natural outsole and heel cap
# remain painted. Final runtime integration must compare these with newly
# authored per-foot ornaments and complete sock occlusion at native scale.
front_upper = curve_mask((466, 1025), [
    (516, 1055, 649, 1098, 724, 1059),
    (774, 1027, 865, 871, 933, 707),
    (951, 675), (975, 726, 1005, 791, 979, 843),
    (921, 889, 879, 919, 843, 968),
    (786, 1037, 759, 1130, 714, 1153),
    (591, 1195, 377, 1186, 284, 1173),
    (249, 1146, 344, 1087, 466, 1025),
]) & front_shoe
rear_upper = curve_mask((389, 826), [
    (441, 852, 513, 866, 554, 832),
    (590, 794, 623, 715, 651, 660),
    (628, 751, 589, 841, 546, 900),
    (485, 937, 347, 942, 270, 924),
    (248, 909, 323, 863, 389, 826),
]) & rear_shoe

for name, mask in regions.items():
    pixels = paint.copy(); pixels[:, :, 3] *= mask; pixels[pixels[:, :, 3] == 0] = 0
    Image.fromarray(pixels).save(KIT / f'{name}.webp', lossless=True, method=6, exact=True)
for foot, mask in [('front', front_upper), ('rear', rear_upper)]:
    pixels = np.zeros_like(paint); pixels[:, :, :3] = 255; pixels[:, :, 3] = alpha * mask
    pixels[pixels[:, :, 3] == 0] = 0
    Image.fromarray(pixels).save(KIT / f'{foot}_upper.webp', lossless=True, method=6, exact=True)
    # Matched grayscale finish weights are derived offline in the same camera.
    luminance = (paint[:, :, 0] * .2126 + paint[:, :, 1] * .7152 + paint[:, :, 2] * .0722) / 255
    for part, rgb, weight in [
        ('shadow', 0, np.clip((.96 - luminance) * 1.6, 0, .62)),
        ('highlight', 255, np.clip((luminance - .83) / .17, 0, 1) * .45),
    ]:
        shading = np.zeros_like(paint); shading[:, :, :3] = rgb
        shading[:, :, 3] = np.rint(alpha * mask * weight).astype('uint8')
        shading[shading[:, :, 3] == 0] = 0
        Image.fromarray(shading).save(KIT / f'{foot}_{part}.webp', lossless=True, method=6, exact=True)
    # Occlusion explicitly names the painted collar/sole layer. It is not a
    # substitute for the separate upper and must be drawn over future socks.
    pixels = paint.copy(); pixels[:, :, 3] *= regions[f'{foot}_shoe'] & ~mask
    pixels[pixels[:, :, 3] == 0] = 0
    Image.fromarray(pixels).save(KIT / f'{foot}_occlusion.webp', lossless=True, method=6, exact=True)

reconstructed = Image.new('RGBA', im.size)
for name in ['rear_legs', 'rear_shoe', 'front_legs', 'front_shoe']:
    reconstructed = Image.alpha_composite(reconstructed, Image.open(KIT / f'{name}.webp'))
assert np.array_equal(np.asarray(reconstructed), paint), 'source partition must reconstruct exact RGBA'
reconstructed.save(KIT / 'reconstructed.webp', lossless=True, method=6, exact=True)

anchors = {
    'scope': 'SOURCE CANDIDATE ONLY; no runtime camera registration',
    'canvas': list(im.size), 'toeGroundImmutable': True,
    'front': {'toe': [275, 1175], 'ground': [906, 1085], 'vamp': [465, 1110],
              'collarFar': [467, 1010], 'collarNear': [929, 665],
              'cuff': {'center': [822, 542], 'radius': [102, 19], 'rotation': -.12},
              'occlusionOrder': 'above rear leg and shoe'},
    'rear': {'toe': [261, 923], 'ground': [373, 942], 'vamp': [385, 883],
             'collarFar': [395, 814], 'collarNear': [675, 602],
             'cuff': {'center': [614, 520], 'radius': [70, 14], 'rotation': .12},
             'occlusionOrder': 'behind front leg and shoe'},
    'integrationRemaining': [
        'Native manual collar/piping refinement and dye-edge acceptance',
        'Native material/shadow/highlight acceptance for these candidate source weights',
        'All raster and procedural ornaments re-authored in these two cameras',
        'All five sock styles with perspective cuffs and original collar occlusion',
        'Complete pair cache/render/fallback path, save compatibility and no-jitter QA',
        'Heel-specific paired sources for the remaining runtime silhouettes',
    ],
}
(KIT / 'anchors.json').write_text(json.dumps(anchors, indent=2) + '\n')
for name, bg in [('light', '#fff5ee'), ('dark', '#243b40')]:
    sheet = Image.new('RGB', im.size, bg); sheet.paste(out, (0, 0), out)
    sheet.save(SRC / f'pair-{name}-native.jpg', quality=96)
    diagnostic = Image.new('RGBA', im.size, bg)
    for foot, colour in [('rear', (154, 203, 245)), ('front', (244, 161, 190))]:
        diagnostic.alpha_composite(Image.open(KIT / f'{foot}_legs.webp'))
        shoe = Image.open(KIT / f'{foot}_shoe.webp'); tint = Image.new('RGBA', im.size, colour + (255,))
        tint.putalpha(shoe.getchannel('A')); diagnostic.alpha_composite(tint)
    diagnostic.convert('RGB').save(KIT / f'partition-{name}.jpg', quality=95)
contact = Image.new('RGB', (im.width * 2, im.height + 38), '#fff5ee')
for x, name in [(0, 'light'), (im.width, 'dark')]:
    contact.paste(Image.open(SRC / f'pair-{name}-native.jpg'), (x, 0))
draw = ImageDraw.Draw(contact)
draw.text((12, im.height + 12), 'INDEPENDENT PAIR / SOURCE CANDIDATE ONLY / NOT RUNTIME INTEGRATED', fill='#6c4c69')
contact.save(SRC / 'contact-review.jpg', quality=94)
# A deliberately conspicuous dye preview exposes skin spill and missed edges.
for bg_name, bg in [('dark', '#243b40'), ('light', '#fff5ee')]:
    dyed = out.copy()
    for foot in ['rear', 'front']:
        tint = Image.new('RGBA', im.size, '#c8bbff')
        tint.putalpha(Image.open(KIT / f'{foot}_upper.webp').getchannel('A'))
        dyed.alpha_composite(tint)
    sheet = Image.new('RGBA', im.size, bg); sheet.alpha_composite(dyed)
    sheet.convert('RGB').save(KIT / f'dye-review-{bg_name}.jpg', quality=95)

report = {
    'status': 'PASS', 'scope': 'source extraction + candidate visible per-foot kit; not runtime integration',
    'originalDimensions': list(im.size), 'alphaBounds': out.getchannel('A').getbbox(),
    'retainedSourceRgbUnchanged': int(np.count_nonzero(opaque)),
    'lowAlphaSourceSpecksRemoved': int(np.count_nonzero((original[:, :, 3] > 0) & (original[:, :, 3] < 8))),
    'transparentPixels': int(np.count_nonzero(alpha == 0)),
    'calvesBleedTop': True, 'shoesClearBottom': True,
    'originalSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'alphaSha256': hashlib.sha256((SRC / 'pair-neutral-alpha.webp').read_bytes()).hexdigest(),
    'runtimeIntegrated': False, 'exactSourceReconstruction': True,
    'disjointVisiblePartitions': True,
    'upperMasksContainedInShoe': bool(np.all(~front_upper | front_shoe) and np.all(~rear_upper | rear_shoe)),
    'regionPixels': {k: int(np.count_nonzero(v)) for k, v in regions.items()},
    'candidateLayers': sorted(p.name for p in KIT.glob('*.webp')),
}
(SRC / 'source-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
