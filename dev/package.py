import os
#!/usr/bin/env python3
"""Create a deterministic CrazyGames upload using Python/Node standard libraries."""
from pathlib import Path
import argparse
import json
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT / 'dist/sweet-shoe-atelier-crazygames.zip')
args = parser.parse_args()
# The painted renderer has no WebGL dependency. Retain the experimental 3D
# sources locally for reference, but never upload them or their vendor/model payload.
archived_js = {'shoe3d.js', 'fitting3d.js'}
# Painted-2D product canvases no longer use the previous worn-leg renderer.
# app.boot explicitly omits these directories from ASSET_NAMES preloading;
# its only createShoeRenderer entry is hydrateCanvases -> Shoe2D.render.
# Retain all source paintings locally for reference, not in the runtime ZIP.
source_only_asset_dirs = {'models', 'angles', 'fabrics', 'legs', 'poses', 'tones'}
files = [ROOT / 'index.html', ROOT / 'style.css', *sorted(p for p in (ROOT / 'js').glob('*.js') if p.name not in archived_js)]
files += sorted(p for p in (ROOT / 'assets').rglob('*') if p.is_file() and p.relative_to(ROOT / 'assets').parts[0] not in source_only_asset_dirs and p.suffix.lower() in {'.webp', '.svg', '.ttf', '.txt', '.mp3', '.ogg', '.gltf', '.glb', '.bin', '.md'})
# Supervisor art drops can arrive before their runtime integration. Keep those
# source variants in the repository without shipping unused upload weight.
source_only = { 'assets/ui/logo_v2.webp', 'assets/ui/logo_v3.webp', 'assets/materials/lace_tile.webp'}
runtime_text = '\n'.join(p.read_text() for p in files if p.suffix in {'.js','.html','.css'})
for name in source_only:
    if name.removeprefix('assets/').removesuffix('.webp') in runtime_text:
        raise SystemExit('Integrated artwork must be removed from source_only: '+name)
