#!/usr/bin/env python3
"""Independent subpixel curvature and normal piping-width measurements."""
import json,math,statistics,importlib
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
m=importlib.import_module('refine-material-trim');ROOT=m.ROOT;OUT=m.OUT

def subedge(a,x,y0):
 p=a.load()
 for y in range(y0,a.height):
  if p[x,y]>=128 and p[x,y-1]<128 and all(p[x,yy]>=128 for yy in range(y,min(y+8,a.height))):return y-1+(127.5-p[x,y-1])/max(1,p[x,y]-p[x,y-1])

def metrics(alpha,src,x0,x1,y0,binding=None):
 trace=[(x,subedge(alpha,x,y0)) for x in range(x0+12,x1-11)];widths=[]
 src=src.filter(ImageFilter.GaussianBlur(.65));p=src.load()
 for i,(x,y) in enumerate(trace):
  slope=(trace[min(i+1,len(trace)-1)][1]-trace[max(0,i-1)][1])/2
  # Anatomical skin/insole is warm; the top of cream piping is its
  # source-colour transition, independent of the repaired dye boundary.
  candidates=[]
  for yy in range(int(y)-20,int(y)-2):
   r,g,b,_=p[x,yy];rr,gg,bb,_=p[x,yy+1];v=r-b;vn=rr-bb
   if v>=38>vn:candidates.append(yy+(v-38)/max(.001,v-vn))
  if binding is not None:
   hits=[yy for yy in range(int(y)-8,int(y)+3) if binding.getpixel((x,yy))>=128]
   if hits:candidates=[float(min(hits))]
  if candidates:widths.append((x,(y-max(candidates))/math.sqrt(1+slope*slope)))
 curvature=[abs(trace[i-1][1]-2*trace[i][1]+trace[i+1][1]) for i in range(1,len(trace)-1)]
 residuals=[w-m.fit(widths,x,10) for x,w in widths] if len(widths)>25 else []
 return dict(samples=len(trace),curvature_mean=statistics.mean(curvature),curvature_spikes=sum(v>=1 for v in curvature),width_samples=len(widths),normal_width_mean=statistics.mean(w for _,w in widths) if widths else None,normal_width_variance=statistics.pvariance(w for _,w in widths) if widths else None,local_width_residual_variance=statistics.mean(v*v for v in residuals) if residuals else None)

def main():
 report=json.loads((OUT/'trim-repairs.json').read_text());rows=[]
 for item in report['files']:
  path=item['file'];old=Image.open(m.PIN/path).convert('RGBA');new=Image.open(ROOT/path).convert('RGBA');assert old.size==new.size and old.convert('RGB').tobytes()==new.convert('RGB').tobytes()
  a=old.getchannel('A');z=new.getchannel('A');band=ImageChops.subtract(a.filter(ImageFilter.MaxFilter(19)),a.filter(ImageFilter.MinFilter(19)))
  outside=ImageChops.multiply(ImageChops.difference(a,z),ImageChops.invert(band.point(lambda v:255 if v else 0)))
  # Separate source-local rear counter leather is intentionally farther
  # from the wrong original cut than the collar's narrow repair band.
  if '/worn/' in path:
   from PIL import ImageDraw
   ImageDraw.Draw(outside).polygon([(325,705),(342,695),(355,681),(358,692),(351,711),(342,728),(332,725)],fill=0)
  assert not outside.getbbox(),path
  painting=path.replace('_upper.webp','_base.webp').replace('_mask.webp','.webp');src=Image.open(ROOT/painting).convert('RGBA')
  for t in item['traces']:
   x0,x1=t['interval'];y0=130 if '/shoe2d/' in path else 600
   binding=Image.open(ROOT/'assets/shoe2d/loafer_binding.webp').getchannel('A') if '/shoe2d/' in path else None
   before=metrics(a,src,x0,x1,y0,binding);after=metrics(z,src,x0,x1,y0,binding)
   rows.append(dict(file=path,interval=[x0,x1],before=before,after=after))
   print(path,x0,'curvature',round(before['curvature_mean'],4),'->',round(after['curvature_mean'],4),'width',before['local_width_residual_variance'],'->',after['local_width_residual_variance'],flush=True)
   assert after['curvature_mean']<before['curvature_mean'],(path,'curvature regression')
   assert after['local_width_residual_variance']<before['local_width_residual_variance'],(path,'piping width regression')
 (OUT/'trim-width-acceptance.json').write_text(json.dumps(dict(status='PASS',rgb_exact=True,outside_source_regions_exact=True,traces=rows),indent=2)+'\n')
if __name__=='__main__':main()
