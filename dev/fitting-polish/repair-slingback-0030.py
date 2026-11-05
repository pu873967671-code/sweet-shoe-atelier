from pathlib import Path
from PIL import Image, ImageChops, ImageFilter

root = Path(__file__).resolve().parents[2]
assets = root / 'assets/fitting2d'
source = root / 'dev/fitting-polish/slingback-0030-source'

Image.open(assets / 'slingback_legs.webp').save(assets / 'bowsling_legs.webp', lossless=True, exact=True)
shoe = Image.open(source / 'bowsling_shoe.webp').convert('RGBA')
repaired = Image.open(assets / 'slingback_shoe.webp').convert('RGBA')
shoe.paste(repaired.crop((650, 480, 900, 760)), (650, 480))
shoe.save(assets / 'bowsling_shoe.webp', lossless=True, exact=True)

for style in ('slingback', 'bowsling'):
    mask = Image.open(source / f'{style}_hosiery.webp').convert('RGBA')
    alpha = mask.getchannel('A')
    expanded = alpha.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(.65))
    shoe_alpha = Image.open(assets / f'{style}_shoe.webp').convert('RGBA').getchannel('A')
    expanded = ImageChops.multiply(expanded, shoe_alpha)
    region = Image.new('L', mask.size)
    region.paste(expanded.crop((650, 480, 900, 760)), (650, 480))
    mask.putalpha(ImageChops.lighter(alpha, region))
    mask.save(assets / f'{style}_hosiery.webp', lossless=True, exact=True)
