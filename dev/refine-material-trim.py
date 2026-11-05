#!/usr/bin/env python3
"""Source-colour fitted loafer piping; alpha only, no morphological filtering.

Each camera/foot has its own source interval. Fit local quadratics to the
painting's cream-to-leather transition, then integrate a one-pixel feather.
Pinned continuation inputs keep earlier material/buckle/edges fixes intact.
"""
import io,json,math,sys
from pathlib import Path
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/material-coverage';PIN=OUT/'trim-baseline'

def solve(m,b):
 a=[list(row)+[v] for row,v in zip(m,b)]
 for j in range(3):
  pivot=max(range(j,3),key=lambda k:abs(a[k][j]));a[j],a[pivot]=a[pivot],a[j]
  t=a[j][j]
  for k in range(j,4):a[j][k]/=t
  for i in range(3):
   if i==j:continue
   t=a[i][j]
   for k in range(j,4):a[i][k]-=t*a[j][k]
 return [a[i][3] for i in range(3)]

def fit(points,x,radius=13):
 samples=[(xx-x,y,math.exp(-((xx-x)/(radius*.55))**2)) for xx,y in points if abs(xx-x)<=radius]
 sums=[sum(w*t**p for t,y,w in samples) for p in range(5)]
 rhs=[sum(w*y*t**p for t,y,w in samples) for p in range(3)]
 return solve([[sums[i+j] for j in range(3)] for i in range(3)],rhs)[0]

def boundary(a,x,y0):
 hits=[y for y in range(y0,a.height-1) if a.getpixel((x,y))>=128 and a.getpixel((x,y-1))<128 and all(a.getpixel((x,yy))>=128 for yy in range(y,min(y+8,a.height)))]
 return min(hits) if hits else None

def trace(source,a,x0,x1,y0,threshold):
 rgb=source.filter(ImageFilter.GaussianBlur(.65));points=[];old=[]
 for x in range(x0,x1+1):
  y=boundary(a,x,y0);old.append((x,y));candidates=[]
  for yy in range(y-4,y+6):
   r,g,b,_=rgb.getpixel((x,yy));rn,gn,bn,_=rgb.getpixel((x,yy+1));v=r-b;vn=rn-bn
   if v>=threshold>vn:candidates.append((abs(yy-y),yy+(v-threshold)/max(.001,v-vn)))
  points.append((x,min(candidates)[1] if candidates else float(y)))
 return old,[(x,fit(points,x)) for x,_ in points]

def main():
 rows=[]
 for cam,variants,intervals in [('shoe2d',[''],[(570,897,130,20)]),('worn',[''],[(195,343,600,22),(378,545,600,20)])]:
  for variant in variants:
   name='loafer'+variant;path=f'assets/{cam}/{name}_'+('upper' if cam=='shoe2d' else 'mask')+'.webp';pin=PIN/path
   if not pin.exists():pin.parent.mkdir(parents=True,exist_ok=True);pin.write_bytes((ROOT/path).read_bytes())
   old=Image.open(pin).convert('RGBA');alpha=old.getchannel('A');a=bytearray(alpha.tobytes());source=Image.open(ROOT/(f'assets/{cam}/{name}'+('_base' if cam=='shoe2d' else '')+'.webp')).convert('RGBA');traces=[]
   for x0,x1,y0,threshold in intervals:
    edge,target=trace(source,alpha,x0,x1,y0,threshold)
    for j,((x,y),(_,yy)) in enumerate(zip(edge,target)):
     taper=min(1,(x-x0)/10,(x1-x)/10);yy=y+(max(y-2.5,min(y+2.5,yy))-y)*taper
     slope=(target[min(j+1,len(target)-1)][1]-target[max(j-1,0)][1])/2
     for row in range(y-4,y+5):
      coverage=max(0,min(1,(row+.5-yy)/math.sqrt(1+slope*slope)+.5))
      a[row*old.width+x]=min(source.getpixel((x,row))[3],round(255*coverage))
    traces.append(dict(interval=[x0,x1],source_threshold=threshold,source_points=target))
   if cam=='worn':
    # Rear counter leather excluded by the former generic leg-contact cut.
    # Measured in this painting; reject skin and the warm cream collar.
    from PIL import ImageDraw
    region=Image.new('L',old.size);ImageDraw.Draw(region).polygon([(325,705),(342,695),(355,681),(358,692),(351,711),(342,728),(332,725)],fill=255)
    for i,v in enumerate(region.tobytes()):
     if not v:continue
     r,g,b,pa=source.getpixel((i%old.width,i//old.width))
     if pa>=128 and r-b<18 and r-g<14:a[i]=max(a[i],pa)
   im=old.copy();im.putalpha(Image.frombytes('L',old.size,bytes(a)));assert im.convert('RGB').tobytes()==old.convert('RGB').tobytes()
   buf=io.BytesIO();im.save(buf,format='WEBP',lossless=True,exact=True)
   if '--check' in sys.argv:assert (ROOT/path).read_bytes()==buf.getvalue(),path
   else:(ROOT/path).write_bytes(buf.getvalue())
   rows.append(dict(file=path,changed=sum(x!=y for x,y in zip(a,alpha.tobytes())),rgb_exact=True,traces=traces))
 (OUT/'trim-repairs.json').write_text(json.dumps(dict(status='PASS',files=rows),indent=2)+'\n');print('PASS source-fitted trim',[(r['file'],r['changed']) for r in rows])
if __name__=='__main__':main()
