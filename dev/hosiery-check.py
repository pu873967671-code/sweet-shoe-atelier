#!/usr/bin/env python3
"""Real Chromium old/new fitting acceptance; all evidence remains in dev/."""
import base64
import functools
import hashlib
import http.server
import io
import json
import re
import subprocess
import threading
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dev/qa-out/hosiery'
# Before hosiery-tune: the reviewed texture sample, not a moving HEAD.
BASELINE = '9a0744aa'
# Original cloth appearance, used to guard solid colour/brightness below.
LEGACY = '48cf2c6dcab7e11376d72ae255e818d2af51940c'


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


RENDER = '''async v=>{
 const c=document.createElement('canvas');c.width=v.w||1220;c.height=v.h||1000;
 await SweetShoe.Fitting2D.render(c,{heel:v.heel,color:'pink',material:'satin',
 pattern:'none',strap:'none',decoration:'none',charm:'none'},
 {sock:v.sock,color:v.colour||'cream',skin:v.skin},'salon',true);
 return {png:c.toDataURL().split(',')[1],data:{...c.dataset}};
}'''


def render(page, case):
    result = page.evaluate(RENDER, case)
    assert result['data']['renderer'] == 'worn-sprite' and result['data']['fallback'] == 'false', result['data']
    return Image.open(io.BytesIO(base64.b64decode(result['png']))).convert('RGBA'), result['data']


