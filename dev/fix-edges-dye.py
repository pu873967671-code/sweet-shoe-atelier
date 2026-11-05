#!/usr/bin/env python3
"""Restore edges-a/b/c dye overcuts; retain only painted, thin collar trim.

Pinned inputs, original sizes/RGB, no resampling. Sock repairs stay unchanged.
The anatomical matte supplies each last's own collar, never a shared trace.
"""
import hashlib,io,json,subprocess,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dev/qa-out/edges-fix'
INPUT='7ec9b42a'
ORIGINALS={'a':'83fb1675031e2e1f0ab1c62af3181979ce1d0fba','b':'a050e5a0beca7e7ae70c013a24407a9ed8102ebe','c':'960c2ce886a12dbf5342a1ce16cb5bca6659d808'}
GROUPS={'a':['flat','block','kitten','stiletto6','wedge'],'b':['platform','bootie','pearlpump','crystalpump','studpump'],'c':['loafer','bowmule','pearlheel','luciteheel','stiletto9']}
REG={'kitten_frill':-1,'kitten_lace':-1,'crystalpump_frill':-1,'bowmule_lace':-1,'pearlheel_frill':-2,'pearlheel_lace':-2,'stiletto9_lace':-1}
# Source-pixel perpendicular collar allowance, inspected against each painting.
RADII={'flat':6,'block':6,'kitten':6,'stiletto6':6,'wedge':6,'platform':6,'bootie':6,'pearlpump':6,'crystalpump':6,'studpump':6,'loafer':6,'bowmule':6,'pearlheel':6,'luciteheel':6,'stiletto9':4}
components=import_module('clean-maryjane-specks').components
def pinned(path):return subprocess.check_output(['git','show',f'{INPUT}:{path}'],cwd=ROOT)
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for group,bases in GROUPS.items():
  for base in bases:
   for variant in ['', '_frill','_lace']:
    name=base+variant;path=f'assets/worn/{name}_mask.webp'
    raw=pinned(path);before=Image.open(io.BytesIO(raw)).convert('RGBA')
    original=Image.open(io.BytesIO(subprocess.check_output(['git','show',f'{ORIGINALS[group]}:{path}'],cwd=ROOT))).convert('RGBA')
    source=Image.open(ROOT/f'assets/worn/{name}.webp').convert('RGBA');w,h=source.size
    leg=Image.open(ROOT/f'assets/worn/{base}_legs.webp').getchannel('A').point(lambda v:255 if v>=128 else 0)
    leg=Image.frombytes('L',leg.size,bytes(components(leg.tobytes(),leg.width,leg.height)))
    aligned=Image.new('L',(w,h));aligned.paste(leg,(REG.get(name,0),0))
    # MaxFilter follows the registered contour; colour below distinguishes
    # actual warm piping/yarn from neutral satin highlights and ornaments.
    collar=aligned.filter(ImageFilter.MaxFilter(RADII[base]*2+1)).tobytes()
    pixels=list(source.getdata());a=before.getchannel('A').tobytes();o=original.getchannel('A').tobytes();z=bytearray(a);protected=bytearray(w*h)
    for i,(r,g,b,pa) in enumerate(pixels):
     warm=r-b>=8 and r-g>=2
     yarn=min(g-r,g-b)>=3
     # Warm collar piping has its own material colour. Neutral tongue/bow
     # surfaces and outer heel/upper highlights must retain original dye.
     protected[i]=255 if collar[i] and (warm or yarn) else 0
     if a[i]<o[i] and not protected[i]:z[i]=o[i]
    after=before.copy();after.putalpha(Image.frombytes('L',(w,h),bytes(z)))
    encoded=io.BytesIO();after.save(encoded,format='WEBP',lossless=True,exact=True)
    if '--check' in sys.argv:assert (ROOT/path).read_bytes()==encoded.getvalue(),path
    else:(ROOT/path).write_bytes(encoded.getvalue())
    assert Image.open(ROOT/path).convert('RGBA').tobytes()==after.tobytes()
    assert before.size==original.size==after.size
    assert before.convert('RGB').tobytes()==after.convert('RGB').tobytes()
    assert all(a[i]<=z[i]<=o[i] for i in range(w*h))
    assert all(z[i]==a[i] for i in range(w*h) if protected[i])
    regression=lambda data:sum(o[i]>=64 and o[i]-data[i]>=32 and not protected[i] for i in range(w*h))
    assert regression(z)==0
    (OUT/f'{name}_mask-before.webp').write_bytes(raw)
    Image.frombytes('L',(w,h),bytes(protected)).save(OUT/f'{name}-trim-band.png')
    Image.frombytes('L',(w,h),bytes(255 if o[i]>=64 and o[i]-a[i]>=32 and not protected[i] else 0 for i in range(w*h))).save(OUT/f'{name}-regressions.png')
    row=dict(base=base,variant=variant or 'base',file=path,size=[w,h],regression_pixels_before=regression(a),regression_pixels_after=regression(z),restored_pixels=sum(x!=y for x,y in zip(a,z)),trim_unchanged=True,rgb_exact=True,sha256=hashlib.sha256(encoded.getvalue()).hexdigest());rows.append(row)
   print('PASS restore / trim protection',base,flush=True)
 (OUT/'mask-verification.json').write_text(json.dumps(dict(status='PASS',input=INPUT,files=rows),indent=2)+'\n')
if __name__=='__main__':main()
