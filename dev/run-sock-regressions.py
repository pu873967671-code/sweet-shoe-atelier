#!/usr/bin/env python3
"""Run existing worn acceptance unchanged except redirecting evidence to dev/."""
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'qa'))
name=sys.argv[1]
assert name in ['worn-sprites-test.py','worn-socks-test.py','worn-socks-detail-test.py','worn-webkit-test.py']
folder=ROOT/'dev/qa-out/sock-repair/regression'/name.removesuffix('.py')

if '--current-contract' in sys.argv: folder=folder.parent/(folder.name+'-current-contract')
folder.mkdir(parents=True,exist_ok=True)
source=(ROOT/'qa'/name).read_text()
source=re.sub(r'^OUT=.*$',f"OUT=Path({str(folder)!r});OUT.mkdir(parents=True,exist_ok=True)",source,flags=re.M)
source=re.sub(r'^CONTACT=.*$',f"CONTACT=Path({str(folder/'contact.jpg')!r})",source,flags=re.M)
# Some incumbent runners contain a semicolon-separated output declaration.
source=source.replace("OUT=q.ROOT/'qa'/'worn-socks';OUT.mkdir(exist_ok=True)",f"OUT=Path({str(folder)!r});OUT.mkdir(parents=True,exist_ok=True)")
if '--current-contract' in sys.argv:
    # Original tests predate the registered ox offset and ASSET_V query strings.
    # Update only those test assumptions in memory; qa/ stays byte-exact.
    source=source.replace("geometry['reference']['x']==193", "geometry['reference']['x']==337")
    source=source.replace("blocked='**/assets/worn/flat_frill_sock.webp'", "blocked='**/assets/worn/flat_frill_sock.webp*'")
exec(compile(source,str(ROOT/'qa'/name),'exec'),{'__name__':'__main__','__file__':str(ROOT/'qa'/name)})