def equal(a, b):
    return a.tobytes() == b.tobytes()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    refs = json.loads(re.search(r'const SPRITES=(.*?);', (ROOT/'js/worn-sprites.js').read_text()).group(1))
    map_checks = {}
    for base in ['flat', 'stiletto9']:
        hose = Image.open(ROOT/f'assets/worn/{base}_hose.webp').convert('RGBA')
        legs = Image.open(ROOT/f'assets/worn/{base}_legs.webp').convert('RGBA')
        assert hose.size == legs.size == (refs[base]['w'], refs[base]['h'])
        assert equal(hose.getchannel('A'), legs.getchannel('A'))
        extrema = [hose.getchannel(c).getextrema() for c in 'RGB']
        assert all(hi > 100 and lo == 0 for lo, hi in extrema), extrema
        assert extrema[0] == (0, 255), 'R must span centre=0 to silhouette=255'
        # Check the actual front contour and centre on independent shin rows.
        for y in [250, 350, 450, 550]:
            xs = [x for x in range(legs.width) if legs.getpixel((x, y))[0] >= 207 and legs.getpixel((x, y))[3] >= 128]
            assert hose.getpixel((min(xs), y))[0] == 255
            assert hose.getpixel((max(xs), y))[0] == 255
            assert hose.getpixel((round((min(xs)+max(xs))/2), y))[0] <= 1
        assert hose.getchannel('B').crop((0, 0, hose.width, int(hose.height*.55))).getextrema()[1] == 0
        map_checks[base] = {'size': hose.size, 'channels': extrema, 'registered_alpha': True}
    old_js = subprocess.check_output(['git', 'show', f'{BASELINE}:js/worn-sprites.js'], cwd=ROOT)
    legacy_js = subprocess.check_output(['git', 'show', f'{LEGACY}:js/worn-sprites.js'], cwd=ROOT)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/'
    errors, cases, unchanged, solid_checks, density_checks = [], [], [], [], []
    states = [('sheer-cream', 'sheer', 'cream', None), ('sheer-nude', 'pantyhose', 'cream', None),
              ('blacksheer', 'blacksheer', 'black', None), ('opaque', 'opaque', 'cream', None),
              ('bare', 'none', 'cream', None), ('bridal', 'none', 'cream', '#8a5a3c'),
              ('bridal-sheer', 'sheer', 'cream', '#8a5a3c')]
    sheet = Image.new('RGB', (960, len(states)*2*470+50), '#f5efe9')
    pen = ImageDraw.Draw(sheet)
    pen.text((16, 12), 'Hosiery sample / OLD left - NEW right / full leg at 0.5x + shin crop at exactly 2x', fill='#382b28')
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            def page(old=False, missing=False, bad=False, legacy=False, neutral=False):
                p = browser.new_page(viewport={'width': 390, 'height': 844})
                p.on('pageerror', lambda error: errors.append(str(error)))
                p.route('https://**/*', lambda route: route.abort())
                if old or legacy:
                    p.route('**/js/worn-sprites.js*', lambda route: route.fulfill(body=legacy_js if legacy else old_js, content_type='application/javascript'))
                if missing:
                    p.route('**/*_hose.webp*', lambda route: route.abort())
                if bad:
                    p.route('**/*_hose.webp*', lambda route: route.fulfill(body=(ROOT/'assets/worn/flat_sole.webp').read_bytes(), content_type='image/webp'))
                if neutral:
                    def neutral_map(route):
                        base = Path(route.request.url.split('?')[0]).name.removesuffix('_hose.webp')
                        legs = Image.open(ROOT/f'assets/worn/{base}_legs.webp').convert('RGBA')
                        image = Image.new('RGBA', legs.size)
                        image.putalpha(legs.getchannel('A'))
                        stream = io.BytesIO()
                        image.save(stream, 'PNG')
                        route.fulfill(body=stream.getvalue(), content_type='image/png')
                    p.route('**/*_hose.webp*', neutral_map)
                p.goto(url, wait_until='domcontentloaded')
                p.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
                return p
            new, old, legacy = page(), page(old=True), page(legacy=True)
            for bi, base in enumerate(['flat', 'stiletto9']):
                for si, (name, sock, colour, skin) in enumerate(states):
                    case = {'heel': base, 'sock': sock, 'colour': colour, 'skin': skin}
                    before, meta = render(old, case)
                    after, _ = render(new, case)
                    same = equal(before, after)
                    assert same == (sock == 'none'), (case, same)
                    g = json.loads(meta['pairLayout'])
                    x, y = round(g['x']), round(g['y'])
                    w, h = refs[base]['w'], refs[base]['h']
                    for col, im in enumerate([before, after]):
                        row = bi*len(states)+si
                        left, top = col*480+10, row*470+40
                        full = im.crop((x, y, x+w, y+h)).resize((w//2, h//2), Image.Resampling.LANCZOS)
                        sheet.paste(full, (left, top+22), full)
                        # Front shin follows the painted mask's sloping centreline.
                        crop = im.crop((x+275, y+365, x+355, y+505)).resize((160, 280), Image.Resampling.NEAREST)
                        sheet.paste(crop, (left+290, top+75), crop)
                        pen.text((left, top), f'{base} / {name} / {"OLD" if col == 0 else "NEW"}', fill='#382b28')
                    if sock in ['sheer', 'pantyhose', 'blacksheer'] and skin is None:
                        # Use the independently painted front-shin silhouette.
                        legs = Image.open(ROOT/f'assets/worn/{base}_legs.webp').convert('RGBA')
                        xs = [xx for xx in range(w) if legs.getpixel((xx, 430))[0] >= 207 and legs.getpixel((xx, 430))[3] >= 128]
                        point = (x+round((min(xs)+max(xs))/2), y+430)
                        original, _ = render(legacy, case)
                        previous, tuned, incumbent = [im.getpixel(point)[:3] for im in [before, after, original]]
                        if sock == 'blacksheer':
                            assert sum(tuned) < sum(previous)-45, ('black shin still silver', tuned, previous)
                        else:
                            assert sum(abs(a-b) for a, b in zip(tuned, incumbent)) < sum(abs(a-b) for a, b in zip(previous, incumbent)), ('sheer lost incumbent colour', case)
                        density_checks.append({**case, 'previous_shin': previous, 'tuned_shin': tuned, 'incumbent_shin': incumbent})
                    cases.append({**case, 'bare_identical': same})
            sheet.save(OUT/'compare.jpg', quality=94)
            # With added edge/sheen disabled, every solid colour must reproduce
            # the original shader exactly. This catches a changed base tint.
            neutral = page(neutral=True)
            for base in ['flat', 'stiletto9']:
                for sock in ['opaque', 'knee', 'thigh']:
                    for colour in ['cream', 'white', 'pink', 'mint', 'black']:
                        case = {'heel': base, 'sock': sock, 'colour': colour}
                        a, _ = render(legacy, case)
                        b, _ = render(neutral, case)
                        assert equal(a, b), ('solid base colour/brightness changed', case)
                        solid_checks.append(case)
            # Every unaffected base: exact old/new shader, including solid and transparent cloth.
            for base in [b for b in refs if '_' not in b and b not in ['flat', 'stiletto9']]:
                for sock in ['sheer', 'opaque']:
                    case = {'heel': base, 'sock': sock}
                    a, _ = render(old, case)
                    b, _ = render(new, case)
                    assert equal(a, b), ('unmapped changed', case)
                    unchanged.append(case)
            # Short socks, skin tone, and fishnet retain exact pixels on the sample bases.
            for base in ['flat', 'stiletto9']:
                for sock in ['frill', 'lace', 'fishnet']:
                    case = {'heel': base, 'sock': sock, 'skin': '#8a5a3c'}
                    a, _ = render(old, case)
                    b, _ = render(new, case)
                    assert equal(a, b), ('sock changed', case)
                    unchanged.append(case)
                for sock in ['knee', 'thigh']:
                    case = {'heel': base, 'sock': sock, 'colour': 'black'}
                    a, _ = render(old, case)
                    b, _ = render(new, case)
                    assert not equal(a, b), ('solid sample unchanged', case)
                for w, h in [(390, 844), (1920, 1080)]:
                    render(new, {'heel': base, 'sock': 'blacksheer', 'w': w, 'h': h})
            missing = page(missing=True)
            bad = page(bad=True)
            for base in ['flat', 'stiletto9']:
                case = {'heel': base, 'sock': 'blacksheer'}
                a, _ = render(legacy, case)
                b, _ = render(missing, case)
                assert equal(a, b), 'missing-map fallback differs'
            a, _ = render(legacy, {'heel': 'stiletto9', 'sock': 'sheer'})
            b, _ = render(bad, {'heel': 'stiletto9', 'sock': 'sheer'})
            assert equal(a, b), 'wrong-size map fallback differs'
            restricted = page()
            restricted.evaluate('''()=>{CanvasRenderingContext2D.prototype.getImageData=function(){
              throw new DOMException('Read restricted for fallback acceptance','SecurityError');};}''')
            a, _ = render(legacy, {'heel': 'flat', 'sock': 'sheer'})
            b, _ = render(restricted, {'heel': 'flat', 'sock': 'sheer'})
            assert equal(a, b), 'read-restricted map fallback differs'
            info = new.evaluate('SweetShoe.WornSprites.info()')
            assert info['cacheEntries'] <= 8 and info['sourceEntries'] <= 8 and info['pending'] == 0, info
            browser.close()
        assert not errors, errors
        report = {'status': 'PASS', 'baseline': BASELINE, 'legacy_fallback_baseline': LEGACY, 'maps': map_checks, 'sample_cases': cases,
                  'solid_base_exact_cases': solid_checks, 'sheer_density_checks': density_checks,
                  'unchanged_cases': unchanged, 'missing_invalid_and_unreadable_map_fallback': 'PASS',
                  'phone_desktop': 'PASS', 'cache': info, 'page_errors': errors, 'external_https_blocked': True}
        (OUT/'acceptance.json').write_text(json.dumps(report, indent=2)+'\n')
        print(f'PASS: {len(cases)} comparison cases, {len(unchanged)} exact unchanged cases; missing/invalid map fallback and bounded cache.')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
