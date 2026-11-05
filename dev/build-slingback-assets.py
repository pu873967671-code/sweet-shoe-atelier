#!/usr/bin/env python3
"""Fixed-frame slingback derivative from genuine reference edits.
The accepted kitten forefoot and calf stay exact; only open rear quarter changes.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/slingback-source'
def read(path,size=None):
 im=Image.open(path).convert('RGBA')
 return np.array(im.resize(size,Image.Resampling.LANCZOS) if size else im)
def save(folder,part,rgb,alpha):
 out=np.zeros((*alpha.shape,4),np.uint8);out[:,:,:3]=rgb;out[:,:,3]=np.clip(alpha,0,255).astype('uint8');Image.fromarray(out).save(ROOT/f'assets/{folder}/slingback_{part}.webp',lossless=True)
def largest(mask):
 n,l,stats,_=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
 return (l==(1+np.argmax(stats[1:,cv2.CC_STAT_AREA]))).astype('uint8')
def smooth(mask,sigma=.6):return cv2.GaussianBlur(mask.astype('float32'),(0,0),sigma)
def skin_finish(src,mask):
 rgb=cv2.inpaint(src[:,:,:3],(mask<10).astype('uint8'),5,cv2.INPAINT_TELEA)
 rgb=cv2.bilateralFilter(rgb,17,35,15).astype('float32');l=cv2.GaussianBlur(rgb@np.array([.2126,.7152,.0722],np.float32),(0,0),6)
 v=cv2.GaussianBlur(np.round(np.clip((l-145)/94,0,1)*8)/8,(0,0),5)
 rgb=np.array([219,155,141])[None,None,:]+v[:,:,None]*np.array([36,75,65])[None,None,:]
 return rgb.clip(0,255).astype('uint8')
meta={}
for view,folder,size,part in [('product','shoe2d',(1024,640),'base'),('fitting','fitting2d',(1024,1024),'shoe')]:
 old=read(ROOT/f'assets/{folder}/kitten_{part}.webp');src=read(SRC/(view+'.png'),size);h,w=old.shape[:2];Y,X=np.indices((h,w))
 if view=='product':
  # API preserves the design, but its output framing differs. Normalize all
  # rear pixels to the exact accepted toe/right/floor and source height.
  src0=Image.open(SRC/'product.png').convert('RGBA');a=np.array(src0)[:,:,3];yy,xx=np.where(a>127)
  crop=src0.crop((int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))).resize((833,490),Image.Resampling.LANCZOS)
  im=Image.new('RGBA',size);im.paste(crop,(96,51));src=np.array(im)
 r,g,b=src[:,:,:3].astype('float32').transpose(2,0,1);alpha=src[:,:,3].astype(float)
 if view=='product':
  shell=alpha
 else:
  # Reviewed boundaries follow the new heel opening. Colour thresholds
  # alone mistake the warm gold buckle and heel core for skin.
  boundary=np.interp(X,[0,640,665,700,740,780,810,1024],[1000,800,775,745,720,695,657,657])
  geometry=(Y>=boundary)
  strapim=Image.new('L',size);ImageDraw.Draw(strapim).polygon([(631,800),(668,716),(703,616),(726,563),(737,525),(735,485),(754,493),(768,520),(765,566),(740,606),(712,675),(688,741),(680,770)],fill=255)
  geometry=np.maximum(geometry,np.array(strapim)/255)
  neutralcloth=((r-g<25)&(r-b<59)&(Y>490))
  geometry=np.maximum(geometry,neutralcloth)
  shell=alpha*smooth(geometry)
 # Preserve every accepted forefoot pixel. A tiny overlap blends broad paint
 # only; the anatomy, source frame and floor do not move between finishes.
 mix=np.clip((X-(560 if view=='product' else 640))/24,0,1)
 basealpha=old[:,:,3]*(1-mix)+shell*mix
 rgb=(old[:,:,:3]*(1-mix[:,:,None])+src[:,:,:3]*mix[:,:,None]).clip(0,255)
 # Drop antialias crumbs while retaining the narrow satin heel strap.
 basealpha[basealpha<4]=0
 boundaryx=560 if view=='product' else 640
 basealpha[:,:boundaryx]=old[:,:boundaryx,3];rgb[:,:boundaryx]=old[:,:boundaryx,:3]
 save(folder,part,rgb,basealpha)
 warm=r-b
 neutral=((warm<25)&(alpha>30)).astype('uint8')
 if view=='product':
  # Original interior paint stays warm; segmentation follows actual opening.
  newupper=smooth(neutral)*shell
 else:
  # Whole authored satin strap and heel support take the selected swatch.
  # Warm painted shadows are fabric, not uncoloured binding islands.
  support=(X>690)&(Y>742)&(Y<832)
  cloth=(np.array(strapim)>0)|support
  # Preserve the petite gold buckle, and a narrow natural outsole seam.
  buckleim=Image.new('L',size);ImageDraw.Draw(buckleim).polygon([(722,540),(742,536),(758,549),(753,568),(743,592),(725,592),(712,578)],fill=255)
  cloth &= np.array(buckleim)==0
  newupper=np.maximum(smooth(neutral),smooth(cloth))*shell

 oldupper=read(ROOT/f'assets/{folder}/kitten_upper.webp')[:,:,3]
 upper=np.minimum(basealpha,oldupper*(1-mix)+newupper*mix)
 # Broad illumination prevents source fabric grain reading as velvet dots.
 lum=cv2.GaussianBlur(rgb@np.array([.2126,.7152,.0722]),(0,0),3)
 save(folder,'upper',255,upper)
 save(folder,'shadow',0,np.clip((242-lum)/155,0,.65)*upper)
 save(folder,'highlight',255,np.clip((lum-205)/65,0,.6)*upper)
 if view=='product':
  # Semantic masks are local drawing alpha; front cream binding and insole
  # remain exact. New rear warm paint is binding/insole, sole stays natural.
  for p in ['binding','insole','sole']:
   original=read(ROOT/f'assets/{folder}/kitten_{p}.webp')[:,:,3]
   if p=='sole':new=original*np.minimum(1,shell/255)
   elif p=='binding':new=np.maximum(0,shell-newupper)
   else:new=np.maximum(0,shell-newupper)*((Y<400)&(X<840))
   save(folder,p,255,original*(1-mix)+new*mix)
 else:
  # Exposed heel skin is a genuine painted addition in the edit. Preserve
  # the accepted calf/instep and source-match only the newly revealed heel.
  skin=alpha*(1-smooth(geometry))
  leg=read(ROOT/'assets/fitting2d/kitten_legs.webp')
  # The edit preserves the original ankle pose. Fill newly exposed lower
  # instep/heel continuously, with broad calf still byte-identical.
  region=np.clip((X-635)/25,0,1)*np.clip((Y-460)/40,0,1)*(Y<760)
  skin*=region
  newrgb=skin_finish(src,skin)
  oldleg=Image.fromarray(leg);newleg=Image.fromarray(np.dstack([newrgb,skin]).clip(0,255).astype('uint8'));oldleg.alpha_composite(newleg);leg=np.array(oldleg)
  save(folder,'legs',leg[:,:,:3],leg[:,:,3])
  original=read(ROOT/'assets/fitting2d/kitten_occlusion.webp')[:,:,3]
  occ=original*(1-mix)+basealpha*mix
  # Outside the edited lower silhouette, clear source foot leakage.
  silhouette=cv2.GaussianBlur((alpha>100).astype('float32')*255,(0,0),.65)
  occ[Y>650]=np.maximum(occ[Y>650],255-silhouette[Y>650])
  save(folder,'occlusion',255,occ)
 Image.fromarray(np.dstack([rgb,basealpha]).clip(0,255).astype('uint8')).save(SRC/(view+'-normalized.png'))
 meta[view]={'source':view+'.png','frame':list(size),'preservedForefootThroughX':560 if view=='product' else 640,'bodyBase':'kitten','newRearPixels':int(np.count_nonzero((basealpha>127)&(mix>0)))}
(SRC/'export.json').write_text(json.dumps(meta,indent=2))
sheet=Image.new('RGB',(1440,800),'#e7fff1');d=ImageDraw.Draw(sheet)
for j,(folder,p) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 im=Image.open(ROOT/f'assets/{folder}/slingback_{p}.webp').convert('RGBA')
 if j:
  legs=Image.open(ROOT/'assets/fitting2d/slingback_legs.webp').convert('RGBA');legs.alpha_composite(im);im=legs
 im.thumbnail((700,740));sheet.paste(im,(j*720,0),im);d.text((j*720+12,760),folder+' neutral slingback',fill='#225e47')
sheet.save(SRC/'export-contact.jpg',quality=95)
print(json.dumps(meta,indent=2))
