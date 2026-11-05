#!/usr/bin/env python3
"""Mount the accepted product's sewn ballet ribbons on the fitted ankle.

Pillow-only derivative. Original body below y760, legs and hosiery remain exact;
only the former tall ribbon component is replaced above that body. Mapping is
source-local and independent of window size, pair mounting and camera warp.
"""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/fitting2d'
def solve3(rows,values):
 a=[list(r)+[v] for r,v in zip(rows,values)]
 for i in range(3):
  pivot=max(range(i,3),key=lambda j:abs(a[j][i]));a[i],a[pivot]=a[pivot],a[i];f=a[i][i];a[i]=[v/f for v in a[i]]
  for j in range(3):
   if j!=i:
    f=a[j][i];a[j]=[v-f*w for v,w in zip(a[j],a[i])]
 return [r[3] for r in a]
src=[[449,350],[700,410],[910,134]];dst=[[290,850],[638,837],[690,565]]
rows=[r+[1] for r in dst];coeff=solve3(rows,[r[0] for r in src])+solve3(rows,[r[1] for r in src])
painting=Image.open(ROOT/'dev/maryjane-source/ballet-product-extracted.png').convert('RGBA')
# The extracted edit also contains warm lining and skin scraps. Keep only
# the product ribbon's semantic upper difference, with its soft native alpha.
product=ROOT/'assets/shoe2d'
ribbon=ImageChops.subtract(Image.open(product/'ballet_upper.webp').getchannel('A'),Image.open(product/'flat_upper.webp').getchannel('A'))
painting.putalpha(ImageChops.multiply(painting.getchannel('A'),ribbon))
patch=painting.convert('RGBa').transform((1024,1024),Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC).convert('RGBA')
# An empty product loop cannot be painted in front of an occupied ankle.
# Retain the original crossed instep ribbons and sewn bow, then mount only
# the visible FRONT faces of the two ankle turns on the measured skin contour.
# Their back faces and far fastening are hidden by the ankle, not translucent.
old=patch.copy();keep=Image.new('L',patch.size)
ImageDraw.Draw(keep).rectangle((0,705,1023,1023),fill=255)
patch.putalpha(ImageChops.multiply(patch.getchannel('A'),keep))
def ankle_band(left,right,top,depth):
 scale=4;box=(left,top-2,right+1,top+depth+18)
 w,h=(box[2]-box[0])*scale,(box[3]-box[1])*scale
 yy,xx=np.mgrid[:h,:w];x=box[0]+(xx+.5)/scale;y=box[1]+(yy+.5)/scale
 t=np.clip((x-left)/(right-left),0,1);edge=top+11*np.sin(np.pi*t)
 v=(y-edge)/depth
 alpha=((v>=0)&(v<=1)).astype(np.uint8)*255
 # Broad satin roll and narrow folded edges, with perspective-darkened ends.
 lum=218+32*np.exp(-((v-.27)/.19)**2)-18*np.exp(-((v-.94)/.1)**2)
 lum-=14*np.abs(2*t-1)**4
 rgb=np.clip(lum,0,255).astype(np.uint8)
 data=np.stack((rgb,rgb,rgb,alpha),axis=-1)
 band=Image.fromarray(data,'RGBA').convert('RGBa').resize((w//scale,h//scale),Image.Resampling.LANCZOS).convert('RGBA')
 patch.alpha_composite(band,(box[0],box[1]))
ankle_band(425,738,552,22)
ankle_band(420,730,593,21)
# The visible faces end exactly at the ankle silhouette; the far attachment
# is behind skin/hosiery. Supersampled alpha keeps the contour soft.
ankle=Image.new('L',patch.size);ImageDraw.Draw(ankle).rectangle((0,0,1023,654),fill=255)
skin=Image.open(OUT/'ballet_legs.webp').getchannel('A')
visible=ImageChops.lighter(ImageChops.invert(ankle),skin)
patch.putalpha(ImageChops.multiply(patch.getchannel('A'),visible))
# A continuous diagonal joins the lower crossed instep to the lower wrap.
# Reuse its original satin folds with an affine mapping, never a cut end.
diagonal=old.copy();dm=Image.new('L',patch.size);dd=ImageDraw.Draw(dm)
dd.polygon([(380,688),(674,559),(705,583),(409,720)],fill=255)
diagonal.putalpha(ImageChops.multiply(diagonal.getchannel('A'),dm))
diagonal=diagonal.convert('RGBa').transform(patch.size,Image.Transform.AFFINE,(1,0,0,0,1.35,-278),Image.Resampling.BICUBIC).convert('RGBA')
patch.alpha_composite(diagonal)
# Reuse the original folded knot/loop/tails, at the near-side attachment.
# Tight semantic clipping excludes the old far clasp and warm lining scraps.
bow=old.crop((650,525,916,690));ba=np.asarray(bow).copy()
neutral=np.max(ba[:,:,:3],axis=2)-np.min(ba[:,:,:3],axis=2)<16
ba[:,:,3]=np.where(neutral,ba[:,:,3],0)
bow=Image.fromarray(ba,'RGBA').convert('RGBa').resize((213,152),Image.Resampling.LANCZOS).convert('RGBA')
patch.alpha_composite(bow,(688,537))
alpha=patch.getchannel('A');cloth=Image.new('L',patch.size);shadow=cloth.copy();light=cloth.copy()
cp,sp,lp=cloth.load(),shadow.load(),light.load()
for y in range(500,900):
 for x in range(200,940):
  r,g,b,a=patch.getpixel((x,y));lum=.2126*r+.7152*g+.0722*b
  if max(r,g,b)-min(r,g,b)<16:
   cp[x,y]=a;sp[x,y]=round(min(.65,max(0,(248-lum)/175))*a);lp[x,y]=round(min(.6,max(0,(lum-205)/65))*a)
report={'source':'dev/maryjane-source/ballet-product-extracted.png','sourceAnchors':src,'wornAnchors':dst,'reconstruction':'original instep crossings and near bow; supersampled front-only ankle satin turns; hidden far loop/clasp','ankleTurns':[[425,738,552,22],[420,730,593,21]],'parts':{}}
for part in ['shoe','upper','shadow','highlight','occlusion']:
 name=f'ballet_{part}.webp';base=Image.open(ROOT/f'dev/flat-fidelity-source/ballet_{part}.webp').convert('RGBA');flat=Image.open(OUT/f'flat_{part}.webp').convert('RGBA')
 # Both styles share this body camera. Original ribbon-only extent is y254..668.
 base.paste(flat.crop((0,0,1024,760)),(0,0))
 # Retain the already accepted low lift, while the original ballet forefoot
 # keeps its almond toe. Both styles share this exact authored rear body.
 base.paste(flat.crop((650,760,1024,1024)),(650,760))
 # The empty flat counter includes its FAR upright tab above the heel.
 # An occupied ankle occludes that tab; only the sewn near bow belongs here.
 base.paste((0,0,0,0),(705,0,1024,600))
 if part=='shoe':base.alpha_composite(patch)
 else:
  old=base.getchannel('A')
  if part=='occlusion':a=ImageChops.lighter(old,alpha)
  elif part=='upper':a=ImageChops.screen(old,cloth)
  else:
   a=ImageChops.add(ImageChops.multiply(old,ImageChops.invert(cloth)),shadow if part=='shadow' else light)
  base.putalpha(a)
  if part in ['upper','highlight']:base=Image.merge('RGBA',(*[Image.new('L',base.size,255)]*3,a))
  elif part=='shadow':base=Image.merge('RGBA',(*[Image.new('L',base.size,0)]*3,a))
 base.save(OUT/name,lossless=True,exact=True);report['parts'][part]=hashlib.sha256((OUT/name).read_bytes()).hexdigest()
(ROOT/'dev/maryjane-source/ballet-ribbon-fidelity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
