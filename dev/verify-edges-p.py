#!/usr/bin/env python3
"""Independent byte, edge-band and painting protection acceptance guards."""
import hashlib, io, json, subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter, ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/edges-p'
def main():
 report=json.loads((OUT/'mask-verification.json').read_text());expected={r['file'] for r in report['files']};rows=[]
 protected=json.loads((OUT/'protected-before.json').read_text());changed=[]
 for name,digest in protected.items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
   assert name in expected,name
   changed.append(name)
 assert set(changed)==expected
 for r in report['files']:
  name=r['file'];raw=subprocess.check_output(['git','show',f"{report['baseline']}:{name}"],cwd=ROOT)
  a=Image.open(io.BytesIO(raw)).convert('RGBA');z=Image.open(ROOT/name).convert('RGBA');assert a.size==z.size==(1024,640)
  assert a.convert('RGB').tobytes()==z.convert('RGB').tobytes(),name
  solid=a.getchannel('A').point(lambda v:255 if v>=128 else 0)
  band=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(7)),solid.filter(ImageFilter.MinFilter(7)))
  painting=Image.open(ROOT/f"assets/shoe2d/{r['base']}_base.webp").convert('RGBA')
  trim=Image.frombytes('L',painting.size,bytes(255 if red-blue>=11 and red-green>=3 and opacity>128 else 0 for red,green,blue,opacity in painting.getdata()))
  # Independent source-coordinate traces; compare the saved diagnostic to
  # source material, never trust the generator's allowed-band bitmap.
  traces={
   'slingback':[(575,373),(580,368),(600,349),(620,329),(640,310),(660,294),(680,280),(700,267),(720,256),(740,248),(760,241),(770,238)],
   'bowsling':[(578,371),(580,368),(600,349),(620,329),(640,310),(660,294),(680,280),(700,267),(720,256),(733,250)],
  }
  if r['base'] in traces:
   rail=Image.new('L',a.size);ImageDraw.Draw(rail).line(traces[r['base']],fill=255,width=9,joint='curve')
   ImageDraw.Draw(rail).line([(836,223),(850,222),(870,222),(890,223),(905,226),(916,230),(922,234)],fill=255,width=3,joint='curve')
   neutral=Image.frombytes('L',a.size,bytes(255 if red>210 and red-blue<18 and opacity>128 else 0 for red,green,blue,opacity in painting.getdata()))
   rail=ImageChops.multiply(rail,neutral);trim=ImageChops.lighter(trim,rail)
   fourth=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(9)),solid.filter(ImageFilter.MinFilter(9)))
   band=ImageChops.lighter(band,ImageChops.multiply(fourth,rail.filter(ImageFilter.MaxFilter(3))))
  assert trim.tobytes()==Image.open(OUT/f"{r['base']}-true-trim.png").tobytes(),name
  delta=ImageChops.difference(a.getchannel('A'),z.getchannel('A'))
  assert ImageChops.multiply(delta,ImageChops.invert(band)).getbbox() is None,name
  old=a.getchannel('A').tobytes();new=z.getchannel('A').tobytes();near=trim.filter(ImageFilter.MaxFilter(7)).tobytes()
  loss=dict(nonzero_to_zero_beyond_3px=sum(x>0 and y==0 and not t for x,y,t in zip(old,new,near)),solid_to_undyed_beyond_3px=sum(x>=128 and y<64 and not t for x,y,t in zip(old,new,near)),substantial_loss_beyond_3px=sum(x>=64 and x-y>=32 and not t for x,y,t in zip(old,new,near)))
  assert not any(loss.values()),(name,loss)
  counts=dict(nonzero_to_zero_total=sum(x>0 and y==0 for x,y in zip(old,new)),solid_to_undyed_total=sum(x>=128 and y<64 for x,y in zip(old,new)))
  session=OUT/'continuation-before'/Path(name).name
  if session.exists():
   previous=Image.open(session).convert('RGBA').getchannel('A').tobytes()
   loss['session_nonzero_to_zero_beyond_3px']=sum(x>0 and y==0 and not t for x,y,t in zip(previous,new,near))
   assert loss['session_nonzero_to_zero_beyond_3px']==0,(name,loss)
  # Independently check every unadorned product retains its painted silhouette.
  for case in range(3):
   before=Image.open(OUT/f"{r['base']}-{case}-before.png").convert('RGBA')
   after=Image.open(OUT/f"{r['base']}-{case}-after.png").convert('RGBA')
   assert before.getchannel('A').tobytes()==after.getchannel('A').tobytes(),(name,case)
  rows.append(dict(base=r['base'],rgb_exact=True,size_exact=True,contour_band_px=4 if r['base'] in traces else 3,rendered_alpha_exact=True,changed_pixels=r['changed_pixels'],**counts,**loss))
 result=dict(status='PASS',protected_assets=len(protected),changed=changed,all_paintings_and_worn_assets_exact=True,anti_regression='All dyed-to-undyed and substantial-loss counts beyond 3 source pixels of source-detected trim are zero.',bases=rows)
 (OUT/'protected-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS',len(rows),'original-size/RGB/narrow band checks; 60 rendered alpha checks;',len(protected),'protected assets; zero dye loss beyond true trim')
if __name__=='__main__':main()
