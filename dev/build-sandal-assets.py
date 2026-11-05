#!/usr/bin/env python3
"""Build complete source-camera sandal candidate kits from original reference edits.

Source paintings and candidate exports remain under dev. Publishing is blocked
until complete artistic and saved-flow acceptance, not just mask checks.
No runtime image manipulation service or skin reconstruction is used.
"""
from pathlib import Path
import argparse,json,shutil,importlib.util
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'dev/sandal-source'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--publish',action='store_true');p.add_argument('--styles',default='crystalsandal,flowersandal',help='Source candidates to prepare; accepted runtime art is never overwritten');args=p.parse_args()
if args.publish:p.error('Source builder cannot publish: accepted crystalsandal runtime art is source-locked; other sandals remain unaccepted. Rebuild candidates, then repeat native/flow/release acceptance; see dev/sandal-source/README.md')
missing=[name for name in ['product.png','fitting.png'] if not (SRC/name).exists()]
if missing:p.error('Original open-toe camera paintings required before building: '+', '.join(missing))
OUT=SRC/'runtime-candidate';STYLES=['crystalsandal','flowersandal','wrapsandal']
for folder in ['shoe2d','fitting2d']:(OUT/folder).mkdir(parents=True,exist_ok=True)
def read(path):return np.array(Image.open(path).convert('RGBA'))
def smooth(a,s=.65):return cv2.GaussianBlur(a.astype('float32'),(0,0),s)
def helper(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'dev'/name)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def save(path,rgb,alpha):
 a=np.zeros((*alpha.shape,4),np.uint8);a[:,:,:3]=rgb;a[:,:,3]=np.clip(alpha,0,255).astype('uint8')
 temp=path.with_name(path.stem+'.tmp.webp');Image.fromarray(a).save(temp,format='WEBP',lossless=True,method=6,exact=True);temp.replace(path)
def normalize(view):
 size=(1024,640) if view=='product' else (1024,1024)
 a=read(SRC/f'{view}.png');rgb=a[:,:,:3];r,g,b=rgb.astype(float).transpose(2,0,1)
 chroma=(r>g+60)&(b>g+45)
 subject=(a[:,:,3]>90)&~chroma
 # The source has open straps, so retain every substantial foreground island,
 # not just one connected component. No unchanged matte survives this key.
 n,l,st,_=cv2.connectedComponentsWithStats(subject.astype('uint8'),8)
 mask=np.zeros(subject.shape,np.uint8)
 for i in range(1,n):
  if st[i,cv2.CC_STAT_AREA]>30:mask[l==i]=1
 alpha=smooth(mask,.55)*255;alpha[alpha<4]=0
 fringe=(alpha>0)&chroma
 rgb=cv2.inpaint(rgb,fringe.astype('uint8'),3,cv2.INPAINT_TELEA)
 im=Image.fromarray(np.dstack([rgb,alpha.clip(0,255).astype('uint8')]))
 if view=='product':
  bounds=im.getchannel('A').point(lambda v:255 if v>127 else 0).getbbox();crop=im.crop(bounds);height=round(crop.height*833/crop.width);crop=crop.resize((833,height),Image.Resampling.LANCZOS);im=Image.new('RGBA',size);im.paste(crop,(96,541-height))
 else:
  im=im.resize(size,Image.Resampling.LANCZOS);a=np.array(im);Y,X=np.indices(a.shape[:2]);yy,xx=np.where((a[:,:,3]>127)&(Y>700));dx=171-int(xx.min());dy=964-int(yy.max());im=Image.fromarray(cv2.warpAffine(a,np.array([[1,0,dx],[0,1,dy]],float),size,flags=cv2.INTER_CUBIC))
 im.save(SRC/f'{view}-normalized.png');return np.array(im)

