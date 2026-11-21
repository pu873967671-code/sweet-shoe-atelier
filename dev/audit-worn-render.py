#!/usr/bin/env python3
"""Render-level audit: count neutral satin pixels that still show the undyed
painting in Chromium renders (worn.js output). Run from the repo root:
  python3 dev/audit-worn-render.py <render dir> <log>
Piping (authored collar no-dye / cream), ornaments and cream paint are excluded."""
import importlib.util,json,re,sys,numpy as np
from PIL import Image
S=sys.argv[1]
spec=importlib.util.spec_from_file_location('rep','dev/repair-worn-mask-coverage.py');rep=importlib.util.module_from_spec(spec);spec.loader.exec_module(rep)
lay={m.group(1):json.loads(m.group(2)) for m in (re.match(r'(\S+) true (\{.*\})',x) for x in open(S+'/'+sys.argv[2])) if m}
def analyse(name):
    base,_,sock,_=name.split('-');v=base if sock in('none','sheer','opaque') else base+'_'+sock;l=lay[name]
    R=np.asarray(Image.open(f'{S}/after/{name}.png').convert('RGBA')).astype(int)[0:l['h'],l['x']:l['x']+l['w']]
    P=np.asarray(Image.open(rep.WORN/f'{v}.webp').convert('RGBA')).astype(int)
    dx,dy=rep.SPRITES[base]['x']-rep.SPRITES[v]['x'],rep.SPRITES[base]['y']-rep.SPRITES[v]['y']
    L=rep.aligned(rep.current(f'{base}_legs'),dx,dy,P.shape)[...,3]
    K=rep.current(f'{v}_sock');K=K[...,3] if K is not None else np.zeros(P.shape[:2],int)
    N=rep.aligned(rep.current(f'{base}_sole'),dx,dy,P.shape)[...,3];M=rep.current(f'{v}_mask')[...,3];C=rep.current(f'{v}_clear')[...,3]
    s0=rep.aligned(rep.baseline(f'{base}_sole'),dx,dy,P.shape)[...,3]>=128
    r,g,b,a=[P[...,i] for i in range(4)];pl=r*.299+g*.587+b*.114;sp=P[...,:3].max(-1)-P[...,:3].min(-1);rl=R[...,:3]@np.array([.299,.587,.114])
    shoe=(R[...,3]>200)&(a>200)&(L<64)&(K<64)
    undyed=shoe&(sp<=24)&(pl>=120)&(rl>=pl-25)
    orn=rep.dilate(rep.thick_parts(s0&(sp<=24)&(pl>=150),rep.THICK),3)
    band=rep.dilate(L>=128,rep.COLLAR)&(L<128) if rep.piping_width(base) else np.zeros(P.shape[:2],bool)
    piping=undyed&band&(s0|(rep.box_mean(g-b,2)>=rep.CREAM_LO+2))
    satin=undyed&~piping&~orn&(g-b<=rep.CREAM_LO)
    return dict(R=R,P=P,satin=satin,M=M,N=N,L=L,K=K,C=C,orn=orn)
if __name__=='__main__' and len(sys.argv)>3:
    for name in sys.argv[3].split(','):
        d=analyse(name);sa=d['satin']
        from collections import Counter
        c=Counter()
        for y,x in zip(*np.nonzero(sa)):
            c[('M>=128' if d['M'][y,x]>=128 else 'M<128','N>=128' if d['N'][y,x]>=128 else ('N part' if d['N'][y,x]>0 else 'N0'),'C' if d['C'][y,x]>=128 else '')]+=1
        print(name,int(sa.sum()),c.most_common(6))
        if len(sys.argv)>4:
            arr=d['R'].astype(np.uint8).copy();bg=Image.new('RGBA',(arr.shape[1],arr.shape[0]),(150,170,165,255));bg.alpha_composite(Image.fromarray(arr));arr=np.asarray(bg).copy()
            arr[rep.dilate(sa,1)]=[255,0,255,255]
            y0=int(arr.shape[0]*.6);Image.fromarray(arr).convert('RGB').crop((0,y0,arr.shape[1],arr.shape[0])).save(sys.argv[4]+name+'.png')

def total(log):
    names=[n for n in lay];tot=0;worst=[]
    for n in sorted(names):
        d=analyse(n);k=int(d['satin'].sum());tot+=k;worst.append((k,n))
    worst.sort(reverse=True);print('TOTAL',tot,'over',len(names),'renders; worst',worst[:5])
if len(sys.argv)==3: total(sys.argv[2])
