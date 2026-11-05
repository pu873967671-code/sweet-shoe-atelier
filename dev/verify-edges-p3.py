#!/usr/bin/env python3
"""Independent all-base rendered cream-shift scan and scope acceptance."""
import csv,hashlib,io,json,subprocess,tarfile
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/edges-p3'
def original(commit,name):return Image.open(io.BytesIO(subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT))).convert('RGBA')
def independent_trim(base):
 prefix=f'assets/shoe2d/{base}_'
 masks={n:original('c69f3e06',prefix+n+'.webp').getchannel('A') for n in ['insole','binding','sole']}
 collar=ImageChops.lighter(masks['insole'],masks['binding']).point(lambda x:255 if x>=64 else 0).filter(ImageFilter.MaxFilter(3))
 outsole=masks['sole'].point(lambda x:255 if x>=64 else 0).filter(ImageFilter.MaxFilter(7))
 painting=original('c69f3e06',prefix+'base.webp')
 colour=Image.frombytes('L',painting.size,bytes(255 if r-b>=20 and r-g>=6 else 0 for r,g,b,a in painting.getdata()))
 result=ImageChops.lighter(collar,ImageChops.multiply(outsole,colour))
 # Keep the independently traced neutral far footbed piping from edges-p.
 # It is absent from the older generic insole part masks on these two lasts.
 rails={
  'slingback':[(575,373),(580,368),(600,349),(620,329),(640,310),(660,294),(680,280),(700,267),(720,256),(740,248),(760,241),(770,238)],
  'bowsling':[(578,371),(580,368),(600,349),(620,329),(640,310),(660,294),(680,280),(700,267),(720,256),(733,250)],
 }
 if base in rails:
  rail=Image.new('L',painting.size);draw=ImageDraw.Draw(rail)
  draw.line(rails[base],fill=255,width=9,joint='curve')
  draw.line([(836,223),(850,222),(870,222),(890,223),(905,226),(916,230),(922,234)],fill=255,width=3,joint='curve')
  neutral=Image.frombytes('L',painting.size,bytes(255 if r>210 and r-b<18 and a>128 else 0 for r,g,b,a in painting.getdata()))
  rail=ImageChops.multiply(rail,neutral).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.35)).point(lambda v:255 if v else 0)
  result=ImageChops.lighter(result,rail)
 protect=Image.new('L',painting.size);d=ImageDraw.Draw(protect)
 if base=='loafer':d.polygon([(90,440),(90,350),(420,235),(485,235),(548,430),(548,455)],fill=255)
 if base=='bowmule':d.rectangle((200,300,555,450),fill=255)
 return ImageChops.subtract(result,protect)
def main():
 report=json.loads((OUT/'mask-counts.json').read_text());rows=[];allowed={f"assets/shoe2d/{r['base']}_upper.webp" for r in report['bases']}
 protected=0
 archive=subprocess.Popen(['git','archive','04531ea5','assets'],cwd=ROOT,stdout=subprocess.PIPE)
 with tarfile.open(fileobj=archive.stdout,mode='r|') as files:
  for entry in files:
   if not entry.isfile() or entry.name in allowed:continue
   raw=files.extractfile(entry).read()
   assert (ROOT/entry.name).read_bytes()==raw,entry.name
   protected+=1
 assert archive.wait()==0
 for row in report['bases']:
  base=row['base'];name=f'assets/shoe2d/{base}_upper.webp';a=original('c69f3e06',name);p=original('04531ea5',name);z=Image.open(ROOT/name).convert('RGBA');trim=independent_trim(base);t=trim.tobytes()
  assert trim.tobytes()==Image.open(OUT/f'{base}-true-trim.png').tobytes()
  assert a.size==p.size==z.size==(1024,640)
  assert a.convert('RGB').tobytes()==p.convert('RGB').tobytes()==z.convert('RGB').tobytes()
  aa=a.getchannel('A').tobytes();pp=p.getchannel('A').tobytes();zz=z.getchannel('A').tobytes()
  assert all(new==prior if allow else new>=old for old,prior,new,allow in zip(aa,pp,zz,t)),base
  assert all(new in (old,prior) for old,prior,new in zip(aa,pp,zz)),base
  # Narrow original contour edit allowance is retained, never expanded.
  solid=a.getchannel('A').point(lambda v:255 if v>=128 else 0)
  band=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(9)),solid.filter(ImageFilter.MinFilter(9)))
  assert ImageChops.multiply(ImageChops.difference(z.getchannel('A'),a.getchannel('A')),ImageChops.invert(band)).getbbox() is None,base
  painting=Image.open(ROOT/f'assets/shoe2d/{base}_base.webp').convert('RGBA').tobytes()
  for case in range(3):
   before=Image.open(OUT/f'{base}-{case}-before.png').convert('RGBA');after=Image.open(OUT/f'{base}-{case}-after.png').convert('RGBA');previous=Image.open(ROOT/f'dev/qa-out/edges-p/{base}-{case}-after.png').convert('RGBA')
   assert before.getchannel('A').tobytes()==after.getchannel('A').tobytes(),(base,case)
   # Render-space check: count changes moving toward the neutral original
   # painting outside semantic trim, rather than relying on alpha alone.
   old=before.tobytes()
   def shifts(render):
    count=0;rendered=render.tobytes()
    difference=ImageChops.difference(before,render)
    red,green,blue,_=difference.split()
    changed=ImageChops.lighter(ImageChops.lighter(red,green),blue).point(lambda v:255 if v>=3 else 0).tobytes()
    for i,change in enumerate(changed):
     if not change or t[i] or aa[i]<16 or old[4*i+3]<128:continue
     j=4*i
     if sum((old[j+c]-painting[j+c])**2-(rendered[j+c]-painting[j+c])**2 for c in range(3))>64:count+=1
    return count
   input_count=shifts(previous);output_count=shifts(after)
   rows.append(dict(base=base,case=case,edges_p_cream_shifts_outside_trim=input_count,final_cream_shifts_outside_trim=output_count,restored_mask_pixels=row['restored_dyed_pixels'],retained_trim_cleanup_pixels=row['retained_trim_cleanup_pixels']))
   print('SCAN',base,case,input_count,'->',output_count,flush=True)
 result=dict(status='PASS' if all(r['final_cream_shifts_outside_trim']==0 for r in rows) else 'FAIL',baseline='c69f3e06',protected_assets=protected,mask_rgb_and_size_exact=True,all_real_trim_cleanup_retained=True,rendered_alpha_exact=True,cases=rows)
 (OUT/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
 with (OUT/'counts.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 assert result['status']=='PASS',[(r['base'],r['case'],r['final_cream_shifts_outside_trim']) for r in rows if r['final_cream_shifts_outside_trim']]
 print('PASS 60 rendered colour/alpha scans;',protected,'protected assets; all source trim cleanup retained')
if __name__=='__main__':main()
