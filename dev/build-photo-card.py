#!/usr/bin/env python3
"""Build the fitting-card pictures and their colour masks from photos/.

Input:  photos/<shape>__<sock>.png  (1024x1536, made by dev/generate-photos.py)
Output: assets/photo-card/<shape>__<sock>.webp       the picture, 720x1080
        assets/photo-card/<shape>__<sock>__mask.webp R = shoe, G = sock (0-255)

Every picture of a shape is an edit of that shape's bare-leg picture and stays
pixel-aligned with it, so the masks are cut automatically:
  shoe  the white satin is cooler (red minus blue) than skin, carpet and floor,
        measured on the bare-leg picture and shared by all its sock pictures
  sock  whatever changed from the bare-leg picture, outside the shoe

The game multiplies the masked areas by the chosen shoe and sock colours
(js/photo-card.js). Black sheer and pantyhose keep their own colour, so their
masks carry the shoe only.

  python dev/build-photo-card.py            # all pictures
  python dev/build-photo-card.py flat maryjane
  python dev/build-photo-card.py --debug    # also writes overlays to photos/_jobs/mask-lab/
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC, OUT, LAB = ROOT / 'photos', ROOT / 'assets/photo-card', ROOT / 'photos/_jobs/mask-lab'
SIZE = (720, 1080)
SHAPES = ['flat', 'block', 'kitten', 'stiletto6', 'stiletto9', 'wedge', 'maryjane', 'ballet', 'slingback', 'loafer',
          'platform', 'bootie', 'pearlpump', 'bowsling', 'crystalpump', 'studpump', 'bowmule', 'pearlheel',
          'luciteheel', 'crystalsandal']
SOCKS = ['none', 'frill', 'lace', 'sheer', 'knee', 'blacksheer', 'pantyhose', 'opaque', 'fishnet']
FIXED_COLOUR = {'blacksheer', 'pantyhose'}


def rgb(path):
    return np.asarray(Image.open(path).convert('RGB').resize(SIZE, Image.LANCZOS)).astype(np.float32)


def as_image(a):
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


def clean(alpha, open_px=5, blur=1.2):
    """Drop thin lines and specks (tile grout, sparkles), then soften the edge."""
    im = as_image(alpha)
    im = im.filter(ImageFilter.MinFilter(open_px)).filter(ImageFilter.MaxFilter(open_px))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im).astype(np.float32) / 255


def grow(alpha, px):
    return np.asarray(as_image(alpha).filter(ImageFilter.MaxFilter(px))).astype(np.float32) / 255


def shoe_mask(bare):
    # The satin is lavender-white: green at or below blue (floor and skin: green
    # 6+ above blue) and only mildly warm even where it reflects the pink floor.
    warmth = bare[..., 0] - bare[..., 2]      # skin ~40, floor ~22-32, white satin ~0-17
    lavender = bare[..., 1] - bare[..., 2]    # satin -6..3, floor and skin 6..13
    light = bare.mean(-1)
    alpha = np.clip((6.5 - lavender) / 4, 0, 1) * np.clip((26 - warmth) / 6, 0, 1) * np.clip((light - 120) / 40, 0, 1)
    alpha = clean(alpha, open_px=3, blur=0)
    # Warm reflections in the satin leave weak patches inside the shoe; fill the
    # silhouette solid so dark colours cover evenly.
    core = as_image((alpha > .3).astype(np.float32)).filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.MinFilter(11))
    solid = np.asarray(core).astype(np.float32) / 255
    alpha = np.maximum(alpha, solid) * big_parts(solid > .5)
    return np.asarray(as_image(alpha).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255


def big_parts(binary, step=4, min_area=40):
    """Keep only pieces at least shoe-part sized (drops cool specks in the marble).

    Labelled at quarter resolution; the kept area is grown back a little so the
    full-resolution edges are not trimmed."""
    small = binary[::step, ::step]
    h, w = small.shape
    keep = np.zeros_like(small, dtype=bool)
    seen = np.zeros_like(small, dtype=bool)
    for y0, x0 in zip(*np.nonzero(small)):
        if seen[y0, x0]:
            continue
        stack, part = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop(); part.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and small[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; stack.append((ny, nx))
        if len(part) >= min_area:
            ys, xs = zip(*part); keep[ys, xs] = True
    full = np.kron(keep, np.ones((step, step)))[:binary.shape[0], :binary.shape[1]].astype(np.float32)
    return grow(full, 2 * step + 1)


def sock_mask(pic, bare, shoe):
    # White hosiery is far cooler than the skin or floor it covers; how much
    # cooler a pixel became is how much sock is there (sheer and mesh: part).
    blur = lambda a: np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32)
    bare, pic = blur(bare), blur(pic)
    warm_bare, warm_pic = bare[..., 0] - bare[..., 2], pic[..., 0] - pic[..., 2]
    drop = warm_bare - warm_pic
    alpha = np.clip((drop - 3) / np.maximum(warm_bare - 8, 10), 0, 1)
    alpha = clean(alpha * (1 - grow(shoe, 5)), open_px=3, blur=1.0)
    return np.where(alpha < .08, 0, alpha)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    debug = '--debug' in sys.argv
    shapes = args or SHAPES
    OUT.mkdir(parents=True, exist_ok=True)
    if debug:
        LAB.mkdir(parents=True, exist_ok=True)
    for shape in shapes:
        bare = rgb(SRC / f'{shape}__none.png')
        shoe = shoe_mask(bare)
        # Sheer white tights barely cool the skin; they take a half-strength
        # tint over the leg, which the opaque-tights picture outlines exactly.
        legs = sock_mask(rgb(SRC / f'{shape}__opaque.png'), bare, shoe)
        for sock in SOCKS:
            path = SRC / f'{shape}__{sock}.png'
            if not path.exists():
                print('missing', path.name); continue
            pic = bare if sock == 'none' else rgb(path)
            socks = np.zeros_like(shoe) if sock == 'none' or sock in FIXED_COLOUR else sock_mask(pic, bare, shoe)
            if sock == 'sheer':  # pulled in a little so the tint never touches the floor
                inner = np.asarray(as_image(legs).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255
                socks = np.maximum(socks, .5 * inner)
            name = f'{shape}__{sock}'
            Image.fromarray(pic.astype(np.uint8)).save(OUT / f'{name}.webp', quality=82, method=6)
            mask = np.stack([shoe, socks, np.zeros_like(shoe)], -1)
            # Masks are smooth: half resolution, lossless (lossy WebP would bleed R into G).
            Image.fromarray(np.clip(mask * 255, 0, 255).astype(np.uint8)).resize((SIZE[0] // 2, SIZE[1] // 2), Image.LANCZOS) \
                .save(OUT / f'{name}__mask.webp', lossless=True, method=6)
            if debug:
                over = pic.copy()
                over[..., 0] = over[..., 0] * (1 - shoe * .7) + 255 * shoe * .7
                over[..., 1] = over[..., 1] * (1 - socks * .7) + 255 * socks * .7
                Image.fromarray(over.astype(np.uint8)).save(LAB / f'{name}.jpg', quality=80)
        print('built', shape)


if __name__ == '__main__':
    main()
