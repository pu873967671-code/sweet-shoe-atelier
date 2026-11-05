#!/usr/bin/env python3
"""Fixed reusable bitmap patches from the atelier's original painted accessories.
No runtime synthesis. Original painted bow, pearls, jewellery retained; satin bands
use a texture crop from the existing painted bow. AI generation is pending a usable
built-in output, so this importer records original-art provenance explicitly.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/shoe2d/accessories';OUT.mkdir(exist_ok=True)
def source(name):
    im=Image.open(ROOT/'assets'/f'{name}.webp').convert('RGBA')
    return im.crop(im.getbbox())
def save(name,im): im.save(OUT/f'{name}.webp',lossless=True,method=6)
bow=source('bow')
# Fixed satin grade: retain the original painted folds, with a rich rose fold
# valley, candy mids and a warm ivory specular crest. A luminance-only sharpen
# strengthens fine gathers without changing this source's contour or alpha.
lum=bow.convert('RGB').convert('L').filter(ImageFilter.UnsharpMask(radius=1.2,percent=95,threshold=2))
stops=[(0,(108,43,70)),(145,(151,63,96)),(185,(196,98,133)),
       (211,(234,139,173)),(232,(252,185,207)),(255,(255,242,235))]
def satin(value):
    for (lo,c0),(hi,c1) in zip(stops,stops[1:]):
        if value<=hi:
            t=max(0,(value-lo)/(hi-lo))
            return tuple(round(a+(b-a)*t) for a,b in zip(c0,c1))
    return stops[-1][1]
pixels=[]
for (r,g,b,alpha),light in zip(bow.getdata(),lum.getdata()):
    # Discard chroma-key debris only; pink satin never has a cyan/green edge.
    if alpha and g>r*1.12 and b>r*1.12:alpha=0
    pixels.append((*satin(light),alpha))
bow.putdata(pixels)
save('bow',bow)
for name,src in [('drop','pearl_drop'),('crystal','charm_crystal'),('flower','flower'),('pearl','charm_pearl')]:save(name,source(src))
# Seven substantially larger painted pearls retain their own spherical light,
# warm gold rims and nacre. The fine silk thread is visible only in tiny gaps.
pearl=source('charm_pearl');pearl.thumbnail((62,62),Image.Resampling.LANCZOS)
strand=Image.new('RGBA',(390,91))
centres=[(31+i*54,31+round(math.sin(i/6*math.pi)*20))for i in range(7)]
thread=ImageDraw.Draw(strand)
thread.line(centres,fill='#ad8278',width=5,joint='curve')
thread.line([(x,y-1)for x,y in centres],fill='#fff0d3',width=2,joint='curve')
for x,y in centres:strand.alpha_composite(pearl,(x-pearl.width//2,y-pearl.height//2))
save('pearls',strand.crop(strand.getbbox()))
# Satin ribbon texture comes from the painted bow's luminous central knot.
texture=bow.crop((int(bow.width*.46),int(bow.height*.38),int(bow.width*.54),int(bow.height*.49)))
def ribbon(size,points,width):
    out=Image.new('RGBA',size);mask=Image.new('L',size);d=ImageDraw.Draw(mask)
    d.line(points,fill=255,width=width,joint='curve')
    for x,y in [points[0],points[-1]]:d.ellipse((x-width//2,y-width//2,x+width//2,y+width//2),fill=255)
    fabric=texture.resize(size,Image.Resampling.BICUBIC);fabric.putalpha(mask)
    out.alpha_composite(fabric)
    edge=ImageDraw.Draw(out);edge.line([(x,y-width//2+2) for x,y in points],fill='#f6e9d0',width=2,joint='curve')
    return out
band=ribbon((300,92),[(16,22),(65,32),(125,49),(180,60),(235,62),(276,48)],26)
b=ImageDraw.Draw(band);b.rounded_rectangle((244,35,275,65),radius=7,outline='#b58c4f',width=5);b.line((259,39,259,61),fill='#ffefc8',width=2)
save('maryjane',band.crop(band.getbbox()))
# Supersampled cord work: shaded edge, warm silk body and a fine highlight.
# Little inset eyelets give each crossing a physical attachment to the upper.
scale=3
laces=Image.new('RGBA',(160*scale,145*scale));b=ImageDraw.Draw(laces)
def line(points,color,width):
    b.line([(round(x*scale),round(y*scale))for x,y in points],fill=color,width=round(width*scale),joint='curve')
def ellipse(box,**kw):b.ellipse(tuple(round(v*scale)for v in box),**{k:(round(v*scale)if k=='width' else v)for k,v in kw.items()})
for y in [20,58,96]:
    for x in [26,134]:
        ellipse((x-10,y-9,x+10,y+11),fill='#8e6662')
        ellipse((x-9,y-10,x+9,y+8),fill='#c7a05e',outline='#ffedbf',width=2)
        ellipse((x-4,y-5,x+4,y+3),fill='#916953',outline='#d2b887',width=1)
    for points in [[(27,y),(58,y+12),(103,y+26),(133,y+35)],[(133,y),(104,y+12),(58,y+26),(27,y+35)]]:
        line([(x+1,yy+2)for x,yy in points],'#8f6e79',10)
        line(points,'#d5aab5',9)
        line([(x,yy-1)for x,yy in points],'#fff0e4',6)
        line([(x,yy-2.5)for x,yy in points],'#fff9ed',1.5)
laces=laces.resize((160,145),Image.Resampling.LANCZOS)
save('laces',laces.crop(laces.getbbox()))
(OUT/'PROVENANCE.md').write_text('Static patches imported from existing original atelier paintings: bow.webp, charm_pearl.webp, pearl_drop.webp, charm_crystal.webp, flower.webp. The satin bow preserves source alpha and painted folds, with a deterministic rose/ivory luminance grade and fine luminance sharpening. The seven-bead pearl strand duplicates the same spherical painted pearl with a short silk connector. Mary Jane ribbon reuses bow satin texture; laces are local supersampled shaded cords with gold eyelets. Runtime adds shoe-contact shadows and a fitted instep band. Rebuild: python3 dev/build-shoe2d-accessories.py (Pillow only). No new AI-generated source is claimed.\n')
print('Saved',len(list(OUT.glob('*.webp'))),'fixed painted patches')
