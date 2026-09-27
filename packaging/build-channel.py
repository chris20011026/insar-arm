#!/usr/bin/env python3
"""Assemble only explicitly selected packages into a publishable Conda channel."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,required=True)
p.add_argument('packages',type=Path,nargs='+')
a=p.parse_args()
out=a.output.resolve()
if out.exists():
    raise SystemExit('Choose a new channel directory; existing channels are not overwritten.')
(out/'osx-arm64').mkdir(parents=True)
(out/'noarch').mkdir()
records=[]
for package in a.packages:
    if package.suffix!='.conda' or not package.is_file():
        raise SystemExit('Expected a .conda package: '+str(package))
    dest=out/'osx-arm64'/package.name
    if dest.exists():raise SystemExit('Duplicate package filename')
    shutil.copy2(package,dest)
    records.append(dict(file='osx-arm64/'+dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),bytes=dest.stat().st_size))
subprocess.run([sys.executable,'-m','conda_index',str(out)],check=True)
# Index caches and build metadata are not needed by channel clients.
for cache in out.rglob('.cache'):
    if cache.is_dir():shutil.rmtree(cache)
(out/'artifacts.json').write_text(json.dumps(records,indent=2)+'\n')
(out/'SHA256SUMS').write_text(''.join(f"{r['sha256']}  {r['file']}\n" for r in records))
(out/'.nojekyll').touch()
(out/'index.html').write_text('''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>InSAR ARM — Conda beta</title><style>body{font:18px system-ui;max-width:850px;margin:60px auto;padding:24px;line-height:1.7;color:#173e38;background:#f5f8f6}pre{white-space:pre-wrap;background:white;padding:20px}a{color:#14735f}</style><h1>InSAR ARM · 0.2.0 beta 1</h1><p>Apple Silicon Mac 的 InSAR Conda 環境。預先編譯 ISCE2、Motif 與 SNAPHU，搭配 conda-forge 的 MintPy 及其他套件。</p><p><strong>公開測試版：</strong>macOS 14.5+、原生 ARM Conda。已在同一台 Mac 的多個全新環境驗證；其他 Mac 與真實衛星資料的完整流程仍待驗證。含 CS2 的元件有非商業用途限制，請閱讀來源包與第三方授權。</p><p><a href="https://github.com/chris20011026/insar-arm/releases/tag/v0.2.0-beta.1">下載、固定版本安裝方式與來源包</a></p><p>也可讓 Conda 解析此版本的相依套件：</p><pre>conda create -n insar_arm_beta --strict-channel-priority --override-channels -c https://chris20011026.github.io/insar-arm -c conda-forge insar-arm=0.2.0b1
conda activate insar_arm_beta
insar-check</pre><p>請使用全新環境名稱。需要與發布測試完全相同的依賴版本時，使用 Release 的固定版本安裝工具。</p><p><a href="artifacts.json">套件清單</a> · <a href="SHA256SUMS">SHA256</a> · <a href="https://github.com/chris20011026/insar-arm">GitHub</a></p></html>''')
print(out)