def ornament(view,style,size):
 S=3;im=Image.new('RGBA',(size[0]*S,size[1]*S));d=ImageDraw.Draw(im)
 def line(points,fill,width):d.line([(round(x*S),round(y*S)) for x,y in points],fill=fill,width=round(width*S),joint='curve')
 def ellipse(box,fill,outline=None,width=1):d.ellipse(tuple(round(v*S) for v in box),fill=fill,outline=outline,width=round(width*S))
 def poly(points,fill):d.polygon([(round(x*S),round(y*S)) for x,y in points],fill=fill)
 if view=='product':center=(397,440);path=[(537,268),(563,290),(587,314),(609,339),(631,366),(650,393)];flower=(397,440)
 else:center=(414,841);path=[(485,558),(511,580),(540,605),(568,631),(596,658),(623,687)];flower=(414,841)
 if style=='crystalsandal':
  # Double champagne rails hold individually set, foreshortened glass stones.
  line([(x+2,y+3) for x,y in path],(106,84,76,100),4)
  line(path,(201,172,126,255),3)
  for i,(x,y) in enumerate(path):
   rx,ry=(8+i*.2,5+i*.3);ellipse((x-rx-1,y-ry-1,x+rx+1,y+ry+1),(200,173,131,255))
   poly([(x-rx,y),(x,y-ry),(x+rx,y),(x,y+ry)],(217,236,238,255));poly([(x-rx,y),(x,y-ry),(x+1,y+1)],(255,255,250,255));line([(x,y-ry),(x+1,y+1),(x+rx,y)],(150,177,189,255),.7)
 elif style=='flowersandal':
  x,y=flower
  ellipse((x-28,y-8,x+35,y+24),(104,75,69,77))
  for i in range(5):
   angle=i*np.pi*2/5;cx=x+np.cos(angle)*19;cy=y+np.sin(angle)*11
   ellipse((cx-18,cy-11,cx+18,cy+11),(245,226,213,255),(220,195,179,255),.8)
   ellipse((cx-15,cy-10,cx+12,cy+6),(255,247,231,255))
  ellipse((x-7,y-5,x+7,y+5),(212,179,124,255));ellipse((x-4,y-4,x+2,y+1),(255,244,195,255))
 elif style=='wrapsandal':
  # One camera-local satin construction, with every visible turn joined to
  # the painted fastening/counter. The old straight strips missed the actual
  # ankle by >100px and ended in skin/empty space. Product loops are closed;
  # worn front turns terminate *inside* the existing strap at both sides, so
  # the invisible return is naturally occluded by the ankle rather than drawn
  # across it. No new calf/foot contour or source mount is introduced.
  def curve(start,segments):
   points=[start];q=np.array(start,dtype=float)
   for ax,ay,bx,by,ex,ey in segments:
    a,b,e=np.array([ax,ay]),np.array([bx,by]),np.array([ex,ey])
    for t in np.linspace(0,1,65)[1:]:points.append(tuple((1-t)**3*q+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*e))
    q=e
   return points
  if view=='product':
   # The far return is narrower/darker. Both complete ovals converge on a
   # sewn tab at the source outer quarter, immediately beneath its buckle.
   paths=[curve((861,83),[(805,83,658,102,607,128),(575,147,690,162,770,136),(820,121,850,101,861,83)]),
          curve((862,104),[(805,102,648,127,597,152),(569,173,686,189,770,159),(825,140,854,122,862,104)])]
   tab=curve((858,77),[(862,88,864,102,861,113)])
  else:
   # Both ends overlap the retained 380–420px ankle fastening or its satin
   # counter; the near curves follow the source's elliptical leg contour.
   paths=[curve((501,398),[(493,414,484,437,493,444),(541,477,666,475,738,433),(742,425,740,415,735,405)]),
          curve((499,405),[(484,432,477,459,486,466),(535,504,662,503,742,455),(748,442,744,421,735,410)])]
   tab=[]
  # Tight contact shade and soft satin edge, all sampled at 3x source pixels.
  # Endpoints lie under source satin, so there are no floating flat cuts.
  width=8.5 if view=='product' else 9
  for points in paths:line([(x+.8,y+2) for x,y in points],(112,83,68,85),width+2)
  for points in paths:
   line(points,(187,162,140,255),width+1.2)
   line([(x,y-.4) for x,y in points],(239,225,209,255),width-1)
   line([(x,y-2) for x,y in points],(255,249,235,255),1.5)
   line([(x,y+2.4) for x,y in points],(215,193,172,255),.8)
  if tab:
   line(tab,(202,178,153,255),10);line([(x-1,y) for x,y in tab],(246,232,214,255),7)
 result=im.resize(size,Image.Resampling.LANCZOS)
 if style=='wrapsandal' and view=='fitting':
  # The ribbon folds around the unchanged ankle silhouette; its side returns
  # disappear behind the leg instead of widening it or leaving a free edge.
  result.putalpha(ImageChops.multiply(result.getchannel('A'),Image.open(SRC/'fitting-normalized.png').getchannel('A')))
 return result

