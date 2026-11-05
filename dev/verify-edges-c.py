#!/usr/bin/env python3
"""Independent scope/pixel checks against the task's pinned baseline."""
import hashlib,io,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/edges-c';BASE='960c2ce886a12dbf5342a1ce16cb5bca6659d808'
def main():
 report=json.loads((OUT/'mask-verification.json').read_text());allowed={r['file'] for r in report['files']};checks=[]
 bases=['loafer','bowmule','pearlheel','luciteheel','stiletto9']
 expected={f'assets/worn/{b}{v}_{k}.webp' for b in bases for v in ['', '_frill','_lace'] for k in (['mask','sock'] if v else ['mask'])}
 assert allowed==expected
 for row in report['files']:
  file=row['file'];raw=subprocess.check_output(['git','show',f'{BASE}:{file}'],cwd=ROOT);before=Image.open(io.BytesIO(raw)).convert('RGBA');after=Image.open(ROOT/file).convert('RGBA');assert before.size==after.size==tuple(row['size'])
  assert before.convert('RGB').tobytes()==after.convert('RGB').tobytes(),file
  band=Image.open(OUT/(Path(file).stem+'-allowed-band.png')).convert('L');w,h=before.size;y0,y1=row['y_range'];a=before.getchannel('A').tobytes();b=after.getchannel('A').tobytes();bp=band.tobytes();changed=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
  assert len(changed)==row['changed_pixels'];assert all(bp[i] and y0<=i//w<=y1 for i in changed),file
  # Independently bound every edit to an original contour, including the
  # faint nonzero contour around detached codec reflections.
  original_alpha=before.getchannel('A');solid=original_alpha.point(lambda v:255 if v>=128 else 0)
  actual_band=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(19)),solid.filter(ImageFilter.MinFilter(19)))
  if file.endswith('_sock.webp'):
   nonzero=original_alpha.point(lambda v:255 if v else 0)
   actual_band=ImageChops.lighter(actual_band,ImageChops.subtract(nonzero.filter(ImageFilter.MaxFilter(19)),nonzero.filter(ImageFilter.MinFilter(19))))
  actual=actual_band.tobytes();assert all(actual[i] for i in changed),file
  assert all(y<=x for x,y in zip(a,b)),file
  checks.append(dict(file=file,changed=len(changed),size_exact=True,rgb_exact=True,outside_band_exact=True,sha256=hashlib.sha256((ROOT/file).read_bytes()).hexdigest()))
 baseline=json.loads((OUT/'baseline-assets.json').read_text());changed=[]
 for file,digest in baseline.items():
  if hashlib.sha256((ROOT/file).read_bytes()).hexdigest()!=digest:
   assert file in allowed,file;changed.append(file)
 assert len(changed)==25;assert not subprocess.check_output(['git','diff','--name-only','--','qa/'],cwd=ROOT)
 (OUT/'protected-checks.json').write_text(json.dumps(dict(status='PASS',assets=len(baseline),changed=checks,all_other_assets_exact=True,qa_exact=True),indent=2)+'\n')
 print('PASS all 25 narrow-band/RGB/size checks; all other assets and qa/ exact')
if __name__=='__main__':main()
