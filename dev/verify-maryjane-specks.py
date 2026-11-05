"""Independent scope, mask-island and exact-rebuild acceptance checks."""
import ast, hashlib, importlib.util, io, json, subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dev/qa-out/maryjane-specks'
BASE='8e5d02d1f2f6fd6604741653af754e8f8e681d18'
ALLOWED={'assets/worn/maryjane_frill_sock.webp','assets/worn/maryjane_lace_sock.webp'}

def main():
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'--','assets','qa'],cwd=ROOT).decode().splitlines())
    assert changed==ALLOWED,changed
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ALLOWED}
    subprocess.run(['python3','dev/clean-maryjane-specks.py'],cwd=ROOT,check=True,capture_output=True)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ALLOWED}
    spec=importlib.util.spec_from_file_location('clean',ROOT/'dev/clean-maryjane-specks.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    rows=[]
    for path in sorted(ALLOWED):
        im=Image.open(ROOT/path).convert('RGBA');w,h=im.size
        before=Image.open(io.BytesIO(subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT))).convert('RGBA')
        assert im.size==before.size
        assert im.crop((0,0,w,630)).tobytes()==before.crop((0,0,w,630)).tobytes()
        alpha=im.getchannel('A').tobytes();connected=builder.components(alpha,w,h)
        assert all(not a or connected[i] or i//w<630 for i,a in enumerate(alpha))
        for i,(a,b) in enumerate(zip(before.getdata(),im.getdata())):
            assert b[3]<=a[3]
            if a[:3]!=b[:3]:
                assert 650<=i//w<=790 and b[0]>=a[0] and b[0]==b[1]==b[2]
        rows.append(dict(file=path,no_detached_shoe_islands=True,cuff_exact=True,same_dimensions=True))
    for path in ['dev/clean-maryjane-specks.py','dev/maryjane-specks-check.py','dev/maryjane-specks-ui.py','dev/verify-maryjane-specks.py']:
        ast.parse((ROOT/path).read_text())
    runtime=list((ROOT/'js').glob('*.js'))+[ROOT/'smoke-test.js']
    for path in runtime:subprocess.run(['node','--check',str(path)],check=True,capture_output=True)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    report=dict(status='PASS',assets_checked=len(subprocess.check_output(['git','ls-files','assets'],cwd=ROOT).splitlines()),allowed_changes=sorted(changed),qa_unchanged=True,byte_exact_rebuild=True,mask_checks=rows,python_parse=True,js_syntax_files=len(runtime),renderer_sha256=hashlib.sha256((ROOT/'js/worn-sprites.js').read_bytes()).hexdigest())
    (OUT/'protected-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS asset scope, exact rebuild, dimensions, cuff preservation, no shoe islands, syntax and whitespace')
if __name__=='__main__':main()
