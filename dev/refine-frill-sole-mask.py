#!/usr/bin/env python3
"""Source-registered final-composite clearance; immutable input is pinned in Git.

Each last has its own front outsole search band. Only source-derived
codec/shadow tails beyond its painted brown outsole are removed. Explicit
reviewed gap polygons clear the flat/pearlheel rear-sole debris; source brown
outsole pixels are protected. No resampling, RGB edits or common shoe shape.
"""
import functools,io,json,re,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/frill-sole-mask';BASELINE='6617fd02'
REFS=json.loads(re.search(r'const SPRITES=(.*);',(ROOT/'js/worn-sprites.js').read_text()).group(1))
# x interval and bottom search row, measured independently in each base camera.
BANDS={'flat':[114,546,811],'block':[140,530,811],'kitten':[220,616,811],
 'stiletto6':[170,582,814],'stiletto9':[158,522,834],'wedge':[142,524,820],
 'maryjane':[121,547,810],'ballet':[120,547,810],'slingback':[201,609,816],
 'loafer':[148,573,811],'platform':[151,524,850],'bootie':[134,524,813],
 'pearlpump':[209,610,824],'bowsling':[216,624,823],'crystalpump':[195,601,821],
 'studpump':[198,600,825],'bowmule':[192,616,822],'pearlheel':[122,536,825],
 'luciteheel':[199,603,830],'crystalsandal':[164,518,831]}
# These polygons trace the empty corridor, not the footwear. Brown source
# outsole and the front collar's white leather remain outside the clearance.
GAPS={
 'flat': [[(174,784),(186,778),(199,774),(212,770),(227,765),(244,762),(262,757),(267,757),(256,765),(250,771),(234,784),(212,774),(200,780),(184,789)]],
 'pearlheel': [[(176,783),(185,782),(193,780),(198,778),(201,778),(199,783),(192,789),(186,789)]]}
REAR={'flat':[0,170,758,790],'block':[0,205,766,789],'kitten':[0,220,748,770],'stiletto6':[0,175,746,777],'stiletto9':[0,180,778,802],'wedge':[0,165,770,798],'maryjane':[0,158,770,790],'ballet':[0,153,770,794],'slingback':[0,220,742,763],'loafer':[24,176,771,796],'platform':[0,170,801,825],'bootie':[0,170,760,786],'pearlpump':[0,218,755,775],'bowsling':[0,220,745,764],'crystalpump':[0,220,754,771],'studpump':[0,220,757,779],'bowmule':[0,205,752,772],'pearlheel':[0,195,770,789],'luciteheel':[0,215,756,775],'crystalsandal':[0,200,778,803]}
@functools.lru_cache(maxsize=200)
def original(name):
 return Image.open(io.BytesIO(subprocess.check_output(['git','show',f'{BASELINE}:assets/worn/{name}.webp'],cwd=ROOT))).convert('RGBA')

def shoe_silhouette(name,im):
 """Both shoes, including undyeable trim/sole and translucent source edges.

 The flat's two outlines are measured in its own source camera. Its legacy
 sole mask includes the reported grey hangers and its legs map includes the
 tan front lining, so neither legacy mask alone is a complete shoe silhouette.
 Only that reviewed corridor is reclassified; all other shoe masks are kept.
 """
 base=name.split('_')[0];r=REFS[name];b=REFS[base]
 dx=b['x']-r['x'];dy=b['y']-r['y'];a=np.array(im)
 upper=np.array(original(name+'_mask'))[:,:,3]>0
 sole=Image.new('L',im.size);sole.paste(original(base+'_sole').getchannel('A'),(dx,dy))
 shoe=(upper|(np.array(sole)>0))&(a[:,:,3]>0)
 if base=='flat':
  rear=[(174,781),(180,779),(190,775),(200,771),(210,768),(220,765),(230,763),(240,760),(250,759),(260,756),(267,754)]
  # Conservative envelope of the translucent cream/lining rows, reviewed
  # in all three flat paintings; both edges are sampled per painting.
  front=[(174,791),(185,784),(195,779),(205,775),(210,773),(215,771),(220,769),(225,768),(230,767),(235,766),(240,764),(245,764),(250,762),(255,760),(260,758),(267,755)]
  rgb=a[:,:,:3].astype(int)
  brown=(rgb[:,:,0]-rgb[:,:,2]>=40)&(rgb[:,:,1]-rgb[:,:,2]>=17)&(a[:,:,3]>=128)
  for x in range(max(0,174+dx),min(im.width,268+dx)):
   expected=int(round(np.interp(x-dx,*zip(*rear))))+dy
   lo=max(0,expected-2);hi=min(im.height,expected+2)
   ys=np.flatnonzero(brown[lo:hi,x]);bottom=int(ys[-1]+lo) if len(ys) else expected
   guide=int(np.floor(np.interp(x-dx,*zip(*front))))+dy
   lo=max(0,guide-3);hi=min(im.height,guide+4)
   cream=(rgb[lo:hi,x,0]>190)&(rgb[lo:hi,x,1]>180)&(rgb[lo:hi,x,2]>145)&(a[lo:hi,x,3]>0)
   ys=np.flatnonzero(cream);top=int(ys[0]+lo) if len(ys) else guide
   # Preserve all front upper, trim AND lining, regardless of dye ownership.
   # Reclassify only the open corridor between the two real shoe boundaries.
   yy=np.arange(im.height);patch=(yy>=748+dy)&(yy<=792+dy)
   shoe[patch,x]=((yy[patch]<=bottom)|(yy[patch]>=top))&(a[patch,x,3]>0)
 return shoe