files = [p for p in files if p.relative_to(ROOT).as_posix() not in source_only]
# Boutique previews now use mint_*.svg. Older room paintings remain available
# as development sources; retain only close_* images still named by the runtime
# while the fixed baked-platform cameras replace them.
retired_art = {
    *(p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets/decor').glob('d_*.webp')),
    *(p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets/scenes').glob('scene_*.webp') if not p.stem.endswith('_thumb')),
}
files = [p for p in files if p.relative_to(ROOT).as_posix() not in retired_art]
names = {p.relative_to(ROOT).as_posix() for p in files}
if 'assets/ornaments/puffy_satin.webp' not in names:
    raise SystemExit('Missing puffy satin artwork')
# Read the actual style registry, rather than duplicating an ever-growing list
# of silhouettes here. Fallback artwork is useful during a network failure,
# but a registered incomplete kit must never become a successful upload.
runtime_art = json.loads(subprocess.check_output(['node', '-e', r"""
const A=require('./game.js'), paths=new Set();
require('./js/item-assets.js');
require('./js/audio.js');
require('./js/fitting-rigid.js');
for(const path of A.SFX_FILES)paths.add(path);
// Match app.boot's preload exclusions: former model/worn-camera sources stay
// archived, but every active portrait, guide and material icon must ship.
for(const name of A.ASSET_NAMES.filter(name=>!/^shoe_|^(legs|tones|angles|poses|fabrics)\//.test(name)))paths.add(`assets/${name}.webp`);
for(const name of A.ITEM_ASSETS)paths.add(`assets/items/${name}.webp`);
const tintable=new Set(['strap_thin','strap_ribbon','strap_cross','decoration_small','decoration_big','charm_mini']);
for(const [heel] of A.opts.heel){
 paths.add(`assets/worn/${heel}.webp`);paths.add(`assets/worn/${heel}_mask.webp`);paths.add(`assets/worn/${heel}_sole.webp`);
 for(const [folder,parts] of Object.entries({shoe2d:['base','upper','binding','insole','sole','shadow','highlight'],fitting2d:['shoe','upper','shadow','highlight','occlusion','legs','hosiery']})){
  for(const part of parts)paths.add(`assets/${folder}/${heel}_${part}.webp`);
  const accessoryHeel=A.SHOE_STYLES[heel]?.accessoryBase||heel;
  for(const category of ['strap','decoration','charm'])for(const [value] of A.opts[category]){
   if(value==='none'||!A.supportsStyleOption(heel,category,value)||A.AccessoryRenderer?.handles(category,value))continue;
   const name=category+'_'+value,prefix=`assets/${folder}/accessories/${accessoryHeel}_${name}`;
   paths.add(prefix+'.webp');if(tintable.has(name))paths.add(prefix+'_tint.webp');
  }
 }
}
for(const heel of A.RigidFitting.styles)for(const which of ['front','rear'])for(const kind of ['skin','cloth','black'])paths.add(`assets/fitting-rigid/${heel}_${which}_${kind}.webp`);
paths.add('assets/fitting-rigid/maryjane_strap.webp');
for(const scene of A.Showcase.scenes){
 paths.add(`assets/${scene.closeImage}.webp`);
 paths.add(`assets/${scene.thumbnail||scene.image+(scene.id==='salon'?'':'_thumb')}.webp`);
}
for(const slot of A.Boutique.SLOTS)for(const level of [1,2])paths.add(A.Boutique.decorAsset(slot,level));
const cameraOwners=[...new Set(A.opts.heel.flatMap(([heel])=>[heel,A.SHOE_STYLES[heel]?.accessoryBase||heel]))];
console.log(JSON.stringify({paths:[...paths].sort(),cameraOwners,authoritativeRigid:A.RigidFitting.userStyles}));
"""], cwd=ROOT, text=True))
# Scene filenames are assembled at runtime, so the registry, rather than a
# substring search, decides whether an earlier camera remains in use.
retired_close = {
    p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets/scenes').glob('close_*.webp')
    if p.relative_to(ROOT).as_posix() not in runtime_art['paths']
    and p.relative_to(ROOT).as_posix() not in runtime_text
}
files = [p for p in files if p.relative_to(ROOT).as_posix() not in retired_close]
names = {p.relative_to(ROOT).as_posix() for p in files}
# Development exporters must not accidentally ship a candidate simply by
# copying its paintings into assets. Camera art belongs to a registered style
# or its explicitly selected ornament source. Keep the original shared fallback
# paintings, which have no style prefix, available for network recovery.
# Cross lacing now uses the shared code-native model in both cameras. Accept
# only these exact previously reviewed extraction sources, then omit their
# unused bytes below. A style prefix never grants ownership to other files.
retired_cross_art = {
    f'assets/{folder}/accessories/{heel}_strap_cross{suffix}.webp'
    for folder in ['shoe2d', 'fitting2d']
    for heel in ['flat', 'block', 'kitten', 'wedge', 'stiletto6', 'stiletto9', 'platform']
    for suffix in ['', '_tint']
}
shared_camera_art = {
    'assets/fitting2d/legs.webp',
    *(f'assets/shoe2d/accessories/{name}.webp' for name in
      ['bow', 'pearls', 'laces', 'maryjane', 'drop', 'crystal', 'flower', 'pearl']),
    # Preserve exact reviewed legacy pearl sources, without admitting experiments that
    # happen to use an accepted style's filename prefix.
    *(f'assets/{folder}/accessories/{heel}_strap_pearl.webp'
      for folder in ['shoe2d', 'fitting2d']
      for heel in ['flat', 'block', 'kitten', 'wedge', 'stiletto6', 'stiletto9', 'platform']),
}
allowed_camera_art = set(runtime_art['paths']) | shared_camera_art | retired_cross_art
unregistered_art = sorted(name for name in names
    if name.startswith(('assets/shoe2d/', 'assets/fitting2d/'))
    and name.endswith('.webp') and name not in allowed_camera_art)
if unregistered_art:
    raise SystemExit('Unregistered runtime camera artwork:\n' + '\n'.join(unregistered_art))
literal_art = set(re.findall(r'assets/[\w/.-]+\.(?:webp|svg|ttf|mp3|ogg)', runtime_text))
missing_art = sorted((set(runtime_art['paths']) | literal_art) - names)
if missing_art:
    raise SystemExit('Incomplete registered runtime artwork:\n' + '\n'.join(missing_art))
# Keep validating the complete registered source kit above, including the
# insole/sole extraction layers, before trimming the upload. Shoe2D.PARTS only
# decodes base/upper/shadow/highlight/binding: base already contains the fixed
# insole and sole. Its emergency fallback uses only shoe_{heel}_none, and app
# boot skips every old shoe_* painting. Baked-strap variants are source-only.
# Unknown camera files are still rejected above, never silently pruned.
source_only_layers = {
    name for name in runtime_art['paths']
    if re.fullmatch(r'assets/shoe2d/[^/]+_(?:insole|sole)\.webp', name)
}
source_only_layers.update(retired_cross_art)
# Returned user anatomy is authoritative even when a leg image is unavailable:
# RigidFitting.prepare returns grounded rigid shoes and retries those same legs,
# so these styles never request their retired fitting2d body cameras. Keep the
# complete source kits mandatory above; only remove unused upload bytes here.
authoritative_rigid = runtime_art['authoritativeRigid']
assert isinstance(authoritative_rigid, list) and authoritative_rigid, 'Missing authoritative rigid registry'
source_only_layers.update(
    f'assets/fitting2d/{heel}_{part}.webp'
    for heel in authoritative_rigid
    for part in ['shoe', 'upper', 'shadow', 'highlight', 'occlusion', 'legs', 'hosiery']
)
# The original shared leg painting predates the per-style worn camera. Every
# registered fitting now loads <heel>_legs directly. Pearl straps are drawn by
# AccessoryRenderer in the worn camera; unlike product legacy art, those worn
# extractions are never preloaded. Keep all originals locally for art history.
if subprocess.check_output(['node', '-e', r"""
const A=require('./game.js');
process.stdout.write(String(A.AccessoryRenderer.handles('strap','pearl','worn')));
"""], cwd=ROOT, text=True).strip() != 'true':
    raise SystemExit('Worn pearl extraction may be needed by runtime')
source_only_layers.add('assets/fitting2d/legs.webp')
source_only_layers.update(
    f'assets/fitting2d/accessories/{heel}_strap_pearl.webp'
    for heel in ['flat', 'block', 'kitten', 'wedge', 'stiletto6', 'stiletto9', 'platform']
)
source_only_layers.update(
    p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets').glob('shoe_*.webp')
    if re.fullmatch(r'shoe_(?:flat|block|kitten|wedge)_(?:thin|ribbon|cross|pearl)', p.stem)
)
if source_only_layers & literal_art:
    raise SystemExit('Retired artwork is referenced by runtime: '
                     + ', '.join(sorted(source_only_layers & literal_art)))
files = [p for p in files if p.relative_to(ROOT).as_posix() not in source_only_layers]
names = {p.relative_to(ROOT).as_posix() for p in files}
for ref in re.findall(r'(?:src|href)="([^"]+)"', (ROOT / 'index.html').read_text()):
    if ref.startswith('https://sdk.crazygames.com/'):
        continue
    if ref.split('?')[0] not in names:
        raise SystemExit('Missing packaged entry dependency: ' + ref)
# Validate the exact bytes that will be archived. Browser-only scripts such as
# app.js are not executed by the Node registry entry above; a syntax error in
# one must not replace an otherwise healthy upload.
payload = {path: path.read_bytes() for path in files}
for path in files:
    if path.suffix != '.js':
        continue
    checked = subprocess.run(['node', '--check'], input=payload[path], capture_output=True)
    if checked.returncode:
        raise SystemExit('Invalid packaged JavaScript: ' + path.relative_to(ROOT).as_posix()
                         + '\n' + checked.stderr.decode('utf-8', errors='replace'))
args.output.parent.mkdir(parents=True, exist_ok=True)
temporary = args.output.with_suffix('.tmp')
try:
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            entry = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), (2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, payload[path])
    with zipfile.ZipFile(temporary) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == names
    if temporary.stat().st_size >= 20 * 1024 * 1024 and not os.environ.get('PREVIEW_NO_BUDGET'):
        raise SystemExit("Upload exceeds the 20 MiB budget: %.2f MiB" % (temporary.stat().st_size/1048576))
    temporary.replace(args.output)
finally:
    temporary.unlink(missing_ok=True)
print(f'PASS: {len(files)} runtime files, {args.output.stat().st_size / 1024 / 1024:.2f} MiB → {args.output}')
