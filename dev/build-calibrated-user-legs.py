#!/usr/bin/env python3
"""Per-last rigid anatomical seating; immutable source pixels and shoe cameras.

Calibration JSONs and traced front/rear collar masks are independent per style.
Only whole-leg similarity transforms are allowed. A near collar covers the foot;
far collar and dye masks must never cut holes in the instep.
"""
from pathlib import Path
import json, math, hashlib, argparse
import numpy as np
from PIL import Image
from user_leg_compression import save_user_derivative
ROOT=Path(__file__).resolve().parents[1]
W,H,OY=1024,2140,1500
STYLES=['stiletto6','kitten','studpump','maryjane','flat']

def similarity(p,q):
 p,q=np.asarray(p,float),np.asarray(q,float);u=p[1]-p[0];v=q[1]-q[0]
 scale=np.linalg.norm(v)/np.linalg.norm(u);theta=math.atan2(v[1],v[0])-math.atan2(u[1],u[0]);c,s=math.cos(theta),math.sin(theta)
 R=np.array([[c,-s],[s,c]]);t=q[0]-scale*R@p[0]
 return dict(scale=float(scale),degrees=float(math.degrees(theta)),tx=float(t[0]),ty=float(t[1]+OY))

def transform(src,p):
 s=p['scale'];r=math.radians(p['degrees']);c,n=math.cos(r),math.sin(r);tx,ty=p['tx'],p['ty']
 return src.transform((W,H),Image.Transform.AFFINE,(c/s,n/s,-(c*tx+n*ty)/s,-n/s,c/s,(n*tx-c*ty)/s),Image.Resampling.BICUBIC)

def build(style):
 path=ROOT/f'dev/fitting-calibration/{style}.json';cfg=json.loads(path.read_text());out=ROOT/'assets/fitting-rigid';ev=ROOT/f'qa/heel-collar-20261030/calibration/{style}';ev.mkdir(parents=True,exist_ok=True)
 report={'style':style,'calibration':str(path.relative_to(ROOT)),'placements':{},'sources':{},'exports':{}}
 for side in ['front','rear']:
  spec=cfg[side];source=ROOT/spec['source'];report['sources'][str(source.relative_to(ROOT))]=hashlib.sha256(source.read_bytes()).hexdigest()
  p=spec.get('placement_override') or similarity(spec['source_anchors'],spec['seat_anchors']);spec['placement']=p;report['placements'][side]=p
  raw=transform(Image.open(source).convert('RGBA'),p);a=np.array(raw)
  # Each side owns a separately saved native mask, traced on this last.
  trace=np.asarray(spec['collar_trace'],float)
  if spec.get('collar_interpolation')=='pchip':
   from scipy.interpolate import PchipInterpolator
   cut=PchipInterpolator(trace[:,0],trace[:,1])(np.arange(W))
  else:cut=np.interp(np.arange(W),trace[:,0],trace[:,1])
  coverage=np.clip((cut[None,:]-(np.arange(H)[:,None]-OY)+.5)/1.5,0,1)
  if spec.get('preserve_upper'):
   # The exact original outer upper covers toes even in front of the throat.
   # This is this last's source alpha, never a generic silhouette approximation.
   upper=np.asarray(Image.open(ROOT/f'assets/shoe2d/{style}_upper.webp').convert('RGBA'))[:,:,3]/255.
   coverage[OY:]*=1-upper
  if spec.get('forefoot_opening_limit'):
   # Closed pointed vamp: the distal toes can only show within its real
   # opening, never above the shoe's outer silhouette in front of the throat.
   insole=np.asarray(Image.open(ROOT/f'assets/shoe2d/{style}_insole.webp').convert('RGBA'))[:,:,3]/255.
   limit=spec['forefoot_opening_limit']
   coverage[OY+300:,:limit]*=insole[300:,:limit]
  a[:,:,3]=np.rint(a[:,:,3]*coverage).astype('uint8')
  Image.fromarray(np.rint(coverage[OY:]*255).astype('uint8')).save(ROOT/f'dev/fitting-calibration/{style}-{side}-collar.png')
  raw.save(ev/f'{side}-unoccluded.png')
  lum=(a[:,:,:3]*np.array([.2126,.7152,.0722])).sum(axis=2);volume=np.clip((lum-165)/85,0,1)
  for kind in ['skin','cloth','black']:
   b=a.copy()
   if kind=='cloth':
    if style in ['stiletto6','kitten']:
     # Preserve the returned painting's ankle, Achilles, instep and toe relief.
     # Lift the broad midtones into white while retaining source-painted
     # Achilles / heel / instep relief. Deep silver shadows obscured the
     # smaller rear foot; this soft shoulder keeps the cloth bright.
     light=207+47*np.clip((lum-178)/65,0,1)**.95
    else:light=221+32*volume**.85
    b[:,:,:3]=np.rint(np.stack([light,light,light],axis=2)).astype('uint8')
   elif kind=='black':
    light=19+45*volume**1.55;b[:,:,:3]=np.rint(np.stack([light,light*.95,light*1.1],axis=2)).astype('uint8')
   target=out/f'{style}_{side}_{kind}.webp';metrics=save_user_derivative(Image.fromarray(b),target,method=4);report['exports'][target.name]={'bytes':target.stat().st_size,**metrics}
 path.write_text(json.dumps(cfg,indent=2)+'\n');(ev/'provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(style,report['placements'])
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--styles',nargs='+',default=STYLES);args=ap.parse_args()
 for style in args.styles:build(style)
