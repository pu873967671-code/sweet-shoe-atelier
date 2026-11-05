#!/usr/bin/env python3
"""Original code-native pearl-orb heel on the accepted 6cm pump cameras.

The upper, exposed skin, toe and forefoot ground pixels remain the existing
painting. Only the distal heel stem is replaced, by a soft nacre sphere between
small champagne fittings. This is native authored geometry, not generated art.
"""
from pathlib import Path
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'dev/pearlheel-source'
SRC.mkdir(exist_ok=True)
CONFIG = {
    'product': {'folder': 'shoe2d', 'base': 'base', 'start': 326,
                'left': 800, 'center': (846, 404), 'radii': (57, 60),
                'cap': (825, 459, 869, 479), 'toe': 96, 'floor': 540},
    'fitting': {'folder': 'fitting2d', 'base': 'shoe', 'start': 714,
                'left': 704, 'center': (754, 791), 'radii': (47, 53),
                'cap': (734, 838, 774, 867), 'toe': 171, 'floor': 964},
}


def save(path, array):
    Image.fromarray(np.clip(array, 0, 255).astype('uint8')).save(
        path, lossless=True, method=6, exact=True)


def geometry(shape, cfg):
    h, w = shape
    y, x = np.indices(shape, dtype=float)
    cx, cy = cfg['center']; rx, ry = cfg['radii']
    u, v = (x-cx)/rx, (y-cy)/ry
    d = u*u + v*v
    alpha = np.clip((1-np.sqrt(d))*min(rx, ry)+.5, 0, 1)
    z = np.sqrt(np.clip(1-d, 0, 1))
    # Broad youthful cartoon shading: warm rose shadow, soft mint reflected
    # light, creamy upper-left gleam, with no noisy or hard mirror streaks.
    light = np.clip(-.28*u-.32*v+.65*z+.17, 0, 1)
    pearl = np.array([180, 160, 163])[None,None,:] + light[:,:,None]*np.array([73,88,72])[None,None,:]
    gleam = np.exp(-((u+.34)**2/.075+(v+.39)**2/.05))
    pearl += gleam[:,:,None]*np.array([18,18,22])[None,None,:]
    pearl += np.exp(-((u-.42)**2/.23+(v-.32)**2/.20))[:,:,None]*np.array([0,9,12])[None,None,:]
    sphere = np.dstack([pearl, alpha*255])
    # Use high-resolution native ellipses for the tiny mounts, preserving
    # smooth contours when inspected at source resolution or zoomed.
    scale = 4
    hardware = Image.new('RGBA',(w*scale,h*scale))
    p = ImageDraw.Draw(hardware)
    def ellipse(box, fill): p.ellipse(tuple(round(n*scale) for n in box), fill=fill)
    def rectangle(box, fill): p.rectangle(tuple(round(n*scale) for n in box), fill=fill)
    neck_width = rx*.36
    rectangle((cx-neck_width,cfg['start']-2,cx+neck_width,cy-ry+6),'#bc9370')
    rectangle((cx-neck_width*.55,cfg['start']-2,cx+neck_width*.28,cy-ry+6),'#f6dfb3')
    ellipse((cx-rx*.42,cy-ry-5,cx+rx*.42,cy-ry+6),'#b38c6e')
    ellipse((cx-rx*.39,cy-ry-5,cx+rx*.39,cy-ry+2),'#f7dfb3')
    cap=cfg['cap']
    rectangle((cx-neck_width,cy+ry-5,cx+neck_width,cap[3]-5),'#c59d77')
    ellipse((cap[0],cap[1],cap[2],cap[3]),'#9a765f')
    ellipse((cap[0]+1,cap[1],cap[2]-1,cap[3]-5),'#d9b78e')
    hardware=hardware.resize((w,h),Image.Resampling.LANCZOS)
    out=hardware.copy();out.alpha_composite(Image.fromarray(np.clip(sphere,0,255).astype('uint8')))
    return out


metadata={}
for view,cfg in CONFIG.items():
    folder=ROOT/'assets'/cfg['folder']
    original=np.array(Image.open(folder/f"stiletto6_{cfg['base']}.webp").convert('RGBA'))
    y,x=np.indices(original.shape[:2])
    region=(y>=cfg['start']) & (x>=cfg['left'])
    # The small original heel contact is retained below the new mount.
    shell=original.copy();shell[region]=0
    support=geometry(original.shape[:2],cfg)
    result=Image.fromarray(shell);result.alpha_composite(support)
    output=np.array(result)
    support_alpha=np.array(support)[:,:,3]
    untouched=~region & (support_alpha==0)
    output[untouched]=original[untouched]
    save(folder/f"pearlheel_{cfg['base']}.webp",output)
    save(SRC/f'{view}-support.webp',np.array(support))
    for part in ['upper','shadow','highlight']:
        effect=np.array(Image.open(folder/f'stiletto6_{part}.webp').convert('RGBA'))
        effect[region,3]=0
        effect[:,:,3]=(effect[:,:,3]*(1-support_alpha/255)).astype('uint8')
        save(folder/f'pearlheel_{part}.webp',effect)
    if view=='product':
        for part in ['binding','insole','sole']:
            effect=np.array(Image.open(folder/f'stiletto6_{part}.webp').convert('RGBA'))
            effect[region,3]=0
            save(folder/f'pearlheel_{part}.webp',effect)
    else:
        for part in ['legs','occlusion']:
            shutil.copyfile(folder/f'stiletto6_{part}.webp',folder/f'pearlheel_{part}.webp')
    original_bounds=Image.fromarray(original[:,:,3]).point(lambda a:255 if a>127 else 0).getbbox()
    bounds=Image.fromarray(output[:,:,3]).point(lambda a:255 if a>127 else 0).getbbox()
    assert bounds[0]==original_bounds[0]==cfg['toe']
    assert bounds[3]-1==original_bounds[3]-1==cfg['floor']
    assert np.array_equal(output[untouched],original[untouched])
    assert (support_alpha[y<cfg['start']-5]==0).all()
    metadata[view]={'base':'stiletto6','frame':[output.shape[1],output.shape[0]],
        'toeX':cfg['toe'],'groundY':cfg['floor'],'heelOnlyRegion':cfg,
        'exactUpperOutsideSupport':True,'source':'original code-native sphere and mounts'}

(SRC/'export.json').write_text(json.dumps(metadata,indent=2)+'\n')
(SRC/'anchors.json').write_text(json.dumps(metadata,indent=2)+'\n')
sheet=Image.new('RGB',(1440,1100),'#f8fff5');p=ImageDraw.Draw(sheet)
for col,(folder,part) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
    for row,bg in enumerate(['#fff4ed','#233c43']):
        im=Image.open(ROOT/f'assets/{folder}/pearlheel_{part}.webp').convert('RGBA')
        if col:
            skin=Image.open(ROOT/'assets/fitting2d/pearlheel_legs.webp').convert('RGBA')
            skin.putalpha(ImageChops.subtract(skin.getchannel('A'),Image.open(ROOT/'assets/fitting2d/pearlheel_occlusion.webp').getchannel('A')))
            skin.alpha_composite(im);im=skin
        im.thumbnail((690,510));tile=Image.new('RGB',(720,550),bg)
        tile.paste(im,((720-im.width)//2,0),im);sheet.paste(tile,(col*720,row*550))
        p.text((col*720+12,row*550+525),folder+' / original pearl orb heel / accepted upper and calf',fill='#f680ae')
sheet.save(SRC/'export-contact.jpg',quality=95)
print('PASS: full 13-layer original pearl-orb kit; toe/floor fixed; exact accepted upper and skin')
