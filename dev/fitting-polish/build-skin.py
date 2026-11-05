#!/usr/bin/env python3
"""Offline cel finish of reviewed source paintings; no generated-art claim.

common: shared calf for review item 3.
heels: source-matched ankle/instep for item 4, identical upper-calf pixels.
Runtime exports are opt-in with --out assets/fitting2d.
"""
import argparse
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['common','heels','all'],default='all');p.add_argument('--out',default='dev/fitting-polish');args=p.parse_args();out=ROOT/args.out;out.mkdir(exist_ok=True,parents=True)
SIZE=(1024,1024);Y,X=np.indices(SIZE)

def read(name):return np.array(Image.open(ROOT/'dev/fitting-source'/name).convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS))

def soften_alpha(alpha):
    alpha=cv2.morphologyEx(alpha,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    alpha=cv2.GaussianBlur(alpha,(0,0),.65)
    alpha[alpha<4]=0
    return alpha

def cel(a,alpha):
    rgb=a[:,:,:3].copy()
    # Inpaint only empty matte before broad smoothing: hidden RGB must never
    # introduce coloured seams into the visible skin edge.
    rgb=cv2.inpaint(rgb,(alpha<10).astype('uint8'),5,cv2.INPAINT_TELEA)
    smooth=cv2.bilateralFilter(rgb,17,35,15).astype('float32')
    light=cv2.GaussianBlur(smooth@np.array([.2126,.7152,.0722],dtype='float32'),(0,0),6)
    # Five broad value bands, softly joined; no pores/freckles/noise bitmap.
    light=np.clip((light-145)/94,0,1)
    bands=np.round(light*8)/8
    bands=cv2.GaussianBlur(bands,(0,0),5.0)
    shade=np.array([219,155,141],dtype='float32');hi=np.array([255,230,206],dtype='float32')
    result=shade[None,None,:]+bands[:,:,None]*(hi-shade)[None,None,:]
    return np.dstack((np.clip(result,0,255).astype('uint8'),soften_alpha(alpha)))

base=read('barefoot.png');a=base[:,:,3].copy();r,g,b=base[:,:,:3].astype('float32').transpose(2,0,1);a[(g>r+15)&(g>b+15)]=0
common=cel(base,a)
# Source canvas is unchanged; composition/short-calf framing belongs to render.
if args.phase in ['common','all']:Image.fromarray(common).save(out/'legs.webp',lossless=True)
if args.phase in ['heels','all']:
    for heel in ['flat','kitten','block','wedge']:
        src=read(heel+'.png');r,g,b=src[:,:,:3].astype('float32').transpose(2,0,1)
        skin=((r-g>25)&(r-b>41)&(src[:,:,3]>64)&(Y<910)).astype('uint8')
        skin[(Y<470)&(src[:,:,3]>64)]=1
        skin=cv2.morphologyEx(skin,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
        skin=cv2.morphologyEx(skin,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        n,labels,stats,_=cv2.connectedComponentsWithStats(skin,8)
        skin=(labels==(1+np.argmax(stats[1:,cv2.CC_STAT_AREA]))).astype('uint8')
        contours,_=cv2.findContours(skin,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(skin,contours,-1,1,cv2.FILLED)
        alpha=src[:,:,3]*skin
        lower=cel(src,alpha)
        # All finish choices and heel types share exact calf pixels through
        # y400; only lower ankle/foot follows the actual shoe-specific painting.
        mix=np.clip((Y-400)/100,0,1)[:,:,None]
        merged=(common.astype('float32')*(1-mix)+lower.astype('float32')*mix).astype('uint8')
        Image.fromarray(merged).save(out/(heel+'_legs.webp'),lossless=True)
        # Larger mask suppresses the old shared toes/heel behind a new source.
        # Root renderer must choose this matching source with its original shoe.
    sheet=Image.new('RGB',(1024,360),'#e4f9ee');draw=ImageDraw.Draw(sheet)
    for i,heel in enumerate(['flat','kitten','block','wedge']):
        leg=Image.open(out/(heel+'_legs.webp')).convert('RGBA')
        shoe=Image.open(ROOT/'assets/fitting2d'/(heel+'_shoe.webp')).convert('RGBA')
        leg.alpha_composite(shoe);leg.thumbnail((256,330));sheet.paste(leg,(i*256,0),leg);draw.text((i*256+8,338),heel,fill='#315d4e')
    sheet.save(out/'skin-contact.jpg',quality=94)
print('PASS',args.phase,'broad cel skin; fixed1024 frames; common y0..400')
