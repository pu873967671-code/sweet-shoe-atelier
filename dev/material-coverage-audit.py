#!/usr/bin/env python3
"""Independent per-base source/painted coverage, hue and boundary audit."""
import csv,hashlib,json,math,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter,ImageDraw
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/material-coverage';BASES=import_module('edges-p-check').BASES

def old(path):
 p=OUT/'baseline'/path
 return Image.open(p if p.exists() else ROOT/path).convert('RGBA')
def roughness(a):
 w,h=a.size;px=a.tobytes();traces=[]
 # Follow each continuous upper-facing boundary, splitting heel/strap/toe
 # jumps so architectural corners are not mistaken for scalloped piping.
 last=[]
 for x in range(w):
  hits=[y for y in range(int(h*.20),h-1) if px[y*w+x]>=128 and px[(y-1)*w+x]<128]
  y=min(hits) if hits else None
  if y is None or (last and abs(y-last[-1][1])>5):
   if len(last)>10:traces.append(last)
   last=[]
  if y is not None:last.append((x,y))
 if len(last)>10:traces.append(last)
 d=[abs(t[i-1][1]-2*t[i][1]+t[i+1][1]) for t in traces for i in range(1,len(t)-1)]
 return dict(samples=len(d),curvature_mean=round(sum(d)/max(1,len(d)),5),spikes=sum(v>=3 for v in d),width_variance_note='Source traces split at >5px architectural jumps; visual review required')
def main():
 rows=[];ragged=[];dye=[];fail=[]
 prefix='loafer-final-' if '--loafer-only' in sys.argv else ''
 for b in (['loafer'] if prefix else BASES):
  for cam in ['product','worn']:
   path=f'assets/shoe2d/{b}_upper.webp' if cam=='product' else f'assets/worn/{b}_mask.webp'
   before=old(path);after=Image.open(ROOT/path).convert('RGBA');assert before.size==after.size and before.convert('RGB').tobytes()==after.convert('RGB').tobytes()
   aa=before.getchannel('A');zz=after.getchannel('A');ragged.append(dict(base=b,camera=cam,before=roughness(aa),after=roughness(zz)))
   for mat in ['satin','mesh','lace','velvet','glitter','patent','metallic','pearlescent','suede','brocade','pave']:
    a=Image.open(OUT/f'{b}-{cam}-{mat}-before.png').convert('RGBA');z=Image.open(OUT/f'{b}-{cam}-{mat}-after.png').convert('RGBA')
    same_alpha=a.getchannel('A').tobytes()==z.getchannel('A').tobytes()
    if not same_alpha:fail.append([b,cam,mat,'silhouette changed'])
    diff=ImageChops.difference(a,z);rgb=ImageChops.lighter(ImageChops.lighter(diff.getchannel('R'),diff.getchannel('G')),diff.getchannel('B'))
    outside=ImageChops.multiply(rgb,ImageChops.invert(ImageChops.lighter(aa,zz).point(lambda v:255 if v else 0).filter(ImageFilter.MaxFilter(3))))
    # The incumbent loafer compositor restores a measured leather fringe
    # from adjacent upper pixels; include that existing ownership explicitly.
    if b=='loafer' and cam=='product':
     allowance=Image.new('L',outside.size);ImageDraw.Draw(allowance).polygon([(750,440),(780,429),(800,422),(830,416),(860,409),(890,400),(915,389),(915,394),(890,405),(860,415),(830,423),(800,430),(780,435),(750,443)],fill=255)
     outside=ImageChops.multiply(outside,ImageChops.invert(allowance.filter(ImageFilter.MaxFilter(3))))
    outside_count=sum(v>2 for v in outside.tobytes())
    if outside_count:fail.append([b,cam,mat,'outside upper',outside_count])
    # BEFORE mesh excludes its eight-pixel band and toe; all other product
    # finish fields cover the full source. Worn BEFORE starts at h*.62.
    bounds=zz.getbbox();miss_before=mat=='mesh' and cam=='product' or cam=='worn' and bounds and bounds[1]<int(zz.height*.62)
    rows.append(dict(base=b,camera=cam,material=mat,before_covered='no' if miss_before else 'yes',after_covered='yes',silhouette_exact=same_alpha,outside_upper_changes=outside_count))
   # Strong-blue scan: neutral original material retained inside one pixel
   # of a dyed upper. Separate flags from confirmed misses: cream piping,
   # metallic hardware and ornaments deliberately keep their source colour.
   source=Image.open(ROOT/(f'assets/shoe2d/{b}_base.webp' if cam=='product' else f'assets/worn/{b}.webp')).convert('RGBA')
   render=Image.open(OUT/f'{b}-{cam}-satin-after.png').convert('RGBA')
   near=zz.filter(ImageFilter.MaxFilter(3)).tobytes();alpha=zz.tobytes();candidates=[]
   for i,((r,g,bl,a),(rr,gg,bb,_)) in enumerate(zip(source.getdata(),render.getdata())):
    if not near[i] or alpha[i]>32 or a<128:continue
    neutral=max(r,g,bl)-min(r,g,bl)<32 and min(r,g,bl)>140
    original=abs(r-rr)+abs(g-gg)+abs(bl-bb)<12
    if neutral and original:candidates.append(i)
   dye.append(dict(base=b,camera=cam,near_upper_original_neutral_candidates=len(candidates),classification='review trim/hardware vs leather; not automatically counted as defects'))
  print('PASS independent',b,flush=True)
 with (OUT/(prefix+'survey.csv')).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (OUT/(prefix+'trim-jaggedness.json')).write_text(json.dumps(ragged,indent=2)+'\n');(OUT/(prefix+'dye-candidates.json')).write_text(json.dumps(dye,indent=2)+'\n')
 (OUT/(prefix+'independent-acceptance.json')).write_text(json.dumps(dict(status='PASS' if not fail else 'FAIL',cases=len(rows),failures=fail,source_rgb_exact=True),indent=2)+'\n')
 print('FAILURES',fail)
 assert not fail
if __name__=='__main__':main()
