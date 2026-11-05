#!/usr/bin/env python3
"""Clothing-only mint/candy finish of existing local cartoon portraits.
Reads a fixed source revision so rebuilds never accumulate colour transforms.
Hair/skin are protected by garment zones and narrow hue masks; alpha is exact.
"""
from io import BytesIO
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCE_REVISION='92ab7cf' # Existing source art before the Supervisor 13:32 palette pass.
OUT=ROOT/'qa'/'character-palette'
OUT.mkdir(exist_ok=True)

def hsv(rgb):
 mx=rgb.max(2);mn=rgb.min(2);d=mx-mn;s=np.divide(d,mx,out=np.zeros_like(d),where=mx>0);h=np.zeros_like(d)
 m=d>0
 sel=m&(mx==rgb[:,:,0]);h[sel]=((rgb[:,:,1]-rgb[:,:,2])[sel]/d[sel])%6
 sel=m&(mx==rgb[:,:,1]);h[sel]=(rgb[:,:,2]-rgb[:,:,0])[sel]/d[sel]+2
 sel=m&(mx==rgb[:,:,2]);h[sel]=(rgb[:,:,0]-rgb[:,:,1])[sel]/d[sel]+4
 return h/6,s,mx

def rgb(h,s,v):
 i=np.floor(h*6).astype(int)%6;f=h*6-np.floor(h*6);p=v*(1-s);q=v*(1-f*s);t=v*(1-(1-f)*s)
 result=np.zeros((*h.shape,3))
 for n,values in enumerate([(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)]):
  mask=i==n
  for c,val in enumerate(values):result[:,:,c][mask]=val[mask]
 return result

files=sorted((ROOT/'assets').glob('c_*_*.webp'))+sorted((ROOT/'assets/mentor').glob('mentor_*.webp'))+[ROOT/'assets/mentor_neutral.webp']
changes=[];sources={};results={}
for path in files:
 rel=path.relative_to(ROOT);source=Image.open(BytesIO(subprocess.check_output(['git','show',SOURCE_REVISION+':'+str(rel)],cwd=ROOT))).convert('RGBA');a=np.array(source);before=a.copy();r=a[:,:,:3]/255.;h,s,v=hsv(r);yy,xx=np.mgrid[:a.shape[0],:a.shape[1]];yn=yy/a.shape[0];xn=xx/a.shape[1];opaque=a[:,:,3]>0
 nh=h.copy();ns=s.copy();nv=v.copy();mask=np.zeros(h.shape,dtype=bool)
 def recolor(m,hue,saturation,value):
  global mask
  m=m&opaque;mask|=m;nh[m]=hue if np.isscalar(hue) else hue[m];ns[m]=saturation if np.isscalar(saturation) else saturation[m];nv[m]=value if np.isscalar(value) else value[m]
 name=path.name
 if name.startswith('c_casual'):
  recolor((yn>.39)&(h>.15)&(h<.40)&(s>.08),.405,np.clip(s*.80,.13,.32),np.minimum(1,v*1.08))
 elif name.startswith('c_school'):
  recolor((yn>.62)&(h>.49)&(h<.73)&(s>.10),.448,np.clip(s*.70,.12,.43),np.minimum(1,v*.92+.12))
 elif name.startswith('c_tea'):
  recolor((yn>.63)&(h>.115)&(h<.45)&(s<.46),.405,np.clip(s*.66,.045,.19),np.minimum(1,v*1.035+.018))
 elif name.startswith('c_bride'):
  recolor((yn>.65)&(h>.115)&(h<.27)&(s<.33),.12,np.clip(s*.72,.04,.17),np.minimum(1,v*1.025+.01))
 elif name.startswith('c_buns') or name.startswith('c_pink'):
  recolor((yn>.66)&((h>.90)|(h<.015))&(s>.10),.947,np.minimum(.48,s*1.06),np.minimum(1,v*1.04+.01))
 else:
  # Cream cardigan and existing green tape; never touch orange skin/pink hair.
  recolor((yn>.22)&(yn<.62)&(h>.12)&(h<.47)&(s>.055)&(s<.52),.405,np.clip(s*.80,.075,.26),np.minimum(1,v*1.035+.01))
  # Existing candy skirt/hair remain source-exact; their hue ranges overlap.
 new=np.uint8(np.clip(np.round(rgb(nh,ns,nv)*255),0,255));a[:,:,:3][mask]=new[mask]
 # Prove there is no unintended full-image grade or alpha alteration.
 assert np.array_equal(a[:,:,3],before[:,:,3])
 assert np.array_equal(a[:,:,:3][~mask],before[:,:,:3][~mask])
 # Entire facial region remains source-exact for customer portraits.
 if name.startswith('c_'): assert np.array_equal(a[:140],before[:140])
 result=Image.fromarray(a);result.save(path,'WEBP',quality=90,method=6,exact=True)
 decoded=np.asarray(Image.open(path).convert('RGBA'));assert np.array_equal(decoded[:,:,3],before[:,:,3])
 sources[str(rel)]=source;results[str(rel)]=Image.open(path).convert('RGBA');changes.append({'asset':str(rel),'changed_pixels':int(mask.sum()),'alpha_preserved':True,'unmasked_pixels_unchanged_before_encoding':True})

def sheet(mapping,paths,dest,width=150,height=200):
 canvas=Image.new('RGB',(len(paths)*width,height+28),'#edfbf4');draw=ImageDraw.Draw(canvas)
 for i,key in enumerate(paths):
  im=mapping[key].copy();im.thumbnail((width-12,height));canvas.paste(im,(i*width+(width-im.width)//2,0),im);draw.text((i*width+5,height+5),Path(key).stem.replace('mentor_','').replace('_neutral',''),fill='#315d4e')
 canvas.save(OUT/dest,quality=94)
customer=[str(p.relative_to(ROOT)) for p in files if p.name.startswith('c_') and '_neutral' in p.name]
mentor=[str(p.relative_to(ROOT)) for p in files if p.parent.name=='mentor']
for label,mapping in [('before',sources),('after',results)]:
 sheet(mapping,customer,'customers-'+label+'.jpg',150,200);sheet(mapping,mentor,'mimi-'+label+'.jpg',175,430)
import json
(OUT/'report.json').write_text(json.dumps({'status':'PASS','assets':changes,'note':'Regraded existing 3D cartoon clothing only; no generated images. Originals retained at source revision 92ab7cf in git. WebP RGB uses quality90; alpha remains exact after encoding.'},indent=2)+'\n')
print(f'PASS: {len(changes)} local character assets; exact decoded alpha; protected pixels retained before RGB encoding')
