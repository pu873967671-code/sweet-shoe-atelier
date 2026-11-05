#!/usr/bin/env python3
"""Repair enclosed Grand-bow extraction holes from retained original paintings.

Pillow only; exact original exterior alpha and bounding box. Satin RGB follows
accepted source registration; tint covers the entire satin. Run after legacy,
heel-height and platform exporters. No shoe/skin/anatomy/camera edits.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import hashlib, json, os
ROOT=Path(__file__).resolve().parents[2]
SRC=Path(__file__).with_name('grand-bow-source');SRC.mkdir(exist_ok=True)
QA=ROOT/'qa/session-0425-bow-cleanup';QA.mkdir(exist_ok=True)
STYLES=['flat','kitten','block','wedge','stiletto6','stiletto9','platform']
records=json.loads((ROOT/'dev/accessory-edits/extraction-report.json').read_text())['layers']
def retained(style,suffix=''):
 p=ROOT/f'assets/shoe2d/accessories/{style}_decoration_big{suffix}.webp';s=SRC/p.name
 if not s.exists():s.write_bytes(p.read_bytes())
 return Image.open(s).convert('RGBA')
def source(style):
 record=next(r for r in records if r['name']==style+'_decoration_big')
 im=Image.open(ROOT/record['source']).convert('RGBA').resize((1024,640),Image.Resampling.LANCZOS)
 im=im.transform((1024,640),Image.Transform.AFFINE,tuple(v for row in record['warp'] for v in row),Image.Resampling.BICUBIC)
 return ImageOps.grayscale(im).point(lambda v:min(255,round(v*1.2)))
def interp(x,xs,ys):
 for i in range(1,len(xs)):
  if x<=xs[i]:return ys[i-1]+(ys[i]-ys[i-1])*(x-xs[i-1])/(xs[i]-xs[i-1])
 return ys[-1]
def remap(im,shift):
 out=Image.new('L',im.size)
 for x in range(im.width):
  strip=im.crop((x,0,x+1,im.height)).transform((1,im.height),Image.Transform.AFFINE,(1,0,0,0,1,-shift(x)),Image.Resampling.BICUBIC)
  out.paste(strip,(x,0))
 return out
paint={h:source(h) for h in STYLES[:4]}
for h in (6,9):paint['stiletto'+str(h)]=remap(paint['kitten'],lambda x:interp(x,[0,285,594,855,1024],[15,15 if h==6 else 20,14,-8 if h==6 else -2,0]))
paint['platform']=remap(paint['block'],lambda x:-52*(1-min(1,max(0,(x-300)/550))))
report={'status':'PASS','provenance':{'model':'retained original gpt-image-2 sources; no new generation','registeredSource':'dev/accessory-edits/extraction-report.json','originals':'dev/fitting-polish/grand-bow-source/','sourceSHA256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.glob('*.webp'))}},'scope':'Enclosed satin holes and complete tint only; tiny inherited exterior contour scraps remain follow-up. No shared worn projection.','styles':[]}
sheet=Image.new('RGB',(1400,len(STYLES)*380),'#273837');draw=ImageDraw.Draw(sheet)
for row,h in enumerate(STYLES):
 before=retained(h);retained(h,'_tint');old=before.getchannel('A');solid=old.point(lambda v:255 if v>100 else 0);ImageDraw.floodfill(solid,(0,0),128)
 interior=solid.point(lambda v:255 if v!=128 else 0).filter(ImageFilter.MinFilter(5))
 alpha=Image.composite(Image.new('L',old.size,255),old,interior)
 assert Image.composite(alpha,old,interior.point(lambda v:255-v)).tobytes()==old.tobytes(),h+' exterior alpha changed'
 assert alpha.getbbox()==old.getbbox(),h+' bounds changed'
 gray=paint[h];after=Image.merge('RGBA',(gray,gray,gray,alpha));tint=Image.merge('RGBA',(Image.new('L',old.size,255),)*3+(alpha,))
 for im,suffix in [(after,''),(tint,'_tint')]:
  p=ROOT/f'assets/shoe2d/accessories/{h}_decoration_big{suffix}.webp';temp=p.with_name('.'+p.name+'.tmp');im.save(temp,format='WEBP',lossless=True,exact=True,method=6);temp.replace(p)
 repaired=sum(a!=b for a,b in zip(alpha.get_flattened_data(),old.get_flattened_data()))
 record={'style':h,'repairedInteriorPixels':repaired,'exteriorAlphaExact':True,'boundsExact':True,'paintingTintAlphaExact':Image.open(ROOT/f'assets/shoe2d/accessories/{h}_decoration_big_tint.webp').getchannel('A').tobytes()==alpha.tobytes(),'sha256':hashlib.sha256((ROOT/f'assets/shoe2d/accessories/{h}_decoration_big.webp').read_bytes()).hexdigest()};report['styles'].append(record)
 bb=old.getbbox();crop=(bb[0]-8,bb[1]-8,bb[2]+8,bb[3]+8)
 for col,(bg,im) in enumerate([('#fff1e7',before),('#fff1e7',after),('#273837',before),('#273837',after)]):
  patch=im.crop(crop);patch.thumbnail((300,340));tile=Image.new('RGBA',(340,355),bg);tile.alpha_composite(patch,((340-patch.width)//2,8));sheet.paste(tile.convert('RGB'),(col*350,row*380));draw.text((col*350+8,row*380+356),h+(' before' if col%2==0 else ' after'),fill='#efb9cc')
 native=Image.new('RGBA',after.size,'#273837');native.alpha_composite(after);native.crop(crop).resize(((crop[2]-crop[0])*3,(crop[3]-crop[1])*3),Image.Resampling.LANCZOS).convert('RGB').save(QA/(h+'-native-after.jpg'),quality=96)
sheet.save(QA/'settled-before-after.jpg',quality=96)
(QA/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
