#!/usr/bin/env python3
"""Genuine edited 6/9cm paintings; fixed frames and per-height perspective mounts."""
from pathlib import Path
import json
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/thin-heels-source'
def read(p):return np.array(Image.open(p).convert('RGBA'))
def blur(a,s=.6):return cv2.GaussianBlur(a.astype('float32'),(0,0),s)
def cleaned(a):
 rgb=a[:,:,:3].copy();r,g,b=rgb.astype(float).transpose(2,0,1);alpha=a[:,:,3].copy()
 # Only neutral/peach artwork is valid: remove inherited red/yellow chroma matte.
 bad=((r>g+90)&(r>b+80))|((g>b+100)&(r>b+100))
 alpha[bad]=0
 silhouette=cv2.morphologyEx((alpha>110).astype('uint8'),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8));alpha=blur(silhouette)*255;alpha[alpha<3]=0
 rgb=cv2.inpaint(rgb,((alpha>0)&(a[:,:,3]<120)|bad).astype('uint8'),3,cv2.INPAINT_TELEA)
 return rgb,alpha
anchors={};meta={}
for height in (6,9):
 heel='stiletto'+str(height);anchors[heel]={}
 for view,folder,size,basepart in [('product','shoe2d',(1024,640),'base'),('fitting','fitting2d',(1024,1024),'shoe')]:
  im=Image.open(SRC/f'{view}-{height}.png').convert('RGBA')
  if view=='product':
   a=np.array(im)[:,:,3];ys,xs=np.where(a>127);im=im.crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))).resize((833,490),Image.Resampling.LANCZOS);out=Image.new('RGBA',size);out.paste(im,(96,51));im=out
  else:
   im=im.resize(size,Image.Resampling.LANCZOS);a=np.array(im);Y,X=np.indices((1024,1024));ys,xs=np.where((a[:,:,3]>127)&(Y>450));dx=int(171-xs.min());dy=int(964-ys.max());dx+=0 if height==6 else 1;dy+=0 if height==6 else -1;im=Image.fromarray(cv2.warpAffine(a,np.array([[1,0,dx],[0,1,dy]],float),size,flags=cv2.INTER_CUBIC))
  a=np.array(im);rgb,alpha=cleaned(a);Y,X=np.indices(alpha.shape)
  if view=='product':
   # Authored opening boundary retains the warm insole and stitched roll.
   xx=[0,96,200,300,330,350,400,450,500,550,600,650,700,750,800,835,850,875,928,1024]
   yy=([540,505,455,408,405,412,425,435,442,443,433,404,349,278,192,112,76,102,190,190] if height==6 else [540,510,468,417,410,416,429,441,449,448,435,402,345,268,178,99,76,102,190,190])
   boundary=np.interp(X,xx,yy);shell=alpha;cloth=Y>boundary
  else:
   xx=[0,171,220,270,300,320,335,350,400,450,500,550,580,600,625,650,675,700,725,750,760,790,820,850,1024]
   yy=([1024,934,888,846,817,800,799,814,837,850,855,847,826,800,748,686,630,574,514,455,417,445,498,550,550] if height==6 else [1024,935,889,846,818,798,801,816,838,851,855,848,829,795,733,669,610,555,492,429,411,451,520,550,550])
   boundary=np.interp(X,xx,yy);geometry=blur((Y>=boundary)|(X<330));shell=alpha*geometry;cloth=(Y>boundary+6)|(X<330)
  # Trim neutral outsole only; complete slender supports take the finish.
  bottom=np.where(shell>127,Y,-1).max(axis=0);cloth &= Y<bottom[None,:]-6
  upper=np.minimum(shell,blur(cloth)*255);shell[shell<3]=0;upper[upper<3]=0
  def save(part,rgb1,alpha1):
   out=np.zeros((*alpha1.shape,4),np.uint8);out[:,:,:3]=rgb1;out[:,:,3]=np.clip(alpha1,0,255).astype('uint8');Image.fromarray(out).save(ROOT/f'assets/{folder}/{heel}_{part}.webp',lossless=True)
  save(basepart,rgb,shell);save('upper',255,upper)
  lum=cv2.GaussianBlur(rgb@np.array([.2126,.7152,.0722]),(0,0),4);save('shadow',0,np.clip((242-lum)/155,0,.65)*upper);save('highlight',255,np.clip((lum-205)/65,0,.6)*upper)
  if view=='product':
   warm=np.maximum(0,shell-upper);save('insole',255,warm*(Y<boundary));save('sole',255,shell*(Y>=bottom[None,:]-7));save('binding',255,warm*(np.abs(Y-boundary)<7))
  else:
   skin=alpha*(1-geometry);srgb=cv2.bilateralFilter(rgb,17,35,15).astype('float32');sl=blur(srgb@np.array([.2126,.7152,.0722],np.float32),6);v=blur(np.round(np.clip((sl-145)/94,0,1)*8)/8,5);srgb=np.array([219,155,141])[None,None,:]+v[:,:,None]*np.array([36,75,65])[None,None,:]
   newleg=np.dstack([srgb,skin]).clip(0,255).astype('uint8');common=read(ROOT/'assets/fitting2d/kitten_legs.webp')
   # Interpolate calf contours, rather than dissolve two offset silhouettes:
   # dissolving creates a translucent flap where the two calf edges differ.
   mapx=X.astype('float32').copy();mapy=Y.astype('float32')
   for row in range(400,501):
    c=np.flatnonzero(common[row,:,3]>127);n=np.flatnonzero(newleg[row,:,3]>127)
    if len(c) and len(n):
     t=(row-400)/100;left=c[0]*(1-t)+n[0]*t;rt=min(1,(row-400)/17);right=c[-1]*(1-rt)+n[-1]*rt
     mapx[row]=n[0]+(np.arange(1024)-left)*(n[-1]-n[0])/max(1,right-left)
   newleg=cv2.remap(newleg,mapx,mapy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
   mix=np.clip((Y-400)/100,0,1)[:,:,None];weight0=common[:,:,3:4]/255*(1-mix);weight1=newleg[:,:,3:4]/255*mix;den=weight0+weight1;leg=np.dstack([((common[:,:,:3]*weight0+newleg[:,:,:3]*weight1)/np.maximum(den,1e-6)).clip(0,255),(den[:,:,0]*255).clip(0,255)]).astype('uint8');leg[400:501,:,3]=newleg[400:501,:,3];leg[:400]=common[:400];save('legs',leg[:,:,:3],leg[:,:,3]);occ=shell.copy();occ[Y>650]=np.maximum(occ[Y>650],255-alpha[Y>650]);save('occlusion',255,occ)
  # One immutable transform for sprite RGB and tint alpha. Three camera-local
  # zones keep the toe, instep and counter mounts seated on their new surfaces.
  for path in (ROOT/f'assets/{folder}/accessories').glob('kitten_*.webp'):
   src=read(path);hh,ww=src.shape[:2];oy,ox=np.indices((hh,ww),dtype='float32')
   if view=='product':
    delta=np.interp(ox,[0,285,594,855,1024],[15,15 if height==6 else 20,14,-8 if height==6 else -2,0]);mx=ox;my=oy-delta
   else:
    delta=np.interp(ox,[0,300,450,600,750,1024],[0,-3,-16,-45 if height==6 else -58,-88 if height==6 else -100,-88]);mx=ox;my=oy-delta
   mapped=cv2.remap(src,mx.astype('float32'),my.astype('float32'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT);Image.fromarray(mapped).save(path.with_name(path.name.replace('kitten_',heel+'_')),lossless=True)
  ys,xs=np.where(shell>127);bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  anchors[heel][view]={'frame':list(size),'toe':[96,540] if view=='product' else [171,964],'groundY':540 if view=='product' else 964,'bbox':bbox,'counter':[855,205 if height==6 else 195] if view=='product' else [770,500],'vamp':[285,460 if height==6 else 465] if view=='product' else [350,865],'strap':[594,332] if view=='product' else [590,710],'ornamentWarp':'per-column source-coordinate translation; see builder; identical RGB/tint mapping'}
  Image.fromarray(np.dstack([rgb,alpha]).astype('uint8')).save(SRC/f'{view}-{height}-normalized.png')
  meta[heel+'_'+view]={'bbox':bbox,'upperPixels':int((upper>127).sum()),'source':f'{view}-{height}.png'}
(SRC/'anchors.json').write_text(json.dumps(anchors,indent=2));(SRC/'export.json').write_text(json.dumps(meta,indent=2))
# Product counter polish is part of the deterministic source rebuild.
import runpy
runpy.run_path(str(ROOT/'dev/fitting-polish/clean-thin-counter.py'),run_name='__main__')
sheet=Image.new('RGB',(1600,1100),'#e2f8ed');d=ImageDraw.Draw(sheet)
for col,h in enumerate((6,9)):
 heel='stiletto'+str(h)
 for row,bg in enumerate(('#fdf2e7','#273e40')):
  product=Image.open(ROOT/f'assets/shoe2d/{heel}_base.webp').convert('RGBA');product.thumbnail((500,310));tile=Image.new('RGB',(800,550),bg);tile.paste(product,(0,10),product)
  leg=Image.open(ROOT/f'assets/fitting2d/{heel}_legs.webp').convert('RGBA');leg.alpha_composite(Image.open(ROOT/f'assets/fitting2d/{heel}_shoe.webp').convert('RGBA'));leg.thumbnail((390,520));tile.paste(leg,(410,10),leg);sheet.paste(tile,(col*800,row*550));d.text((col*800+10,row*550+530),str(h)+'cm product + worn neutral',fill='#ff77aa')
sheet.save(SRC/'export-contact.jpg',quality=94)
print(json.dumps(meta,indent=2))
