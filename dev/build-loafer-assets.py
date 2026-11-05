#!/usr/bin/env python3
"""Normalize and extract genuine penny-loafer reference edits.
The high vamp is image-edited; source calf is immutable accepted cel artwork.
No runtime generation, pixel readback, or external dependencies.
"""
from pathlib import Path
import json,shutil
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/loafer-source'
def read(p,size=None):
 im=Image.open(p).convert('RGBA');return np.array(im.resize(size,Image.Resampling.LANCZOS) if size else im)
def save(folder,part,rgb,alpha):
 out=np.empty((*alpha.shape,4),np.uint8);out[:,:,:3]=rgb;out[:,:,3]=np.clip(alpha,0,255).astype('uint8');Image.fromarray(out).save(ROOT/f'assets/{folder}/loafer_{part}.webp',lossless=True,method=6)
def blur(a,n=.65):return cv2.GaussianBlur(a.astype('float32'),(0,0),n)
def largest(a):
 n,l,s,_=cv2.connectedComponentsWithStats(a.astype('uint8'),8);return (l==1+np.argmax(s[1:,cv2.CC_STAT_AREA])).astype('uint8')
meta={}
for view,folder,size,part in [('product','shoe2d',(1024,640),'base'),('fitting','fitting2d',(1024,1024),'shoe')]:
 src=read(SRC/(view+'.png'),size)
 if view=='product':
  im=Image.open(SRC/'product.png').convert('RGBA');a=np.array(im)[:,:,3];yy,xx=np.where(a>192);bounds=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));crop=im.crop(bounds);height=round(crop.height*833/crop.width);crop=crop.resize((833,height),Image.Resampling.LANCZOS);im=Image.new('RGBA',size);im.paste(crop,(96,541-height));src=np.array(im)
 rgb=src[:,:,:3].astype('float32');r,g,b=rgb.transpose(2,0,1);alpha=src[:,:,3].astype('float32');Y,X=np.indices(alpha.shape)
 if view=='product':
  shell=alpha
  # Warm lining is a separate connected aperture. Saddle/apron stitching
  # remains inside the cloth rather than being misclassified as the insole.
  warm=((r-b>22)&(alpha>30)&(Y<430)).astype('uint8')
  n,l,s,_=cv2.connectedComponentsWithStats(warm,8);ids=[i for i in range(1,n) if s[i,cv2.CC_STAT_AREA]>2000 and s[i,cv2.CC_STAT_TOP]<260];interior=np.isin(l,ids).astype('uint8')
  interior=cv2.morphologyEx(interior,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
  contours,_=cv2.findContours(interior,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(interior,contours,-1,1,cv2.FILLED);interior=interior.astype('float32')
  # The low tan outsole follows the original last, not a horizontal cut.
  seam=np.interp(X,[0,100,200,300,400,500,600,700,800,900,1024],[510,510,526,532,531,525,497,456,418,395,395]);sole=(Y>=seam).astype('float32')
  sole*=((r-b>20)|(Y>=seam+4));sole*=alpha/255
  interior=blur(interior,.5)*alpha/255
  # Keep only a very narrow original collar piping. Raised saddle and apron
  # construction are fully tinted, including their warm source shadows.
  edge=np.maximum(0,cv2.dilate((interior>0.3).astype('uint8'),np.ones((3,3),np.uint8))-interior)
  upper=np.clip(1-interior-edge-sole,0,1)*shell
  save(folder,'binding',255,np.maximum(0,shell-upper-interior*255-sole*255))
  save(folder,'insole',255,interior*255);save(folder,'sole',255,sole*255)
 else:
  # Source-neutral cloth is cleanly distinct from peach skin. Resolve its
  # exact curved collar, then retain the whole warm outsole below it.
  seed=((r-g<22)&(r-b<57)&(alpha>70)&(Y>490)).astype('uint8');seed=cv2.morphologyEx(seed,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));seed=largest(seed)
  top=np.where(seed>0,Y,1024).min(axis=0);geometry=(Y>=top[None,:]).astype('float32')
  silhouette=blur(cv2.morphologyEx((alpha>100).astype('uint8')*255,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)),.65);shell=blur(geometry)*silhouette
  # Continuous broad upper down to the narrow tan welt. Every warm fold of
  # the sewn penny saddle is cloth; no cream islands on black velvet.
  bottom=np.where(shell>100,Y,-1).max(axis=0)
  # Follow the actual outsole rather than an approximate arch polyline;
  # the latter left a broad cream fabric island on the rising outer waist.
  soleband=(Y>=bottom[None,:]-7)
  heelim=Image.new('L',size);ImageDraw.Draw(heelim).polygon([(696,749),(735,726),(787,696),(798,741),(754,783),(698,795)],fill=255)
  heel=(np.array(heelim)>0)&(r-b>28)
  upper=shell*blur((~(soleband|heel)).astype('float32'),.6)
  # Preserve a restrained 2px ivory stitched collar at the skin join.
  rim=(Y<top[None,:]+1.5);upper[rim]=0
  legs=read(ROOT/'assets/fitting2d/flat_legs.webp');save(folder,'legs',legs[:,:,:3],legs[:,:,3])
  occ=shell.copy();occ[Y>650]=np.maximum(occ[Y>650],255-silhouette[Y>650]);save(folder,'occlusion',255,occ)
 save(folder,part,rgb,shell);save(folder,'upper',255,upper)
 lum=blur(rgb@np.array([.2126,.7152,.0722]),3)
 save(folder,'shadow',0,np.clip((242-lum)/155,0,.65)*upper);save(folder,'highlight',255,np.clip((lum-205)/65,0,.6)*upper)
 Image.fromarray(np.dstack([rgb,shell]).clip(0,255).astype('uint8')).save(SRC/(view+'-normalized.png'))
 meta[view]={'source':view+'.png','frame':list(size),'sourceAlphaPreserved':True,'shoePixels':int((shell>127).sum()),'upperPixels':int((upper>127).sum()),'bodyBase':'genuine image edit','skinBase':'accepted flat cel leg, exact pixels' if view=='fitting' else None}
(SRC/'export.json').write_text(json.dumps(meta,indent=2))
sheet=Image.new('RGB',(1440,800),'#eafff2');d=ImageDraw.Draw(sheet)
for j,(folder,p) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 im=Image.open(ROOT/f'assets/{folder}/loafer_{p}.webp').convert('RGBA')
 if j:
  leg=Image.open(ROOT/'assets/fitting2d/loafer_legs.webp').convert('RGBA');occ=Image.open(ROOT/'assets/fitting2d/loafer_occlusion.webp').getchannel('A');import PIL.ImageChops as C;leg.putalpha(C.subtract(leg.getchannel('A'),occ));leg.alpha_composite(im);im=leg
 im.thumbnail((700,740));sheet.paste(im,(j*720,0),im);d.text((j*720+12,760),folder+' neutral penny loafer',fill='#225e47')
sheet.save(SRC/'export-contact.jpg',quality=95)
print(json.dumps(meta,indent=2))
