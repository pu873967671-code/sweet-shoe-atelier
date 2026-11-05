#!/usr/bin/env python3
"""Extract local gpt-image-2 worn-view edits; never alter neutral shoe/skin pixels.
Run after source edits arrive: python3 dev/build-fitting-accessories.py.
"""
from pathlib import Path
import cv2,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/fitting-accessories';OUT=ROOT/'assets/fitting2d/accessories';OUT.mkdir(exist_ok=True)
SIZE=1024;cv2.setNumThreads(1)
ROIS={
 'decoration':(700,380,890,690),
 'strap':(360,570,780,880),
 'charm':(180,790,450,960),
}
def extract(h,variant,category):
 original=np.array(Image.open(ROOT/f'dev/fitting-source/{h}.png').convert('RGBA').resize((SIZE,SIZE),Image.Resampling.LANCZOS))
 edit=np.array(Image.open(SRC/f'{h}-{variant}.png').convert('RGBA').resize((SIZE,SIZE),Image.Resampling.LANCZOS))
 # Translation registration uses untouched skin above every shoe/accessory.
 a=original[:,:,:3].astype('float32');b=edit[:,:,:3].astype('float32');warp=np.eye(2,3,dtype='float32');focus=np.zeros((SIZE,SIZE),np.uint8);focus[40:420,430:850]=255
 try:
  raise cv2.error('fixed source frame')
  cv2.findTransformECC(cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)/255,cv2.cvtColor(b,cv2.COLOR_RGB2GRAY)/255,warp,cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_COUNT|cv2.TERM_CRITERIA_EPS,50,1e-5),focus,3)
  if np.max(np.abs(warp[:,2]))<15:edit=cv2.warpAffine(edit,warp,(SIZE,SIZE),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
 except cv2.error:pass
 b=edit[:,:,:3].astype('float32');r,g,bl=b[:,:,0],b[:,:,1],b[:,:,2];delta=np.max(np.abs(a-b),axis=2);rgb=b.copy()
 roi=np.zeros((SIZE,SIZE),np.uint8);x0,y0,x1,y1=ROIS[category];roi[y0:y1,x0:x1]=1
 fabric=((category=='strap' and variant!='pearl') or (category=='decoration' and variant=='bow') or (category=='charm' and variant=='ribbon'))
 lilac=(bl-g>5)&(r-g>2)&(g<245)
 if fabric:
  seed=lilac&(delta>19)&(roi>0)&(edit[:,:,3]>0)
  seed=cv2.morphologyEx(seed.astype('uint8'),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
  count,parts,stats,_=cv2.connectedComponentsWithStats(seed,8);keep=np.zeros_like(seed)
  for i in range(1,count):
   area=stats[i,cv2.CC_STAT_AREA];w=stats[i,cv2.CC_STAT_WIDTH];hh=stats[i,cv2.CC_STAT_HEIGHT]
   if area<90 or w*hh>(x1-x0)*(y1-y0)*.75:continue
   keep[parts==i]=1
 elif category=='charm':
  centers={'bow':{'flat':(277,834),'kitten':(300,830),'block':(259,865),'wedge':(306,844)},'pearl':{'flat':(281,858),'kitten':(300,844),'block':(288,866),'wedge':(228,894)}}
  cx,cy=centers[variant][h];local=np.zeros_like(roi);cv2.ellipse(local,(cx,cy),(28,26),-20,0,360,1,-1)
  warm=(r-bl>8)&(r-g>0)&(r>100)
  keep=(warm&(local>0)).astype('uint8');keep=cv2.morphologyEx(keep,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8));keep &= local
  contours,_=cv2.findContours(keep,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(keep,contours,-1,1,cv2.FILLED)
 elif category=='strap':
  # Neutral spherical bead cores, then include only their nearby gold rims.
  neutral=(np.min(b,axis=2)>180)&(np.ptp(b,axis=2)<48)
  seed=(neutral&(delta>24)&(roi>0)).astype('uint8')
  count,parts,stats,_=cv2.connectedComponentsWithStats(seed,8);keep=np.zeros_like(seed)
  for i in range(1,count):
   area=stats[i,cv2.CC_STAT_AREA];w=stats[i,cv2.CC_STAT_WIDTH];hh=stats[i,cv2.CC_STAT_HEIGHT]
   if 12<area<1900 and 3<w<49 and 3<hh<49:keep[parts==i]=1
  keep=cv2.dilate(keep,np.ones((7,7),np.uint8));keep &= roi
  contours,_=cv2.findContours(keep,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(keep,contours,-1,1,cv2.FILLED)
 else:
  warm=(r-bl>18)&(r-g>5)&(r>100)
  neutral=(np.min(b,axis=2)>170)&(np.ptp(b,axis=2)<42)
  local=np.zeros_like(roi)
  if variant=='pearl':cv2.ellipse(local,(790,560 if h=='wedge' else 575),(65,75),-25,0,360,1,-1)
  else:cv2.ellipse(local,(790,590),(45,110),-25,0,360,1,-1)
  seed=((warm|neutral)&(delta>25)&(roi>0)&(local>0)).astype('uint8')
  seed=cv2.morphologyEx(seed,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
  count,parts,stats,_=cv2.connectedComponentsWithStats(seed,8);keep=np.zeros_like(seed)
  for i in range(1,count):
   if stats[i,cv2.CC_STAT_AREA]>30:keep[parts==i]=1
  contours,_=cv2.findContours(keep,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(keep,contours,-1,1,cv2.FILLED)
 # Strict changed-pixel alpha precludes source painting rectangles.
 keep=(keep>0)&((delta>9) if fabric else True)&(roi>0)
 alpha=np.clip(cv2.distanceTransform(keep.astype('uint8'),cv2.DIST_L2,5)/1.15,0,1)*edit[:,:,3]
 if fabric:
  lum=rgb@np.array([.2126,.7152,.0722]);rgb=np.repeat(np.clip(lum*1.1,0,255)[:,:,None],3,axis=2)
 out=np.zeros((SIZE,SIZE,4),np.uint8);out[:,:,:3]=rgb.clip(0,255).astype('uint8');out[:,:,3]=alpha.clip(0,255).astype('uint8')
 mask=out.copy();mask[:,:,:3]=255;mask[:,:,3]=(alpha*lilac).astype('uint8') if fabric else 0
 return Image.fromarray(out),Image.fromarray(mask),{'pixels':int(np.count_nonzero(alpha)),'alpha_bounds':Image.fromarray(out).getbbox(),'alignment':warp.tolist(),'unchanged_alpha_pixels':int(np.count_nonzero((delta<=9)&(alpha>0)))}

def scale_patch(im,factor):
 if factor==1:return im
 bbox=im.getbbox()
 if not bbox:return im
 patch=im.crop(bbox);cx=(bbox[0]+bbox[2])/2;cy=(bbox[1]+bbox[3])/2;size=(round(patch.width*factor),round(patch.height*factor));patch=patch.resize(size,Image.Resampling.LANCZOS);out=Image.new('RGBA',im.size);out.alpha_composite(patch,(round(cx-size[0]/2),round(cy-size[1]/2)));return out
report={};sheet=Image.new('RGB',(1280,840),'#f3fff8');draw=ImageDraw.Draw(sheet)
for i,h in enumerate(['flat','kitten','block','wedge']):
 if not all((SRC/f'{h}-{v}.png').exists() for v in ['bow','lace']):continue
 layers={}
 for variant in ['bow','lace','pearl','ribbon']:
  if not (SRC/f'{h}-{variant}.png').exists():continue
  for category in ['decoration','strap','charm']:
   if (variant=='lace' and category=='charm') or (variant=='ribbon' and category=='decoration'):continue
   im,tint,info=extract(h,variant,category);layers[variant+'_'+category]=(im,tint);report[h+'_'+variant+'_'+category]=info
 # Explicit variants use the same correctly foreshortened painted foundation.
 options={'decoration_small':('bow_decoration',.72),'decoration_big':('bow_decoration',1),'decoration_drop':('lace_decoration',1),'decoration_flower':('pearl_decoration',1),'strap_thin':('bow_strap',1),'strap_ribbon':('ribbon_strap',1),'strap_cross':('lace_strap',1),'charm_crystal':('bow_charm',1),'charm_mini':('ribbon_charm',1),'charm_pearl':('pearl_charm',1),'strap_pearl':('pearl_strap',1)}
 for name,(key,scale) in options.items():
  if key not in layers:continue
  im,tint=layers[key];im=scale_patch(im,scale);tint=scale_patch(tint,scale)
  im.save(OUT/f'{h}_{name}.webp',lossless=True)
  if tint.getbbox():tint.save(OUT/f'{h}_{name}_tint.webp',lossless=True)
  else:(OUT/f'{h}_{name}_tint.webp').unlink(missing_ok=True)
 base=Image.open(ROOT/f'assets/fitting2d/{h}_shoe.webp').convert('RGBA');skin=Image.open(ROOT/'assets/fitting2d/legs.webp').convert('RGBA');base=Image.alpha_composite(skin,base)
 for j,variant in enumerate(['bow','lace']):
  im=base.copy()
  for cat in ['decoration','strap','charm']:
   if variant+'_'+cat in layers:im=Image.alpha_composite(im,layers[variant+'_'+cat][0])
  im.thumbnail((320,390));sheet.paste(im,(i*320,j*420),im);draw.text((i*320+8,j*420+395),h+' '+variant,fill='#315c4b')
(SRC/'extraction-report.json').write_text(json.dumps(report,indent=2));sheet.save(SRC/'contact-sheet.jpg',quality=94)
print(json.dumps({'layers':len(list(OUT.glob('*.webp'))),'components':len(report),'report':str(SRC/'extraction-report.json')}))