meta={}
for view,folder,part in [('product','shoe2d','base'),('fitting','fitting2d','shoe')]:
 a=normalize(view);rgb=a[:,:,:3];alpha=a[:,:,3].astype(float);h,w=a.shape[:2];Y,X=np.indices((h,w))
 if view=='product':
  shell,upper,semantic=helper('sandal-product-masks.py').semantic_masks(a)
 else:
  shell,upper,semantic=helper('sandal_masks_fitting.py').semantic_fitting(a)
 bottom=np.where(shell>127,Y,-1).max(axis=0)
 lum=smooth(rgb@np.array([.2126,.7152,.0722]),4)
 save(SRC/f'{view}-source-shell.webp',rgb,shell)
 save(SRC/f'{view}-source-upper.webp',255,upper)
 if view=='fitting':
  skin=np.maximum(0,alpha-shell)
  # Complete camera-matched source skin, with accepted upper calf retained.
  leg=rgb.copy();common=read(ROOT/'assets/fitting2d/stiletto6_legs.webp');legAlpha=skin.copy()
  mix=np.clip((Y-400)/80,0,1);w0=common[:,:,3]*(1-mix);w1=legAlpha*mix;den=w0+w1
  leg=((common[:,:,:3]*w0[:,:,None]+leg*w1[:,:,None])/np.maximum(den[:,:,None],1e-6)).clip(0,255).astype('uint8');legAlpha=den
  leg[:400]=common[:400,:,:3];legAlpha[:400]=common[:400,:,3]
 for style in STYLES:
  hardware=ornament(view,style,(w,h));hardware.save(SRC/f'{view}-{style}-trim.webp',lossless=True,method=6);ha=np.array(hardware)[:,:,3]
  base=Image.fromarray(np.dstack([rgb,shell.clip(0,255).astype('uint8')]));base.alpha_composite(hardware)
  out=OUT/folder;save(out/f'{style}_{part}.webp',np.array(base)[:,:,:3],np.array(base)[:,:,3])
  effectupper=upper*(1-ha/255)
  # Ribbon wrap is satin and therefore belongs to the dye mask.
  if style=='wrapsandal':effectupper=np.maximum(upper,ha)
  save(out/f'{style}_upper.webp',255,effectupper)
  finishlum=smooth(np.array(base)[:,:,:3]@np.array([.2126,.7152,.0722]),2) if style=='wrapsandal' else lum
  save(out/f'{style}_shadow.webp',0,np.clip((242-finishlum)/155,0,.65)*effectupper)
  save(out/f'{style}_highlight.webp',255,np.clip((finishlum-205)/65,0,.6)*effectupper)
  if view=='product':
   save(out/f'{style}_binding.webp',255,np.maximum(0,shell-upper)*.14)
   save(out/f'{style}_insole.webp',255,np.maximum(0,shell-upper))
   save(out/f'{style}_sole.webp',255,shell*(Y>=bottom[None,:]-5))
  else:
   save(out/f'{style}_legs.webp',leg,legAlpha)
   # Remove socks from painted sole/support, but allow exposed toes and instep.
   save(out/f'{style}_occlusion.webp',255,np.maximum(shell,ha))
  meta.setdefault(style,{})[view]={'frame':[w,h],'source':view+'.png','toeX':int(np.where(np.array(base)[:,:,3]>127)[1].min()),'floorY':int(np.where(np.array(base)[:,:,3]>127)[0].max()),'trim':style,'sourceCameraIndependent':True,'candidateKit':True,'visualAcceptanceRequired':True,'semanticMask':semantic}
(SRC/'export.json').write_text(json.dumps(meta,indent=2)+'\n')
sheet=Image.new('RGB',(1800,1800),'#fff3e9');d=ImageDraw.Draw(sheet)
for col,style in enumerate(STYLES):
 for row,(view,folder,part,bg) in enumerate([('product','shoe2d','base','#fff4ed'),('product','shoe2d','base','#233c43'),('fitting','fitting2d','shoe','#fff4ed'),('fitting','fitting2d','shoe','#233c43')]):
  base=Image.open(OUT/folder/f'{style}_{part}.webp').convert('RGBA')
  if view=='fitting':
   leg=Image.open(OUT/folder/f'{style}_legs.webp').convert('RGBA');leg.putalpha(ImageChops.subtract(leg.getchannel('A'),Image.open(OUT/folder/f'{style}_occlusion.webp').getchannel('A')));leg.alpha_composite(base);base=leg
  base.thumbnail((590,415));tile=Image.new('RGB',(600,450),bg);tile.paste(base,((600-base.width)//2,0),base);sheet.paste(tile,(col*600,row*450));d.text((col*600+12,row*450+425),style+' / '+view,fill='#e67c99')
sheet.save(SRC/'export-contact.jpg',quality=95)
if args.publish:
 for folder in ['shoe2d','fitting2d']:
  for path in (OUT/folder).glob('*.webp'):
   if path.stem.split('_')[0] not in args.styles.split(','):continue
   target=ROOT/'assets'/folder/path.name;temp=target.with_name(target.stem+'.tmp.webp')
   shutil.copyfile(path,temp)
   temp.replace(target)
print('Candidate complete:39 layers; review dev/sandal-source/export-contact.jpg before --publish')
