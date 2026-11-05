#!/usr/bin/env python3
"""Original backless bow mule: matched reference edits, fixed source frames."""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageChops
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/bowmule-source'
def read(p):return np.array(Image.open(p).convert('RGBA'))
def blur(a,s=.55):return cv2.GaussianBlur(a.astype('float32'),(0,0),s)
def largest(a):
 n,l,stats,_=cv2.connectedComponentsWithStats(a.astype('uint8'),8)
 return (l==1+np.argmax(stats[1:,cv2.CC_STAT_AREA])).astype('uint8')
def save(folder,part,rgb,alpha):
 a=np.zeros((*alpha.shape,4),np.uint8);a[:,:,:3]=rgb;a[:,:,3]=np.clip(alpha,0,255).astype('uint8');Image.fromarray(a).save(ROOT/f'assets/{folder}/bowmule_{part}.webp',lossless=True,method=6,exact=True)
meta={}
for view,folder,size,part in [('product','shoe2d',(1024,640),'base'),('fitting','fitting2d',(1024,1024),'shoe')]:
 a=read(SRC/(view+'.png'));r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
 chroma=((r>g+75)&(r>b+75))|((g>b+90)&(r>b+90))
 mask=largest((a[:,:,3]>110)&~chroma);mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8));a[:,:,3]=(blur(mask)*255).clip(0,255).astype('uint8')
 a[:,:,:3]=cv2.inpaint(a[:,:,:3],((a[:,:,3]>0)&chroma).astype('uint8'),3,cv2.INPAINT_TELEA)
 im=Image.fromarray(a)
 if view=='product':
  bounds=im.getchannel('A').point(lambda v:255 if v>127 else 0).getbbox();crop=im.crop(bounds);h=round(crop.height*833/crop.width);crop=crop.resize((833,h),Image.Resampling.LANCZOS);im=Image.new('RGBA',size);im.paste(crop,(96,541-h))
 else:
  im=im.resize(size,Image.Resampling.LANCZOS);a=np.array(im);Y,X=np.indices((1024,1024));yy,xx=np.where((a[:,:,3]>127)&(Y>700));dx=171-int(xx.min());dy=964-int(yy.max());im=Image.fromarray(cv2.warpAffine(a,np.array([[1,0,dx],[0,1,dy]],float),size,flags=cv2.INTER_CUBIC))
 src=np.array(im);rgb=src[:,:,:3];alpha=src[:,:,3].astype(float);Y,X=np.indices(alpha.shape)
 old=read(ROOT/f'assets/{folder}/bowsling_{part}.webp')
 # Product uses the entire genuine mule painting, including its open footbed.
 # Worn front pixels stay exact; only its exposed rear heel comes from the edit.
 mix=np.ones(alpha.shape) if view=='product' else np.clip((X-550)/24,0,1)
 if view=='product':geometry=np.ones(alpha.shape);shell=alpha
 else:
  boundary=np.interp(X,[0,171,220,270,300,350,400,450,500,550,600,650,700,750,780,800,820,1024],[1024,934,888,846,819,824,843,849,845,822,790,748,714,688,671,653,650,650])
  geometry=blur(Y>=boundary);shell=alpha*geometry
 bodyalpha=old[:,:,3]*(1-mix)+shell*mix;bodyrgb=(old[:,:,:3]*(1-mix[:,:,None])+rgb*mix[:,:,None]).clip(0,255)
 bodyalpha[(bodyalpha<3)&(mix>0)]=0;save(folder,part,bodyrgb,bodyalpha)
 if view=='product':
  # Warm cream footbed is never recoloured. Neutral satin sidewall/support is.
  collar=np.interp(X,[0,96,150,200,240,300,350,400,450,500,550,600,650,700,750,800,850,900,928,1024],[540,510,481,449,426,409,421,431,434,435,433,420,396,367,337,307,285,263,252,252])
  bow=Image.new('L',size);ImageDraw.Draw(bow).polygon([(232,410),(238,390),(253,371),(274,349),(299,327),(317,318),(329,319),(343,331),(358,349),(369,369),(375,381),(394,373),(411,374),(417,384),(448,380),(483,381),(515,388),(541,399),(555,407),(548,432),(533,461),(516,491),(530,528),(480,530),(450,532),(424,495),(411,467),(400,437),(398,425),(376,420),(359,414),(342,428),(330,443),(315,461),(299,447),(286,435),(267,430),(248,423),(236,419)],fill=255)
  cloth=(Y>collar)|(np.array(bow)>0)|((X<400)&(Y>400))
 else:cloth=Y>boundary+7
 bottom=np.where(shell>127,Y,-1).max(axis=0);cloth &= Y<bottom[None,:]-6
 newupper=np.minimum(shell,blur(cloth)*255);oldupper=read(ROOT/f'assets/{folder}/bowsling_upper.webp')[:,:,3]
 upper=np.minimum(bodyalpha,oldupper*(1-mix)+newupper*mix);save(folder,'upper',255,upper)
 lum=cv2.GaussianBlur(rgb@np.array([.2126,.7152,.0722]),(0,0),4)
 for effect,col,strength in [('shadow',0,np.clip((242-lum)/155,0,.65)),('highlight',255,np.clip((lum-205)/65,0,.6))]:
  oldeffect=read(ROOT/f'assets/{folder}/bowsling_{effect}.webp')[:,:,3];save(folder,effect,col,np.minimum(bodyalpha,oldeffect*(1-mix)+strength*newupper*mix))
 if view=='product':
  warm=np.maximum(0,shell-newupper)
  for layer,new in [('binding',warm*(cv2.dilate((newupper>100).astype('uint8'),np.ones((5,5),np.uint8))>0)),('insole',warm*(Y<500)),('sole',shell*(Y>=bottom[None,:]-7))]:
   oldlayer=read(ROOT/f'assets/{folder}/bowsling_{layer}.webp')[:,:,3];save(folder,layer,255,np.minimum(bodyalpha,oldlayer*(1-mix)+new*mix))
 else:
  skin=alpha*(1-geometry);skinrgb=cv2.bilateralFilter(rgb,17,35,15).astype('float32');sl=cv2.GaussianBlur(skinrgb@np.array([.2126,.7152,.0722],np.float32),(0,0),6);v=cv2.GaussianBlur(np.round(np.clip((sl-145)/94,0,1)*8)/8,(0,0),5);skinrgb=np.array([219,155,141])[None,None,:]+v[:,:,None]*np.array([36,75,65])[None,None,:]
  # Preserve common calf and accepted forefoot anatomy. Only newly exposed
  # rear heel/instep skin is source-matched from the neutral mule edit.
  oldleg=read(ROOT/'assets/fitting2d/bowsling_legs.webp');newleg=np.dstack([skinrgb,skin]).clip(0,255);legmix=mix*np.clip((Y-400)/80,0,1)
  w0=oldleg[:,:,3]*(1-legmix);w1=newleg[:,:,3]*legmix;den=w0+w1
  legrgb=(oldleg[:,:,:3]*w0[:,:,None]+newleg[:,:,:3]*w1[:,:,None])/np.maximum(den[:,:,None],1e-6);legrgb[:400]=oldleg[:400,:,:3];den[:400]=oldleg[:400,:,3];save(folder,'legs',legrgb,den)
  oldocc=read(ROOT/'assets/fitting2d/bowsling_occlusion.webp')[:,:,3];occ=oldocc*(1-mix)+shell*mix;occ[Y>650]=np.maximum(occ[Y>650],(255-alpha[Y>650])*mix[Y>650]);save(folder,'occlusion',255,occ)
  assert np.array_equal(read(ROOT/'assets/fitting2d/bowmule_legs.webp')[:400],oldleg[:400]),'common calf changed'
 im.save(SRC/(view+'-normalized.png'))
 output=read(ROOT/f'assets/{folder}/bowmule_{part}.webp');unchanged=X<(560 if view=='product' else 550)
 if view=='fitting':assert np.array_equal(output[unchanged],old[unchanged]),'front shoe pixels changed'
 ys,xs=np.where(output[:,:,3]>127)
 meta[view]={'source':view+'.png','frame':list(size),'baseFront':'genuine full mule edit' if view=='product' else 'bowsling','exactForefootThroughX':None if view=='product' else 550,'toeX':int(xs.min()),'groundY':int(ys.max()),'backlessRearFromOriginalEdit':True,'skin':'exact common upper400; source-matched exposed rear heel' if view=='fitting' else None}
(SRC/'export.json').write_text(json.dumps(meta,indent=2)+'\n');(SRC/'anchors.json').write_text(json.dumps(meta,indent=2)+'\n')
sheet=Image.new('RGB',(1440,1100),'#ecfff5');d=ImageDraw.Draw(sheet)
for col,(folder,part) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 for row,bg in enumerate(['#fff4ed','#233c43']):
  im=Image.open(ROOT/f'assets/{folder}/bowmule_{part}.webp').convert('RGBA')
  if col:
   legs=Image.open(ROOT/'assets/fitting2d/bowmule_legs.webp').convert('RGBA');legs.putalpha(ImageChops.subtract(legs.getchannel('A'),Image.open(ROOT/'assets/fitting2d/bowmule_occlusion.webp').getchannel('A')));legs.alpha_composite(im);im=legs
  im.thumbnail((690,510));tile=Image.new('RGB',(720,550),bg);tile.paste(im,((720-im.width)//2,0),im);sheet.paste(tile,(col*720,row*550));d.text((col*720+12,row*550+525),folder+' / genuine backless mule / pinned toe and ground',fill='#f680ae')
sheet.save(SRC/'export-contact.jpg',quality=95)
print(json.dumps(meta,indent=2))
