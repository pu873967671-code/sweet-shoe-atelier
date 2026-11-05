#!/usr/bin/env python3
"""Import generated neutral shoe edits into a stable, pixel-identical painted kit.

Generation: /workspace/work/gen/edit.py shoe2d_<heel> dev/refs/shoe2d_test.jpg
Prompts/provenance: dev/shoe2d-source/prompts.json. Runtime never regenerates art.
All exported layers share their source alpha and the SAME affine placement.
"""
from pathlib import Path
import json, argparse, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/shoe2d'
SOURCE = ROOT / 'dev/shoe2d-source'
SIZE = (1024, 640)
TOE, RIGHT, GROUND = 96, 928, 540
HEELS = ('flat', 'kitten', 'block', 'wedge')
# Reviewed source-coordinate cleanup is authored after initial contact-sheet inspection.
# Polygon coordinates are in NORMALIZED 1024x640 canvas pixels.
LANDMARKS = {
    'flat': {'interiorRegion': [(285,385),(500,365),(720,240),(855,158),(883,174),(848,265),(720,365),(560,430),(405,425)], 'insoleSeed': (680,300)},
    'kitten': {'interiorRegion': [(330,365),(545,292),(750,120),(860,53),(882,77),(845,185),(735,325),(615,423),(490,423)], 'insoleSeed': (680,250)},
    'block': {'interiorRegion': [(320,377),(520,303),(700,145),(845,52),(876,66),(853,149),(760,300),(650,410),(510,435)], 'insoleSeed': (680,250)},
    'wedge': {'interiorRegion': [(318,370),(520,303),(730,120),(850,51),(879,68),(851,156),(745,309),(640,400),(505,405)], 'insoleSeed': (680,250)},
}

def polygon(points):
    im = Image.new('L', SIZE)
    if points: ImageDraw.Draw(im).polygon(points, fill=255)
    return np.array(im, dtype=float) / 255

def write(name, rgb, alpha):
    rgb = np.broadcast_to(np.asarray(rgb), (*alpha.shape, 3))
    # 32 alpha stops preserve antialias edges; smooth light maps avoid noisy ZIPs.
    alpha=np.round(np.clip(alpha,0,1)*31)/31
    a = np.dstack((rgb, alpha * 255)).clip(0,255).astype('uint8')
    Image.fromarray(a, 'RGBA').save(OUT / name, lossless=True, method=6)

def key(src):
    source_alpha=np.array(src.convert('RGBA'),dtype=float)[...,3]/255
    a=np.array(src.convert('RGB'), dtype=float)
    r,g,b=a[...,0],a[...,1],a[...,2]
    spill=np.maximum(0,g-np.maximum(r,b))
    alpha=np.clip(1-(spill-12)/110,0,1)*source_alpha
    # Remove the chroma matte from semi-transparent edge pixels.
    a[...,1]=np.where(spill>12,np.minimum(g,np.maximum(r,b)),g)
    return Image.fromarray(np.dstack([a,alpha*255]).clip(0,255).astype('uint8'),'RGBA')

