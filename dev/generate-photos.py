#!/usr/bin/env python3
"""Generate the fitting-card photo set with GPT Image (OpenAI) or Gemini.

Reads every prompt, shoe shape and sock style from docs/photo-generation-prompts.md
(the single source), then runs the workflow described there:

  1. master.png            Prompt A (text only); reused if it already exists
  2. <shape>__none.png     Prompt B, an edit of master.png, one per shoe shape
  3. <shape>__<sock>.png   Prompt C, an edit of that shape's bare-leg photo
  4. <name>__mask.png      Prompt D, optional (--masks)

Existing files are skipped, so a run can be stopped and resumed, and a photo is
redone simply by deleting it. Only the Python standard library is used.

Keys come from the environment, never from this file:
  OPENAI_API_KEY   for --provider openai  (model gpt-image-1, 1024x1536)
  GEMINI_API_KEY   for --provider gemini  (model gemini-2.5-flash-image, 3:4)
  --provider codex needs no key: it runs Codex CLI's built-in image generator with
  the ChatGPT login (session model from CODEX_MODEL, default gpt-6.1-terra).

Examples:
  python3 dev/generate-photos.py --provider openai --test        # the 9-photo test batch
  python3 dev/generate-photos.py --provider gemini --shapes flat,maryjane --socks none,fishnet
  python3 dev/generate-photos.py --provider openai               # everything (200 photos)
  python3 dev/generate-photos.py --dry-run --test                # print the prompts only
"""
import argparse, base64, json, os, re, subprocess, sys, time, uuid
import urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/photo-generation-prompts.md'
TEST_SHAPES, TEST_SOCKS = ['flat', 'maryjane', 'stiletto9'], ['none', 'sheer', 'fishnet']


def load_doc():
    text = DOC.read_text(encoding='utf-8')
    prompts = {}
    for letter in 'ABCD':
        m = re.search(r'## Prompt ' + letter + r'\b.*?```\n(.*?)```', text, re.S)
        prompts[letter] = m.group(1).strip()
    def table(after):
        part = text.split(after, 1)[1]
        rows = {}
        for line in part.splitlines()[2:]:
            if not line.startswith('|'):
                if rows:
                    break
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) >= 3 and cells[0].startswith('`'):
                rows[cells[0].strip('`')] = cells[2]
        return rows
    return prompts, table('### Shape descriptions'), table('### Sock descriptions')


# ── providers ────────────────────────────────────────────────────────────
def http(req, retries=4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'replace')[:600]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(8 * (attempt + 1)); continue
            raise SystemExit(f'HTTP {e.code}: {body}')
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(8 * (attempt + 1)); continue
            raise SystemExit(f'Network error: {e}')


def openai_image(prompt, ref=None):
    key = os.environ.get('OPENAI_API_KEY') or sys.exit('Set OPENAI_API_KEY first.')
    head = {'Authorization': 'Bearer ' + key}
    if ref is None:
        body = json.dumps({'model': 'gpt-image-1', 'prompt': prompt, 'size': '1024x1536', 'quality': 'high', 'n': 1}).encode()
        req = urllib.request.Request('https://api.openai.com/v1/images/generations', body, {**head, 'Content-Type': 'application/json'})
    else:
        b = uuid.uuid4().hex; parts = []
        for name, value in [('model', 'gpt-image-1'), ('prompt', prompt), ('size', '1024x1536'), ('quality', 'high'), ('n', '1')]:
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="image[]"; filename="{ref.name}"\r\nContent-Type: image/png\r\n\r\n'.encode() + ref.read_bytes() + b'\r\n')
        parts.append(f'--{b}--\r\n'.encode())
        req = urllib.request.Request('https://api.openai.com/v1/images/edits', b''.join(parts), {**head, 'Content-Type': 'multipart/form-data; boundary=' + b})
    return base64.b64decode(http(req)['data'][0]['b64_json'])


def gemini_image(prompt, ref=None):
    key = os.environ.get('GEMINI_API_KEY') or sys.exit('Set GEMINI_API_KEY first.')
    parts = [{'text': prompt}]
    if ref is not None:
        parts.append({'inline_data': {'mime_type': 'image/png', 'data': base64.b64encode(ref.read_bytes()).decode()}})
    body = json.dumps({'contents': [{'parts': parts}],
                       'generationConfig': {'responseModalities': ['IMAGE'], 'imageConfig': {'aspectRatio': '3:4'}}}).encode()
    url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent'
    out = http(urllib.request.Request(url, body, {'Content-Type': 'application/json', 'x-goog-api-key': key}))
    for part in out.get('candidates', [{}])[0].get('content', {}).get('parts', []):
        data = part.get('inlineData') or part.get('inline_data')
        if data:
            return base64.b64decode(data['data'])
    raise SystemExit('Gemini returned no image: ' + json.dumps(out)[:600])