def protected_shoes(name,im):
 # One source pixel in all directions. Clearance never touches the original
 # antialiasing or this safety margin, so there is no new hard shoe edge.
 return np.array(Image.fromarray(np.uint8(shoe_silhouette(name,im))*255).filter(ImageFilter.MaxFilter(3)))>0

def region(name,im):
 base=name.split('_')[0];r=REFS[name];b=REFS[base];dx=b['x']-r['x'];dy=b['y']-r['y'];a=np.array(im);rgb=a[:,:,:3].astype(int)
 warm=(rgb[:,:,0]-rgb[:,:,2]>=40)&(rgb[:,:,1]-rgb[:,:,2]>=16)&(rgb[:,:,0]>=rgb[:,:,1])
 clear=np.zeros(a.shape[:2],bool);x0,x1,y0=BANDS[base]
 # Source-colour contour, independently sampled per x and per variant.
 for x in range(max(0,x0+dx),min(im.width,x1+dx)):
  ys=np.flatnonzero(warm[max(0,y0+dy):,x]&(a[max(0,y0+dy):,x,3]>=160))
  if not len(ys):continue
  bottom=int(ys[-1]+max(0,y0+dy));
  # Retain one antialias row. Remove the residual tail beyond the source-colour contour;
  # the opaque sole and pearl/lucite hardware stay above the contour.
  for y in range(bottom+2,min(im.height,bottom+13)):
   if a[y,x,3]>0:clear[y,x]=True
 rx0,rx1,ry0,ry1=REAR[base]
 for x in range(max(0,rx0+dx),min(im.width,rx1+dx)):
  ys=np.flatnonzero(warm[ry0+dy:ry1+dy,x]&(a[ry0+dy:ry1+dy,x,3]>=160))
  if not len(ys):continue
  bottom=int(ys[-1]+ry0+dy)
  for y in range(bottom+2,min(im.height,bottom+9,ry1+dy)):
   if a[y,x,3]>0:clear[y,x]=True
 for poly in GAPS.get(base,[]):
  m=Image.new('L',im.size);ImageDraw.Draw(m).polygon([(x+dx,y+dy) for x,y in poly],fill=255)
  # Sole protection includes its translucent brown antialiasing.
  gap=np.array(m)>0
  if base=='flat':
   # Locate the rear brown sole independently of the warm front lining.
   guides=[(174,781),(180,779),(190,775),(200,771),(210,768),(220,765),(230,763),(240,760),(250,759),(260,756),(267,754)]
   strong=(rgb[:,:,0]-rgb[:,:,2]>=40)&(rgb[:,:,1]-rgb[:,:,2]>=17)&(a[:,:,3]>=128)
   for x in range(max(0,174+dx),min(im.width,268+dx)):
    expected=int(round(np.interp(x-dx,[p[0] for p in guides],[p[1] for p in guides])))+dy
    lo=max(0,expected-2);hi=min(im.height,expected+2)
    ys=np.flatnonzero(strong[lo:hi,x]);edge=int(ys[-1]+lo+1) if len(ys) else expected+1
    gap[:edge+1,x]=False
   clear |= gap
  else:clear |= gap&~warm
 return clear&~protected_shoes(name,im)

def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for name in REFS:
  im=original(name);a=np.array(im);fix=region(name,im);shoe=protected_shoes(name,im);new=a.copy();new[fix,3]=0
  assert not np.any(fix&shoe),name
  assert np.array_equal(a[shoe],new[shoe]),name
  # Keep original encoded artwork byte-exact. Apply this small matte only
  # after the complete runtime composite, so skin/cloth shading is unchanged.
  path=ROOT/f'assets/worn/{name}_clear.webp'
  matte=np.full_like(a,255);matte[:,:,3]=np.uint8(fix)*255
  if '--check' in sys.argv:
   assert np.array_equal(np.array(Image.open(path).convert('RGBA')),matte),name
  else:Image.fromarray(matte).save(path,lossless=True,exact=True,method=6)
  assert np.array_equal(a[:,:,:3],new[:,:,:3]);assert np.array_equal(a[~fix],new[~fix])
  rows.append(dict(sprite=name,removed=int(np.sum(a[:,:,3]!=new[:,:,3])),region_pixels=int(fix.sum()),protected_shoe_pixels=int(shoe.sum()),shoe_pixels_removed=0))
 (OUT/'source-scope.json').write_text(json.dumps(dict(status='PASS',baseline=BASELINE,rgb_exact=True,outside_region_exact=True,shoe_pixels_removed=0,shoe_dilation_px=1,files=rows),indent=2)+'\n')
 print('PASS alpha-only',len(rows),'sprites;',sum(r['removed'] for r in rows),'pixels')
if __name__=='__main__':main()
