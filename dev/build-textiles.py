#!/usr/bin/env python3
"""Draw the textile tiles for the UI theme (textile.css): lace trim, tulle net,
a satin bow and a lace corner rosette. Original vector art, CC0.
usage: python3 dev/build-textiles.py  -> assets/ui/textile/*.svg"""
import math
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / 'assets/ui/textile'
OUT.mkdir(parents=True, exist_ok=True)
LINE = '#9dd0bc'

def circle_path(cx, cy, r):
    return f'M{cx-r:.2f},{cy:.2f}a{r},{r} 0 1,0 {2*r},0a{r},{r} 0 1,0 {-2*r},0Z'

def lace():
    # 48 x 24 tile: a heading band with eyelets, one scallop with a flower and picots
    W, H, band, depth = 48, 24, 6, 15
    outer = f'M0,0H{W}V{band}'
    # scallop as an arc from (W,band) back to (0,band) dipping to band+depth
    r = (W*W/4 + depth*depth) / (2*depth)
    outer += f'A{r:.2f},{r:.2f} 0 0,1 0,{band}Z'
    holes = [circle_path(x, 3, 1.25) for x in (6, 18, 30, 42)]
    cx, cy = W/2, band + 7
    holes.append(circle_path(cx, cy, 1.6))
    for k in range(6):
        a = k * math.pi / 3
        holes.append(circle_path(cx + 4.1*math.cos(a), cy + 4.1*math.sin(a), 1.55))
    for x in (9, 39):
        holes.append(circle_path(x, band + 3.2, 1.0))
    picots = []
    for k in range(1, 10):
        t = k / 10
        ang = math.pi/2 + (t - .5) * 2 * math.asin((W/2)/r)
        px = W/2 - r*math.cos(ang) * (-1) if False else W/2 + r*math.sin((t-.5)*2*math.asin((W/2)/r))
        py = band + depth - r + r*math.cos((t-.5)*2*math.asin((W/2)/r))
        picots.append(f'<circle cx="{px:.2f}" cy="{py+1.6:.2f}" r="1.25" fill="#fff" stroke="{LINE}" stroke-width=".6"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'<path d="{outer}{"".join(holes)}" fill="#fff" fill-rule="evenodd" stroke="{LINE}" stroke-width=".8"/>'
           f'<path d="M0,{band}H{W}" stroke="{LINE}" stroke-width=".5" stroke-dasharray="1.5 2"/>'
           + ''.join(picots) + '</svg>')
    (OUT / 'lace-trim.svg').write_text(svg)

def tulle():
    # hexagonal net, 14 x 24.25 tile
    s = 7; h = s * math.sqrt(3)
    pts = f'M0,0 L{s},{h/2} L{s},{h*1.5} L0,{2*h} M{s},{h/2} L{2*s},0 M{s},{h*1.5} L{2*s},{2*h}'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{2*s}" height="{2*h:.2f}" viewBox="0 0 {2*s} {2*h:.2f}">'
           f'<path d="{pts}" fill="none" stroke="#8fc7b1" stroke-opacity=".38" stroke-width=".7"/></svg>')
    (OUT / 'tulle.svg').write_text(svg)

def bow():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="44" viewBox="0 0 64 44">'
           '<defs><linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b1e5d0"/><stop offset=".45" stop-color="#8cd6b8"/><stop offset="1" stop-color="#6ebc9d"/></linearGradient></defs>'
           '<path d="M30,20 C22,6 6,2 4,10 C2,18 8,26 30,22Z" fill="url(#s)" stroke="#5da789" stroke-width="1"/>'
           '<path d="M34,20 C42,6 58,2 60,10 C62,18 56,26 34,22Z" fill="url(#s)" stroke="#5da789" stroke-width="1"/>'
           '<path d="M28,23 L18,42 L24,39 L27,43 L31,24Z" fill="url(#s)" stroke="#5da789" stroke-width="1"/>'
           '<path d="M36,23 L46,42 L40,39 L37,43 L33,24Z" fill="url(#s)" stroke="#5da789" stroke-width="1"/>'
           '<path d="M10,11 C14,8 20,10 25,16" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="1.6" stroke-linecap="round"/>'
           '<path d="M54,11 C50,8 44,10 39,16" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="1.6" stroke-linecap="round"/>'
           '<rect x="27" y="16" width="10" height="10" rx="4" fill="#8cd6b8" stroke="#5da789" stroke-width="1"/>'
           '<path d="M29.5,18.5 h4" stroke="#fff" stroke-opacity=".8" stroke-width="1.4" stroke-linecap="round"/></svg>')
    (OUT / 'bow.svg').write_text(svg)

