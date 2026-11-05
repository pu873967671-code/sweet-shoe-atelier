#!/usr/bin/env python3
"""Export genuine neutral ankle-bow reference edits to immutable camera kits."""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageChops
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/dorsay-source'
def read(p):return np.array(Image.open(p).convert('RGBA'))
def soft(a,s=.55):return cv2.GaussianBlur(a.astype('float32'),(0,0),s)
def poly(points,size):
 im=Image.new('L',size);ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)
def clean(im):
 a=np.array(im.convert('RGBA'));rgb=a[:,:,:3];r,g,b=rgb.astype(float).transpose(2,0,1)
 bad=((r>g+65)&(r>b+65))|((g>b+75)&(r>b+75))
 m=(a[:,:,3]>110)&~bad;n,l,st,_=cv2.connectedComponentsWithStats(m.astype('uint8'),8);m=(l==1+np.argmax(st[1:,cv2.CC_STAT_AREA])).astype('uint8')
 m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8));alpha=soft(m)*255;alpha[alpha<3]=0
 rgb=cv2.inpaint(rgb,((alpha>0)&bad).astype('uint8'),3,cv2.INPAINT_TELEA)
 return Image.fromarray(np.dstack([rgb,alpha.clip(0,255).astype('uint8')]))
def save(folder,part,rgb,alpha):
 out=np.zeros((*alpha.shape,4),np.uint8);out[:,:,:3]=rgb;out[:,:,3]=alpha.clip(0,255).astype('uint8');Image.fromarray(out).save(SRC/f'runtime-candidate/{folder}/dorsay_{part}.webp',lossless=True,method=6,exact=True)
