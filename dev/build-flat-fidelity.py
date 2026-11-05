#!/usr/bin/env python3
"""USER13:27: source-local pointed flat repair from retained genuine edit.

Only toe satin and distal heel are admitted. Collar, calves, ornaments, hosiery
maps and all other source pixels stay exact. Run after legacy flat exporters.
"""
from pathlib import Path
import hashlib,json
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/flat-fidelity-source';OUT=ROOT/'assets/fitting2d';QA=ROOT/'qa/fidelity-1327/flat';QA.mkdir(parents=True,exist_ok=True)
def read(p):return np.array(Image.open(p).convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS))
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
y,x=np.indices((1024,1024));old=read(SRC/'flat_shoe.webp');new=read(SRC/'candidate.png')
# Remove saturated chroma remnants at generated transparent cutout edges.
r,g,b=[new[:,:,i].astype(float) for i in range(3)];new[:,:,3][(g>r+30)|(b>r+50)|(r-g>100)]=0
# A thin outsole retains each original rear ground coordinate; no leg moves.
oldbottom=np.where(old[:,:,3]>140,y,-1).max(axis=0);newbottom=np.where(new[:,:,3]>140,y,-1).max(axis=0)
strength=smooth((x-650)/45)*smooth((y-695)/45)
# Smooth the displacement field before sampling. Per-column integer silhouette
# differences produce a stair-step heel even with cubic image interpolation.
# Ignore empty columns and extend edge values before the Gaussian convolution.
valid=(oldbottom>=0)&(newbottom>=0)
displacement=np.interp(np.arange(1024),np.flatnonzero(valid),(oldbottom-newbottom)[valid]).astype('float32')
displacement=cv2.GaussianBlur(displacement[None,:],(0,0),7)[0]
delta=displacement[None,:]*strength
mapy=(y-delta).astype('float32');mapx=x.astype('float32')
new=cv2.remap(new,mapx,mapy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
# Fully replace leading toe; feather only within continuous satin, away from
# its cream collar. Point extends 22px into existing transparent source space.
toe=(1-smooth((x-280)/110))*smooth((y-835)/45)
heel=smooth((x-650)/40)*smooth((y-700)/35)
report={'styles':{},'method':'genuine gpt-image-2 edit, original source-local blend','protected':'all calves, original collar, accessories, contact anchors and framing'}
for style in ['flat','maryjane','ballet']:
 # Only the product flat has a pointed last. Earned Mary Jane and ballet
 # cameras retain their accepted almond toe, while sharing the low heel.
 w=np.maximum(toe if style=='flat' else np.zeros_like(toe),heel)[:,:,None]
 original=read(SRC/f'{style}_shoe.webp');shoe=np.rint(original*(1-w)+new*w).clip(0,255).astype('uint8')
 # Premultiplied blending prevents dark semi-transparent matte seams.
 aa=original[:,:,3:4]/255;ba=new[:,:,3:4]/255;alpha=aa*(1-w)+ba*w
 rgb=np.divide(original[:,:,:3]*aa*(1-w)+new[:,:,:3]*ba*w,alpha,out=original[:,:,:3].astype(float),where=alpha>0)
 shoe[:,:,:3]=np.rint(rgb).clip(0,255);shoe[:,:,3]=np.rint(alpha[:,:,0]*255)
 # Explicit sole semantics: last six source pixels remain neutral tan.
 bottom=np.where(shoe[:,:,3]>100,y,-1).max(axis=0)
 cloth=(shoe[:,:,3].astype(float)*((y<bottom[None,:]-6)&(shoe[:,:,0].astype(float)-shoe[:,:,2]<68)))
 lum=shoe[:,:,:3]@np.array([.2126,.7152,.0722])
 for part in ['shoe','upper','shadow','highlight','occlusion']:
  base=read(SRC/f'{style}_{part}.webp')
  if part=='shoe':result=shoe
  else:
   result=base.copy()
   if part=='occlusion':a=np.maximum(base[:,:,3],shoe[:,:,3])
   else:
    target=cloth
    if part=='shadow':target=cloth*np.clip((235-lum)/110,0,.65)
    if part=='highlight':target=cloth*np.clip((lum-190)/65,0,.8)
    a=base[:,:,3]*(1-w[:,:,0])+target*w[:,:,0]
   result[:,:,3]=np.rint(a).clip(0,255)
   # Newly admitted pointed-toe pixels were transparent in the old masks;
   # their stored RGB can be black. Giving those pixels highlight alpha
   # without white RGB paints dark rectangular flecks into the satin.
   if part=='highlight':result[:,:,:3][(w[:,:,0]>0)&(result[:,:,3]>0)]=255
  Image.fromarray(result).save(OUT/f'{style}_{part}.webp',lossless=True,exact=True)
  if part!='occlusion':assert np.array_equal(result[w[:,:,0]==0],base[w[:,:,0]==0]),(style,part,'protected pixels changed')
 assert (OUT/f'{style}_legs.webp').read_bytes()==(SRC/f'{style}_legs.webp').read_bytes()
 assert (OUT/f'{style}_hosiery.webp').read_bytes()==(SRC/f'{style}_hosiery.webp').read_bytes()
 report['styles'][style]={'changedShoePixels':int(np.any(shoe!=original,axis=2).sum()),'legsAndHosieryExact':True,'toeClass':'pointed' if style=='flat' else 'almond','soleClass':'thin tan / low heel','sha256':hashlib.sha256((OUT/f'{style}_shoe.webp').read_bytes()).hexdigest()}
 bg=Image.new('RGBA',(2048,1024),'#e4f0e8')
 for i,im in enumerate([original,shoe]):bg.alpha_composite(Image.fromarray(im),(i*1024,0))
 bg.crop((150,475,1870,1000)).save(QA/f'{style}-before-after.png')
(QA/'source-report.json').write_text(json.dumps(report,indent=2)+'\n')
(SRC/'provenance.json').write_text(json.dumps({'model':'gpt-image-2','workflow':'built-in returned no artifact; existing REVIEW API edit workflow via bundled imagegen CLI','prompt':'prompt.txt','inputs':['edit-input.png','design-reference.png'],'originalLayers':'<style>_<part>.webp','output':'candidate.png','integration':'dev/build-flat-fidelity.py'},indent=2)+'\n')
print(json.dumps(report))
