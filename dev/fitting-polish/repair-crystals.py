#!/usr/bin/env python3
"""Restore crystal facets from the original reviewed image-edit paintings.

The previous jewellery key removed purple gemstone interiors along with lilac
shoe residue; kitten fitting also retained distant piping fragments. This final
export pass uses a tight authored jewel aperture and a gold-bezel convex hull.
All visible RGB comes from the original gpt-image-2 edits; no new art is claimed.
Run after accessory extraction/residue cleanup, and after platform export.
Only *_charm_crystal.webp and worn *_charm_pearl.webp files are written. Body/skin and other ornaments stay exact.
"""
import io,json,subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'qa/crystal-repair';OUT.mkdir(exist_ok=True)
cv2.setNumThreads(1)
HEELS=['flat','kitten','block','wedge']
CENTERS={'product':{'flat':(298,413,51,31),'kitten':(320,417,51,37),'block':(298,423,52,35),'wedge':(292,384,55,43)},'fitting':{'flat':(278,848,25,23),'kitten':(302,832,24,24),'block':(252,865,25,22),'wedge':(304,842,21,20)}}
warps={x['name']:x['warp'] for x in json.loads((ROOT/'dev/accessory-edits/extraction-report.json').read_text())['layers']}
def original_before(path):
 try:
  raw=subprocess.check_output(['git','show','e7de245:'+str(path.relative_to(ROOT))],cwd=ROOT,stderr=subprocess.DEVNULL)
  return Image.open(io.BytesIO(raw)).convert('RGBA')
 except (subprocess.CalledProcessError,FileNotFoundError):return Image.open(path).convert('RGBA')