def rosette():
    # small round lace medallion for tab and tool buttons
    parts = []
    for k in range(16):
        a = 2*math.pi*k/16
        parts.append(f'<circle cx="{32+27*math.cos(a):.2f}" cy="{32+27*math.sin(a):.2f}" r="5" fill="#fff" stroke="{LINE}" stroke-width=".8"/>')
    holes = ''.join(f'<circle cx="{32+22*math.cos(2*math.pi*k/16+.2):.2f}" cy="{32+22*math.sin(2*math.pi*k/16+.2):.2f}" r="1.2" fill="{LINE}" fill-opacity=".55"/>' for k in range(16))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">' + ''.join(parts) +
           f'<circle cx="32" cy="32" r="27" fill="#fff" stroke="{LINE}" stroke-width=".8"/>' + holes +
           f'<circle cx="32" cy="32" r="18.5" fill="none" stroke="{LINE}" stroke-width=".6" stroke-dasharray="1.4 1.8"/></svg>')
    (OUT / 'rosette.svg').write_text(svg)

def tulle_fine():
    # real tulle is a tiny, barely visible diamond net
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="6" height="10" viewBox="0 0 6 10">'
           '<path d="M0,0 L3,5 L0,10 M6,0 L3,5 L6,10" fill="none" stroke="#7fb7a0" stroke-opacity=".16" stroke-width=".45"/></svg>')
    (OUT / 'tulle-fine.svg').write_text(svg)

def bow_fine():
    # a slim satin bow: soft folded loops, long fluttering tails
    g = ('<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#dbf5eb"/><stop offset=".5" stop-color="#93d4ba"/><stop offset="1" stop-color="#7ec0a5"/></linearGradient>'
         '<linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a2dec6"/><stop offset=".55" stop-color="#83c7ac"/><stop offset="1" stop-color="#70b297"/></linearGradient></defs>')
    loop_l = 'M47,26 C38,12 22,5 12,9 C5,12 6,22 13,27 C22,33 36,31 47,28Z'
    fold_l = 'M47,27 C38,22 26,20 17,23 C26,25 37,27 47,28Z'
    tail_l = 'M45,29 C40,38 33,47 24,58 C29,57 32,59 34,62 C39,50 45,40 49,30Z'
    def mirror(d):
        import re
        return re.sub(r'(-?\d+(?:\.\d+)?),', lambda m: f'{96-float(m.group(1)):g},', d)
    parts = [(loop_l, 'url(#a)'), (fold_l, '#77b79d'), (tail_l, 'url(#b)')]
    body = ''
    for d, f in parts:
        body += f'<path d="{d}" fill="{f}" stroke="#68a28b" stroke-width=".8" stroke-linejoin="round"/>'
        body += f'<path d="{mirror(d)}" fill="{f}" stroke="#68a28b" stroke-width=".8" stroke-linejoin="round"/>'
    body += '<path d="M15,13 C22,10 32,13 40,20" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="1.3" stroke-linecap="round"/>'
    body += '<path d="M81,13 C74,10 64,13 56,20" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="1.3" stroke-linecap="round"/>'
    body += '<ellipse cx="48" cy="27.5" rx="5.2" ry="6" fill="url(#a)" stroke="#68a28b" stroke-width=".8"/><path d="M46,24 q2,-1 4,0" stroke="#fff" stroke-opacity=".8" stroke-width="1" fill="none" stroke-linecap="round"/>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="64" viewBox="0 0 96 64">{g}{body}</svg>'
    (OUT / 'bow.svg').write_text(svg)

for f in (lace, tulle, tulle_fine, bow, rosette, bow_fine):
    f()
print('PASS', sorted(p.name for p in OUT.iterdir()))
