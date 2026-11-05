"""Rebuild only Mary Jane sock mattes from the pinned pre-task assets.

Reject disconnected codec reflections and cap coverage by the actual painted
green yarn at the shoe. Preserve dimensions and all unselected RGBA pixels.
"""
import io, json, subprocess
from collections import deque
from pathlib import Path
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[1]
BASE = '8e5d02d1f2f6fd6604741653af754e8f8e681d18'
OUT = ROOT / 'dev/qa-out/maryjane-specks'

def components(alpha, w, h, minimum=1000):
    seen = bytearray(v > 0 for v in alpha); keep = bytearray(w*h)
    for i in range(w*h):
        if not seen[i]: continue
        seen[i] = 0; queue = deque([i]); group = []
        while queue:
            j = queue.popleft(); group.append(j)
            for k in [j-w,j+w]+([j-1] if j%w else [])+([j+1] if j%w<w-1 else []):
                if 0 <= k < w*h and seen[k]: seen[k] = 0; queue.append(k)
        if len(group) >= minimum:
            for j in group: keep[j] = 255
    return keep

def main():
    OUT.mkdir(parents=True, exist_ok=True); report=[]
    for name in ['maryjane_frill', 'maryjane_lace']:
        path = f'assets/worn/{name}_sock.webp'
        raw = subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)
        (OUT/f'{name}-before.webp').write_bytes(raw)
        im = Image.open(io.BytesIO(raw)).convert('RGBA'); w,h=im.size
        src = list(Image.open(ROOT/f'assets/worn/{name}.webp').convert('RGBA').getdata())
        original = list(im.getdata()); alpha = im.getchannel('A').tobytes()
        keep = components(alpha,w,h)
        # Source green chroma supplies a soft material boundary, independent
        # of the selected runtime sock colour. No geometric resampling.
        coverage = bytes(round(255*max(0,min(1,(min(g-r,g-b)-2)/10))) for r,g,b,a in src)
        coverage = Image.frombytes('L',im.size,coverage).filter(ImageFilter.MedianFilter(3)).tobytes()
        dye = Image.open(ROOT/f'assets/worn/{name}_mask.webp').convert('RGBA').getchannel('A').tobytes()
        pixels=[]; changed=0; shade_changed=0
        for i,(r,g,b,a) in enumerate(original):
            aa=a if keep[i] or i//w<630 else 0
            if i//w>=630: aa=min(aa,coverage[i])
            # Remove the baked broad under-strap penumbra from cloth alone.
            # A neutral dyeable pixel above identifies the actual strap;
            # warm collar piping and cuff lace cannot trigger this selection.
            if 650<=i//w<=790 and aa>=128 and i+14*w<w*h and alpha[i+14*w]>=200:
                for distance in range(1,13):
                    j=i-distance*w
                    R,G,B,A=src[j]
                    if alpha[j]<32 and dye[j]>=64 and max(R,G,B)-min(R,G,B)<18:
                        donor=original[i+14*w][0]
                        value=round(donor*(.97 if distance<=2 else 1))
                        if value>r: r=g=b=value; shade_changed+=1
                        break
            pixels.append((r,g,b,aa)); changed+=aa!=a
        # Material clipping can disconnect a faint codec filament. Remove
        # those final islands too; preserve every original cuff/lace pixel.
        final=components(bytes(p[3] for p in pixels),w,h)
        pixels=[p if final[i] or i//w<630 else (*p[:3],0) for i,p in enumerate(pixels)]
        changed=sum(a[3]!=b[3] for a,b in zip(original,pixels))
        assert all(a==b for a,b in zip(original[:630*w],pixels[:630*w]))
        assert all(b[3]<=a[3] for a,b in zip(original,pixels))
        im.putdata(pixels); im.save(ROOT/path,lossless=True,exact=True)
        assert Image.open(ROOT/path).convert('RGBA').tobytes()==im.tobytes()
        report.append(dict(file=path,changed_alpha=changed,under_strap_shade_pixels=shade_changed,size=[w,h]))
    (OUT/'mask-verification.json').write_text(json.dumps(dict(baseline=BASE,files=report),indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