for folder in ['shoe2d','fitting2d']:(SRC/'runtime-candidate'/folder).mkdir(parents=True,exist_ok=True)
meta={}
for view,folder,size,part in [('product','shoe2d',(1024,640),'base'),('fitting','fitting2d',(1024,1024),'shoe')]:
 im=clean(Image.open(SRC/f'{view}.png'))
 if view=='product':
  a=np.array(im);ys,xs=np.where(a[:,:,3]>127);s=832/(xs.max()-xs.min());new=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS);out=Image.new('RGBA',size);out.paste(new,(96-round(xs.min()*s),540-round(ys.max()*s)));im=out
 else:
  im=im.resize(size,Image.Resampling.LANCZOS);a=np.array(im);Y,X=np.indices(a.shape[:2]);ys,xs=np.where((a[:,:,3]>127)&(Y>700));dx=171-int(xs.min());dy=964-int(ys.max());im=Image.fromarray(cv2.warpAffine(a,np.array([[1,0,dx],[0,1,dy]],float),size,flags=cv2.INTER_CUBIC))
 im.save(SRC/f'{view}-normalized.png');a=np.array(im);rgb=a[:,:,:3];alpha=a[:,:,3].astype(float);Y,X=np.indices(alpha.shape)
 if view=='product':
  xs=[0,96,150,200,250,300,330,350,400,450,500,550,600,650,700,750,780,800,810,820,830,840,850,870,900,925,1024]
  yy=[540,510,480,451,425,402,396,405,417,429,439,441,431,399,348,301,271,241,198,144,100,80,80,80,100,160,160]
  boundary=np.interp(X,xs,yy)
  bow=poly([(791,40),(800,18),(818,12),(835,31),(840,34),(855,18),(882,5),(906,12),(909,43),(878,58),(892,74),(928,117),(899,105),(875,89),(870,120),(857,147),(841,139),(834,107),(828,72),(810,73),(800,59)],size)
  band=poly([(638,49),(670,51),(730,53),(790,50),(806,54),(790,76),(738,75),(691,75),(638,69)],size)
  cloth=(Y>boundary)|(bow>0)|(band>0)|(X<330);shell=alpha
 else:
  xs=[0,171,220,270,300,320,335,350,400,450,500,550,580,600,625,650,675,700,720,735,745,755,770,790,810,830,850,1024]
  yy=[1024,934,888,846,817,800,799,814,837,850,855,849,837,820,785,739,702,671,624,567,505,450,426,449,485,526,550,550]
  boundary=np.interp(X,xs,yy)
  bow=poly([(628,390),(636,382),(654,382),(671,385),(686,378),(706,367),(727,361),(742,367),(748,386),(728,399),(710,402),(740,425),(752,446),(728,439),(697,418),(688,447),(675,472),(658,459),(660,429),(669,407),(648,415),(637,408)],size)
  band=poly([(509,373),(530,383),(567,388),(605,390),(638,390),(648,411),(615,414),(572,411),(532,404),(505,394)],size)
  ribbons=(bow>0)|(band>0);geometry=np.maximum(soft((Y>=boundary)|((X<330)&(Y>700))),soft(ribbons));shell=alpha*geometry;cloth=(Y>boundary+6)|ribbons|(X<330)
 bottom=np.where(shell>127,Y,-1).max(axis=0);cloth &= (Y<bottom[None,:]-6)|((bow>0)|(band>0))
 r,g,b=rgb.astype(float).transpose(2,0,1)
 # Neutral satin is separated from warm cream lining and peach skin by its
 # source chroma, then closed/smoothed into a continuous camera-local mask.
 # This avoids staircase corners at the rising back collar.
 neutral=((r-b)<58)&((r-g)<36)&(abs(g-b)<40)&(r>85)
 neutral=cv2.morphologyEx(neutral.astype('uint8'),cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
 if view=='product':
  # Keep the entire warm footbed and band lining outside the finish.
  continuous=cv2.GaussianBlur(boundary.astype('float32'),(0,0),3)
  cloth=(Y>continuous)|(bow>0)|(band>0)|(X<330)
  neutral=neutral*cloth
 upper=np.minimum(shell,soft(neutral,.85)*255)
 upper[Y>=bottom[None,:]-5]=0;save(folder,part,rgb,shell);save(folder,'upper',255,upper)
 lum=cv2.GaussianBlur(rgb@np.array([.2126,.7152,.0722]),(0,0),4)
 save(folder,'shadow',0,np.clip((242-lum)/155,0,.65)*upper);save(folder,'highlight',255,np.clip((lum-205)/65,0,.6)*upper)
 if view=='product':
  warm=np.maximum(0,shell-upper);save(folder,'binding',255,warm*(abs(Y-boundary)<7));save(folder,'insole',255,warm*(Y<boundary));save(folder,'sole',255,shell*(Y>=bottom[None,:]-7))
 else:
  skin=alpha*(1-geometry);srgb=cv2.bilateralFilter(rgb,17,35,15).astype('float32');sl=soft(srgb@np.array([.2126,.7152,.0722],np.float32),6);v=soft(np.round(np.clip((sl-145)/94,0,1)*8)/8,5);srgb=np.array([219,155,141])[None,None,:]+v[:,:,None]*np.array([36,75,65])[None,None,:]
  # Accepted calf is exact above400; below it follows the genuine worn edit.
  common=read(ROOT/'assets/fitting2d/stiletto6_legs.webp');newleg=np.dstack([srgb,skin]).clip(0,255).astype('uint8');mix=np.clip((Y-400)/80,0,1)[:,:,None];w0=common[:,:,3:4]*(1-mix);w1=newleg[:,:,3:4]*mix;den=w0+w1;legrgb=(common[:,:,:3]*w0+newleg[:,:,:3]*w1)/np.maximum(den,1e-6);legrgb[:400]=common[:400,:,:3];den[:400]=common[:400,:,3:4];save(folder,'legs',legrgb,den[:,:,0])
  occ=shell.copy();occ[Y>650]=np.maximum(occ[Y>650],255-alpha[Y>650]);save(folder,'occlusion',255,occ)
  assert np.array_equal(read(ROOT/'assets/fitting2d/dorsay_legs.webp')[:400],common[:400])
 ys,x=np.where(shell>127);meta[view]={'source':view+'.png','frame':list(size),'toeX':int(x.min()),'groundY':int(ys.max()),'genuineAnkleBow':True,'sideOpening':'lowered curved quarter, not a deep side cutout','upper400CalfExact':view=='fitting'}
(SRC/'export.json').write_text(json.dumps(meta,indent=2)+'\n');(SRC/'anchors.json').write_text(json.dumps(meta,indent=2)+'\n')
sheet=Image.new('RGB',(1440,1100),'#eafff5');d=ImageDraw.Draw(sheet)
for col,(folder,part) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 for row,bg in enumerate(['#fff4ed','#233c43']):
  im=Image.open(SRC/f'runtime-candidate/{folder}/dorsay_{part}.webp').convert('RGBA')
  if col:
   leg=Image.open(ROOT/'assets/fitting2d/dorsay_legs.webp').convert('RGBA');leg.putalpha(ImageChops.subtract(leg.getchannel('A'),Image.open(ROOT/'assets/fitting2d/dorsay_occlusion.webp').getchannel('A')));leg.alpha_composite(im);im=leg
  im.thumbnail((690,510));tile=Image.new('RGB',(720,550),bg);tile.paste(im,((720-im.width)//2,0),im);sheet.paste(tile,(col*720,row*550));d.text((col*720+10,row*550+525),folder+' / original ankle-bow pump / genuine edit',fill='#f679a6')
sheet.save(SRC/'export-contact.jpg',quality=95)
print(json.dumps(meta,indent=2))
