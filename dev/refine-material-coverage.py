#!/usr/bin/env python3
"""Source-local buckle leather; alpha-only, pinned input."""
import io,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/material-coverage';rows=[]
def load(path):
 p=OUT/'baseline'/path
 if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/path).read_bytes())
 return Image.open(p).convert('RGBA')
def save(path,im,old):
 assert im.size==old.size and im.convert('RGB').tobytes()==old.convert('RGB').tobytes()
 buf=io.BytesIO();im.save(buf,format='WEBP',lossless=True,exact=True)
 if '--check' in sys.argv:assert (ROOT/path).read_bytes()==buf.getvalue(),path
 else:(ROOT/path).write_bytes(buf.getvalue())
 rows.append(dict(file=path,changed=sum(a!=b for a,b in zip(im.getchannel('A').tobytes(),old.getchannel('A').tobytes())),rgb_exact=True))
def buckle(camera,variant=''):
 path=f'assets/{camera}/slingback{variant}_'+('upper' if camera=='shoe2d' else 'mask')+'.webp';old=load(path);im=old.copy();a=bytearray(old.getchannel('A').tobytes());w,h=im.size
 painting=Image.open(ROOT/('assets/'+camera+'/slingback'+variant+('_base' if camera=='shoe2d' else '')+'.webp')).convert('RGBA')
 region=Image.new('L',im.size);d=ImageDraw.Draw(region)
 if camera=='shoe2d':polys=[[(834,153),(862,113),(884,135),(857,177)],[(864,112),(884,72),(898,100),(880,133)]]
 else:polys=[[(306,621),(322,601),(333,612),(318,632)],[(320,603),(332,590),(337,601),(331,613)],[(551,680),(568,657),(579,670),(563,691)],[(567,658),(575,644),(584,658),(578,671)]]
 for poly in polys:d.polygon(poly,fill=255)
 rp=region.tobytes()
 for i,(r,g,b,pa) in enumerate(painting.getdata()):
  # Neutral leather/stitches inside each measured strap; warm buckle metal
  # and lining stay exact, as do every pixel outside these source polygons.
  if rp[i] and pa>=96 and max(r,g,b)-min(r,g,b)<30 and r-b<20:a[i]=max(a[i],pa)
 im.putalpha(Image.frombytes('L',im.size,bytes(a)));save(path,im,old)
def main():
 buckle('shoe2d')
 for variant in ['', '_frill','_lace']:buckle('worn',variant)
 (OUT/'mask-repairs.json').write_text(json.dumps(dict(status='PASS',files=rows),indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