records=[];before={}
for view,folder,size in [('product','shoe2d',(1024,640)),('fitting','fitting2d',(1024,1024))]:
 for h in HEELS:
  dest=ROOT/f'assets/{folder}/accessories/{h}_charm_crystal.webp';before[(view,h)]=original_before(dest)
  src=ROOT/(f'dev/accessory-edits/{h}_charm_crystal.png' if view=='product' else f'dev/fitting-accessories/{h}-bow.png')
  arr=np.array(Image.open(src).convert('RGBA').resize(size,Image.Resampling.LANCZOS))
  if view=='product':arr=cv2.warpAffine(arr,np.array(warps[h+'_charm_crystal'],np.float32),size,flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT)
  rgb=arr[:,:,:3].astype(float);r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
  cx,cy,rx,ry=CENTERS[view][h];local=np.zeros(arr.shape[:2],np.uint8);cv2.ellipse(local,(cx,cy),(rx,ry),0,0,360,1,-1)
  # Strong gold differs from the cream/lilac upper; the hull closes its bezel
  # around the original clear/lilac facets without carrying the shoe painting.
  seed=((r-b>45)&(r-g>25)&(r>115)&(local>0)&(arr[:,:,3]>0)).astype('uint8')
  pts=cv2.findNonZero(seed);assert pts is not None,(view,h)
  keep=np.zeros_like(local);cv2.fillConvexPoly(keep,cv2.convexHull(pts),1)
  keep &=local
  # Inward antialiasing prevents any new matte or outward pale contour.
  alpha=np.clip(cv2.distanceTransform(keep,cv2.DIST_L2,5)/1.2,0,1)*arr[:,:,3]
  arr[:,:,3]=alpha.astype('uint8');im=Image.fromarray(arr);im.save(dest,lossless=True)
  records.append({'view':view,'heel':h,'source':str(src.relative_to(ROOT)),'aperture':[cx,cy,rx,ry],'bounds':im.getbbox(),'visible_pixels':int((alpha>0).sum())})
 # Preserve the accepted source-coordinate transform for this derivative.
 path=ROOT/f'assets/{folder}/accessories/platform_charm_crystal.webp';before[(view,'platform')]=original_before(path)
 a=np.array(Image.open(ROOT/f'assets/{folder}/accessories/block_charm_crystal.webp').convert('RGBA'));yy,xx=np.indices(a.shape[:2],dtype='float32')
 if view=='product':mapy=yy+52*(1-np.clip((xx-300)/550,0,1));mapx=xx
 else:mapy=yy+40;mapx=xx-5
 mapped=cv2.remap(a,mapx.astype('float32'),mapy.astype('float32'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
 Image.fromarray(mapped).save(path,lossless=True)
# Pearl cores were also removed by the strict changed-pixel key. Re-extract
# their complete original painted bezel/core within compact authored apertures.
pearl_before={};pearl_centers={'flat':(281,858),'kitten':(300,850),'block':(288,860),'wedge':(228,894)}
for h in HEELS:
 dest=ROOT/f'assets/fitting2d/accessories/{h}_charm_pearl.webp';pearl_before[h]=original_before(dest)
 src=ROOT/f'dev/fitting-accessories/{h}-pearl.png'
 arr=np.array(Image.open(src).convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS));rgb=arr[:,:,:3].astype(float);r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
 cx,cy=pearl_centers[h];local=np.zeros(arr.shape[:2],np.uint8);cv2.ellipse(local,(cx,cy),(23,24),0,0,360,1,-1)
 seed=((r-b>40)&(r-g>22)&(r>110)&(local>0)&(arr[:,:,3]>0)).astype('uint8');pts=cv2.findNonZero(seed);assert pts is not None,('pearl',h)
 keep=np.zeros_like(local);cv2.fillConvexPoly(keep,cv2.convexHull(pts),1);keep &=local
 alpha=np.clip(cv2.distanceTransform(keep,cv2.DIST_L2,5)/1.2,0,1)*arr[:,:,3];arr[:,:,3]=alpha.astype('uint8');im=Image.fromarray(arr);im.save(dest,lossless=True)
 records.append({'view':'fitting','heel':h,'ornament':'pearl','source':str(src.relative_to(ROOT)),'aperture':[cx,cy,23,24],'bounds':im.getbbox(),'visible_pixels':int((alpha>0).sum())})
path=ROOT/'assets/fitting2d/accessories/platform_charm_pearl.webp';pearl_before['platform']=original_before(path)
a=np.array(Image.open(ROOT/'assets/fitting2d/accessories/block_charm_pearl.webp').convert('RGBA'));yy,xx=np.indices(a.shape[:2],dtype='float32');mapped=cv2.remap(a,xx-5,yy+40,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT);Image.fromarray(mapped).save(path,lossless=True)
ps=Image.new('RGB',(1500,500),'#f3fff8');pd=ImageDraw.Draw(ps)
for col,h in enumerate(HEELS+['platform']):
 old=pearl_before[h];new=Image.open(ROOT/f'assets/fitting2d/accessories/{h}_charm_pearl.webp').convert('RGBA');bb=new.getbbox();box=(bb[0]-8,bb[1]-8,bb[2]+8,bb[3]+8)
 for row,bg in enumerate(['#f3fff8','#243d3a']):
  for side,im in enumerate([old,new]):
   patch=Image.new('RGBA',im.size,bg);patch.alpha_composite(im);patch=patch.crop(box).resize((140,170));x,y=col*300+side*150,row*240+30;ps.paste(patch.convert('RGB'),(x,y));pd.text((x+3,y-20),h+(' before' if side==0 else ' restored'),fill='#244f41')
ps.save(OUT/'pearls-before-after.jpg',quality=95)
# Original and repaired native pixels side by side, on both matte colours.
sheet=Image.new('RGB',(1500,1000),'#f3fff8');d=ImageDraw.Draw(sheet)
for row,view in enumerate(['product','fitting']):
 folder='shoe2d' if view=='product' else 'fitting2d'
 for col,h in enumerate(HEELS+['platform']):
  old=before[(view,h)];new=Image.open(ROOT/f'assets/{folder}/accessories/{h}_charm_crystal.webp').convert('RGBA');bb=new.getbbox();box=(bb[0]-9,bb[1]-9,bb[2]+9,bb[3]+9)
  for bgrow,bg in enumerate(['#f3fff8','#243d3a']):
   for side,im in enumerate([old,new]):
    p=Image.new('RGBA',im.size,bg);p.alpha_composite(im);p=p.crop(box);p.thumbnail((140,185));x,y=col*300+side*150,row*500+bgrow*240+30;sheet.paste(p.convert('RGB'),(x,y));d.text((x+3,y-20),h+(' before' if side==0 else ' restored'),fill='#244f41')
sheet.save(OUT/'before-after.jpg',quality=95)
(OUT/'report.json').write_text(json.dumps({'source':'Original gpt-image-2 edits; deterministic mask repair only','records':records},indent=2))
print(json.dumps(records))
