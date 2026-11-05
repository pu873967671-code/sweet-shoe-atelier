import os,base64,sys,io,json,hashlib,contextlib,importlib.util,importlib.machinery
loader=importlib.machinery.SourceFileLoader('apicall','/usr/local/bin/apicall')
spec=importlib.util.spec_from_loader('apicall',loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
ST='/workspace/work/shoe-cg/dev/preview_state.json'
state=json.load(open(ST)) if os.path.exists(ST) else {}
def blob(b): return hashlib.sha1(b'blob %d\0'%len(b)+b).hexdigest()
root='/tmp/pvdist';ok=skip=0
for d,_,fs in os.walk(root):
    for f in sorted(fs):
        p=os.path.relpath(os.path.join(d,f),root);raw=open(os.path.join(d,f),'rb').read();h=blob(raw)
        if state.get(p)==h: skip+=1; continue
        args=['apicall','github','contents_put','owner=pu873967671-code','repo=vibe-coding',f'path=sweet-shoe-atelier/{p}',f'message=preview {p}','branch=sweet-shoe-preview',f'content={base64.b64encode(raw).decode()}']
        if p in state: args.append(f'sha={state[p]}')
        for a in range(3):
            sys.argv=args;out=io.StringIO()
            try:
                with contextlib.redirect_stdout(out): m.main()
            except SystemExit: pass
            if '"commit"' in out.getvalue(): state[p]=h; ok+=1; break
            print('retry',p,out.getvalue()[:200],flush=True)
            if 'does not match' in out.getvalue() or 'sha' in out.getvalue():
                sys.argv=['apicall','github','contents_get','owner=pu873967671-code','repo=vibe-coding',f'path=sweet-shoe-atelier/{p}','ref=sweet-shoe-preview'];o2=io.StringIO()
                try:
                    with contextlib.redirect_stdout(o2): m.main()
                except SystemExit: pass
                try:
                    rs=json.loads(o2.getvalue())['sha']
                    args=[x for x in args if not x.startswith('sha=')]+[f'sha={rs}']
                except Exception: pass
json.dump(state,open(ST,'w'),indent=0)
print('uploaded',ok,'unchanged',skip,flush=True)
print('URL https://raw.githack.com/pu873967671-code/vibe-coding/sweet-shoe-preview/sweet-shoe-atelier/index.html')
