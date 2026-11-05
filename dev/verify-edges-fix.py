#!/usr/bin/env python3
"""Independent scope, original-band and pre-chunk dye-loss regression guard."""
import hashlib,io,json,subprocess,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'dev'))
f=import_module('fix-edges-dye');OUT=f.OUT

def main():
 rows=[];expected={f'assets/worn/{b}{v}_mask.webp' for bs in f.GROUPS.values() for b in bs for v in ['', '_frill','_lace']}
 tree=subprocess.check_output(['git','ls-tree','-r',f.INPUT,'assets'],cwd=ROOT,text=True);changed=[];assets=0;qa=0
 for line in tree.splitlines():
  meta,path=line.split('\t');blob=meta.split()[2];data=(ROOT/path).read_bytes();digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  if path.startswith('assets/'):assets+=1
  else:qa+=1
  if digest!=blob:assert path in expected,path;changed.append(path)
 assert set(changed)==expected,(len(changed),len(expected))
 subprocess.run(['git','diff','--quiet',f.INPUT,'--','qa'],cwd=ROOT,check=True)
 qa=len(subprocess.check_output(['git','ls-files','qa'],cwd=ROOT,text=True).splitlines())
 for group,bases in f.GROUPS.items():
  for b in bases:
   for case,variant in [(0,'_lace'),(1,''),(2,'_frill')]:
    name=b+variant;path=f'assets/worn/{name}_mask.webp'
    original=Image.open(io.BytesIO(subprocess.check_output(['git','show',f'{f.ORIGINALS[group]}:{path}'],cwd=ROOT))).convert('RGBA')
    before=Image.open(io.BytesIO(f.pinned(path))).convert('RGBA');after=Image.open(ROOT/path).convert('RGBA')
    assert original.size==before.size==after.size
    assert before.convert('RGB').tobytes()==after.convert('RGB').tobytes()
    old=original.getchannel('A');a=old.tobytes();bad=before.getchannel('A').tobytes();z=after.getchannel('A').tobytes();p=Image.open(OUT/f'{name}-trim-band.png').tobytes()
    # Independently bind all alpha edits to the ORIGINAL nine-pixel contour.
    solid=old.point(lambda v:255 if v>=128 else 0);band=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(19)),solid.filter(ImageFilter.MinFilter(19))).tobytes()
    assert all(band[i] for i in range(len(a)) if bad[i]!=z[i]),name
    assert all(bad[i]<=z[i]<=a[i] for i in range(len(a))),name
    assert all(z[i]==bad[i] for i in range(len(a)) if p[i]),name
    loss=lambda x:sum(a[i]>=64 and a[i]-x[i]>=32 and not p[i] for i in range(len(a)))
    undyed=lambda x:sum(a[i]>=128 and x[i]<64 and not p[i] for i in range(len(a)))
    assert loss(z)==undyed(z)==0,name
    rows.append(dict(base=b,case=case,source=name,loss_before=loss(bad),loss_after=loss(z),undyed_before=undyed(bad),undyed_after=undyed(z),original_boundary_exact=True,rgb_size_exact=True,trim_exact=True))
 report=dict(status='PASS',assets_checked=assets,qa_files_checked=qa,changed=changed,all_other_files_exact=True,cases=rows)
 (OUT/'regressions.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS 45 base/case dye-loss checks; 45 original-boundary/RGB/size guards;',assets,'assets and',qa,'qa files protected')
if __name__=='__main__':main()