def codex_image(prompt, ref=None):
    """Codex CLI's built-in image generator (ChatGPT login, no API key)."""
    jobs = ROOT / 'photos' / '_jobs'; jobs.mkdir(parents=True, exist_ok=True)
    job = uuid.uuid4().hex[:10]
    pfile, ofile = jobs / f'{job}.txt', jobs / f'{job}.png'
    pfile.write_text(prompt + '\n', encoding='utf-8')
    rel = lambda p: p.relative_to(ROOT).as_posix()
    ask = (f'Read {rel(pfile)}. Use the built-in $imagegen image generator with the exact text of that file '
           'as the prompt, unchanged, in portrait orientation'
           + (', as an edit of the attached image: pass the attached image to the generator as the image to edit, '
              'so the result is the same picture with only the requested change' if ref else '')
           + f'. Generate one image and save the PNG to {rel(ofile)}, copied exactly as generated: do not crop, '
           'resize or re-encode it. Do not call the OpenAI image API. Do not modify any other file.')
    cmd = ['codex.cmd' if os.name == 'nt' else 'codex', 'exec', '-m', os.environ.get('CODEX_MODEL', 'gpt-6.1-terra'),
           '--sandbox', 'workspace-write', ask]
    if ref is not None:
        cmd += ['-i', str(ref)]
    run = subprocess.run(cmd, cwd=ROOT, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if run.returncode or not ofile.exists():
        raise SystemExit(f'Codex made no image (exit {run.returncode}):\n' + (run.stdout + run.stderr)[-1200:])
    data = ofile.read_bytes(); ofile.unlink(); pfile.unlink()
    return data


# ── workflow ─────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--provider', choices=['openai', 'gemini', 'codex'], default='openai')
    ap.add_argument('--shapes', help='comma-separated shape ids (default: all)')
    ap.add_argument('--socks', help='comma-separated sock ids (default: all)')
    ap.add_argument('--test', action='store_true', help='the 9-photo test batch')
    ap.add_argument('--masks', action='store_true', help='also make Prompt D masks')
    ap.add_argument('--out', default=str(ROOT / 'photos'), help='output folder (default: photos/)')
    ap.add_argument('--dry-run', action='store_true', help='print what would be generated')
    a = ap.parse_args()

    prompts, shapes, socks = load_doc()
    pick = lambda arg, table, test: (test if a.test else arg.split(',') if arg else list(table))
    want_shapes, want_socks = pick(a.shapes, shapes, TEST_SHAPES), pick(a.socks, socks, TEST_SOCKS)
    for s in want_shapes:
        if s not in shapes: sys.exit(f'Unknown shape "{s}". Known: {", ".join(shapes)}')
    for s in want_socks:
        if s not in socks: sys.exit(f'Unknown sock "{s}". Known: {", ".join(socks)}')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    make = {'openai': openai_image, 'gemini': gemini_image, 'codex': codex_image}[a.provider]

    def step(path, prompt, ref=None):
        if path.exists():
            print('skip  ', path.name); return
        print('make  ', path.name, f'(edit of {ref.name})' if ref else '')
        if a.dry_run:
            print('      ', prompt.replace('\n', ' ')[:220], '…'); return
        path.write_bytes(make(prompt, ref)); print('saved ', path)

    master = out / 'master.png'
    step(master, prompts['A'])
    for shape in want_shapes:
        bare = out / f'{shape}__none.png'
        step(bare, prompts['B'].replace('{SHAPE DESCRIPTION}', shapes[shape]), master)
        for sock in want_socks:
            if sock == 'none':
                continue
            step(out / f'{shape}__{sock}.png', prompts['C'].replace('{SOCK DESCRIPTION}', socks[sock]), bare)
        if a.masks:
            for sock in want_socks:
                photo = out / f'{shape}__{sock}.png'
                if photo.exists() or a.dry_run:
                    step(out / f'{shape}__{sock}__mask.png', prompts['D'], photo)
    print('done. Photos are in', out)


if __name__ == '__main__':
    main()
