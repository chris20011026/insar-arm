#!/usr/bin/env python3
"""Distribute exact upstream archives plus build recipes, patches and helper sources."""
import argparse,gzip,hashlib,io,json,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--cache',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists():raise SystemExit('Output already exists')
items=[s for s in json.loads((ROOT/'locks/sources.json').read_text()) if s['name'] in ['isce2','motif','snaphu']]
for s in items:
    source=a.cache/s['filename']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=s['sha256']:raise SystemExit('Source hash mismatch: '+s['name'])
def norm(info):
    info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
    return info
with a.output.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as t:
    for s in items:t.add(a.cache/s['filename'],arcname='upstream/'+s['filename'],filter=norm)
    for name in ['packaging','insar_arm','locks','LICENSE','THIRD_PARTY.md','install-binary.sh']:
        src=ROOT/name
        paths=[src] if src.is_file() else sorted(x for x in src.rglob('*') if x.is_file())
        for f in paths:
            if '__pycache__' in f.parts or f.suffix=='.pyc':continue
            t.add(f,arcname='build-tools/'+str(f.relative_to(ROOT)),filter=norm)
    content=(json.dumps(items,indent=2)+'\n').encode();info=tarfile.TarInfo('SOURCE-MANIFEST.json');info.size=len(content)
    t.addfile(norm(info),io.BytesIO(content))
print(a.output,hashlib.sha256(a.output.read_bytes()).hexdigest())