def build(heel):
    src=SOURCE/f'{heel}.png'
    if not src.exists():
        gen=Path('/workspace/work/gen/raw')/f'shoe2d_{heel}.png'
        if not gen.exists(): raise SystemExit(f'Missing generated source {gen}')
        shutil.copy2(gen,src)
    im=key(Image.open(src))
    a=np.array(im)[...,3]
    yy,xx=np.where(a>192)
    bounds=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
    crop=im.crop(bounds)
    height=round(crop.height*(RIGHT-TOE)/crop.width)
    height=min(height,490)
    crop=crop.resize((RIGHT-TOE+1,height),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',SIZE)
    canvas.paste(crop,(TOE,GROUND-height+1))
    arr=np.array(canvas,dtype=float)
    rgb,alpha=arr[...,:3],arr[...,3]/255
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    warm=r-b
    # Satin is near-white neutral; insole/outsole/binding preserve their warm paint.
    upper=np.clip((24-warm)/12,0,1)*alpha
    region=LANDMARKS[heel]
    sole_regions={
      'flat':[(80,485),(300,512),(490,518),(600,490),(740,435),(940,370),(940,550),(80,550)],
      'kitten':[(80,505),(300,520),(500,520),(610,480),(710,400),(780,345),(940,335),(940,550),(80,550)],
      'block':[(80,505),(300,520),(500,520),(610,485),(720,385),(940,320),(940,550),(80,550)],
      'wedge':[(80,485),(300,500),(500,490),(650,440),(780,350),(940,250),(940,550),(80,550)],
    }
    sole_allowed=polygon(sole_regions[heel])
    # Reviewed hand-authored broad interior region excludes outsole, heel and weave.
    # Colour segmentation inside it follows the painted opening exactly.
    allowed=1-sole_allowed
    warm_pixels=(warm>16)&(alpha>.05)&(allowed>0)
    candidate=Image.fromarray((warm_pixels*255).astype('uint8'),'L').copy()
    seed=tuple(region['insoleSeed'])
    if candidate.getpixel(seed)==255:
        ImageDraw.floodfill(candidate,seed,128,thresh=0)
    interior=(np.array(candidate)==128).astype('uint8')*255
    # Interior and collar share cream colour: retain a 4px painted piping band.
    interior_im=Image.fromarray(interior,'L')
    insole=np.array(interior_im.filter(ImageFilter.MinFilter(5)),dtype=float)/255*alpha
    inner_edge=np.array(interior_im.filter(ImageFilter.MaxFilter(5)),dtype=float)/255
    binding=np.maximum(0,inner_edge-insole)*alpha
    sole=np.clip((warm-15)/14,0,1)*alpha*sole_allowed
    upper=np.clip((23-warm)/10,0,1)*alpha*(1-inner_edge)*(1-sole)
    # The block support is satin, including its shaded inner face and painted
    # vertical construction seam. Colour thresholding mistakes those warm
    # shadows for cream binding/leather and leaves a pale stripe after tinting.
    # A reviewed support-face polygon keeps the complete face in the SAME upper
    # mask; its tan bottom lift and the narrow arch welt remain protected.
    if heel == 'block':
        support=polygon([(744,384),(766,360),(790,340),(812,322),
                         (836,307),(865,290),(892,275),(917,259),
                         (917,446),(903,452),(879,458),(853,462),
                         (830,465),(802,460),(774,454),(744,447)])*alpha
        upper=np.maximum(upper,support)
        sole*=1-support
        binding*=1-support
    # Preserve all warm paint as binding/sole; no insole or rope receives tint.
    binding=np.maximum(binding,np.maximum(0,alpha-upper-insole-sole))
    lum=rgb@np.array([.2126,.7152,.0722])
    # Maps are deliberately restrained: near-white upper retains luminous colour.
    softlum=np.array(Image.fromarray(lum.clip(0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(.65)),dtype=float)
    shadow=np.clip((248-softlum)/175,0,.65)*upper
    highlight=np.clip((softlum-205)/65,0,.6)*upper
    canvas.save(OUT/f'{heel}_base.webp',quality=90,method=6)
    neutral=np.repeat((rgb@np.array([.2126,.7152,.0722]))[...,None],3,axis=2)
    write(f'{heel}_upper.webp',[255,255,255],upper)
    for part,mask in [('binding',binding),('insole',insole),('sole',sole)]:
        write(f'{heel}_{part}.webp',[255,255,255],mask)
    write(f'{heel}_shadow.webp',[0,0,0],shadow)
    write(f'{heel}_highlight.webp',[255,255,255],highlight)
    return {'source':str(src.relative_to(ROOT)),'sourceBounds':bounds,'canvas':list(SIZE),'toe':[TOE,GROUND], 'groundY':GROUND,'rightX':RIGHT,'length':RIGHT-TOE,'bbox':[TOE,GROUND-height+1,RIGHT+1,GROUND+1],'anchors':{'vamp':[350,GROUND-100],'counter':[837,GROUND-height*.65],'strap':[590,GROUND-height*.48]}}

def contact(meta):
    sheet=Image.new('RGB',(1024*2,720*2),'#f5f4f0')
    for i,heel in enumerate(HEELS):
        base=Image.open(OUT/f'{heel}_base.webp')
        x,y=(i%2)*1024,(i//2)*720
        sheet.paste(base,(x,y+45),base)
        d=ImageDraw.Draw(sheet)
        d.text((x+40,y+15),heel,fill='#493e51',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',26))
        d.line((x+40,y+45+GROUND,x+980,y+45+GROUND),fill='#e491b2',width=1)
        d.line((x+TOE,y+80,x+TOE,y+650),fill='#85c8bd',width=1)
    sheet.save(ROOT/'qa/shoe2d-source-contact.jpg',quality=92)
    masks=Image.new('RGB',(1024,4*320),'#e7efec')
    for i,heel in enumerate(HEELS):
        for j,part in enumerate(('base','upper','insole','sole')):
            im=Image.open(OUT/f'{heel}_{part}.webp');im.thumbnail((256,256))
            masks.paste(im,(j*256,i*320+35),im)
            ImageDraw.Draw(masks).text((j*256+10,i*320+10),f'{heel} {part}',fill='#323845')
    masks.save(ROOT/'qa/shoe2d-mask-contact.jpg',quality=92)

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True);SOURCE.mkdir(parents=True,exist_ok=True)
    meta={heel:build(heel) for heel in HEELS}
    (OUT/'anchors.json').write_text(json.dumps(meta,indent=2))
    contact(meta)
    print(json.dumps(meta,indent=2))
