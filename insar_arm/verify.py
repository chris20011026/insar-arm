#!/usr/bin/env python3
"""Validate this activated environment and write local JSON/HTML diagnostics."""
from __future__ import annotations
import argparse
from collections import Counter
import datetime
import html
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import time

PREFIX=Path(sys.prefix).resolve()
HERE=Path(__file__).resolve().parent


def cpu_types(data):
    magic=data[:4]
    if magic in (b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe'):
        return [struct.unpack_from('<I',data,4)[0]]
    if magic in (b'\xfe\xed\xfa\xcf',b'\xfe\xed\xfa\xce'):
        return [struct.unpack_from('>I',data,4)[0]]
    if magic in (b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf'):
        count=struct.unpack_from('>I',data,4)[0]
        if count>64:return []
        stride=32 if magic[-1]==0xbf else 20
        return [struct.unpack_from('>I',data,8+i*stride)[0] for i in range(count)]
    return []


def runtime_paths(load_commands):
    """LC_ID_DYLIB names are identities, not dependencies to open on disk."""
    command=''
    result=[]
    for line in load_commands.splitlines():
        line=line.strip()
        if line.startswith('cmd '):
            command=line[4:]
        elif command in ('LC_LOAD_DYLIB','LC_REEXPORT_DYLIB','LC_LOAD_UPWARD_DYLIB','LC_LOAD_WEAK_DYLIB') and line.startswith('name '):
            result.append((command,line[5:].split(' (offset ')[0]))
        elif command=='LC_RPATH' and line.startswith('path '):
            result.append((command,line[5:].split(' (offset ')[0]))
    return result


class Verify:
    def __init__(self,output):
        self.output=output
        self.output.mkdir(parents=True,exist_ok=True)
        self.results=[]
        self.env=os.environ.copy()
        self.env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
                        MPLCONFIGDIR=str(output/'matplotlib'),OPENBLAS_NUM_THREADS='1',
                        OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')

    def run(self,argv,cwd=None,allowed=(0,),help_text=False):
        result=subprocess.run(list(map(str,argv)),cwd=cwd,env=self.env,
                              capture_output=True,text=True,timeout=300)
        self.messages.append('$ '+' '.join(map(str,argv))+'\n'+result.stdout+result.stderr)
        if result.returncode not in allowed or 'Traceback (most recent call last)' in result.stderr:
            raise RuntimeError(f'Command failed ({result.returncode}): {argv[0]}\n'+result.stderr[-2000:])
        if help_text and not any(s in result.stdout.lower() for s in ('usage:','input file','configurable parameters')):
            raise RuntimeError('Expected help output was not produced.')
        return result.stdout

    def check(self,name,fn):
        self.messages=[]
        start=time.time()
        try:
            detail=fn()
            record=dict(name=name,status='PASS',details=detail)
        except Exception as exc:
            record=dict(name=name,status='FAIL',details=str(exc))
        record['seconds']=round(time.time()-start,2)
        record['log']=name+'.log'
        (self.output/record['log']).write_text('\n'.join(self.messages))
        self.results.append(record)
        print(f'{record["status"]:4} {name}',flush=True)

    def environment(self):
        assert platform.machine()=='arm64','Python is not running natively on ARM.'
        assert Path(os.environ.get('CONDA_PREFIX','')).resolve()==PREFIX,'Activate the target Conda environment first.'
        assert Path(os.environ.get('ISCE_STACK','')).resolve()==PREFIX/'share/isce2','Incorrect ISCE_STACK.'
        assert str(PREFIX/'share/isce2') in os.environ.get('PYTHONPATH','').split(os.pathsep),'Stack root missing from PYTHONPATH.'
        tools={name:shutil.which(name) for name in ('python','python3','mdx','snaphu','montage','convert','smallbaselineApp.py')}
        for name,path in tools.items():
            assert path and Path(path).is_relative_to(PREFIX),f'{name} points outside the selected environment: {path}'
        return tools

    def imports(self):
        modules=['numpy','scipy','osgeo.gdal','h5py','mintpy','cartopy','cvxopt','pyaps3',
                 'pysolid','pygrib','pyresample','asf_search','skimage','imagecodecs','isce',
                 'isceobj','stdproc','topsStack.Stack','stripmapStack.Stack',
                 'contrib.alos2proc.alos2proc','contrib.alos2proc_f.alos2proc_f',
                 'contrib.Snaphu.Snaphu','zerodop.topozero.topozero','zerodop.geo2rdr.geo2rdr',
                 'mroipac.formimage.formslc']
        # Isolate compiled extension crashes so the report can still be produced.
        script='import importlib,json; names='+repr(modules)+'; print(json.dumps({n:importlib.import_module(n).__file__ for n in names}))'
        output=self.run([sys.executable,'-c',script])
        loaded=json.loads(output.splitlines()[-1])
        assert all(Path(p).resolve().is_relative_to(PREFIX) for p in loaded.values()),'A module was loaded from another environment.'
        return loaded

    def entry(self,relative):
        with tempfile.TemporaryDirectory(prefix='insar-entry-') as folder:
            self.run([sys.executable,PREFIX/relative,'--help'],cwd=folder,
                     allowed=(0,1) if '/applications/' in relative else (0,),help_text=True)
        return 'CLI startup/help passed; full real-data workflow NOT validated.'

    def selectors(self):
        script='''
set -e
export PYTHONPATH=/tmp/insar-restore-test
export MAGICK_CONFIGURE_PATH=/tmp/insar-font-restore-test
source "$CONDA_PREFIX/etc/conda/activate.d/insar-arm.sh"
use_alosStack
test "$(command -v geocode.py)" = "$ISCE_STACK/alosStack/geocode.py"
test "$(command -v python3)" = "$CONDA_PREFIX/bin/python3"
use_topsStack
test "$(command -v stackSentinel.py)" = "$ISCE_STACK/topsStack/stackSentinel.py"
use_stripmapStack
test "$(command -v stackStripMap.py)" = "$ISCE_STACK/stripmapStack/stackStripMap.py"
use_mintpy
test "$(command -v geocode.py)" = "$CONDA_PREFIX/bin/geocode.py"
source "$CONDA_PREFIX/etc/conda/deactivate.d/insar-arm.sh"
test "$PYTHONPATH" = /tmp/insar-restore-test
test "$MAGICK_CONFIGURE_PATH" = /tmp/insar-font-restore-test
'''
        for shell,flags in [('/bin/bash',['--noprofile','--norc']),('/bin/zsh',['-f'])]:
            self.run([shell,*flags,'-c',script])
        return 'bash and zsh: stack selection, command collisions, and variable restoration passed.'

    def probe(self,name):
        with tempfile.TemporaryDirectory(prefix='insar-probe-') as folder:
            output=self.run([sys.executable,HERE/'probes.py',name],cwd=folder)
            if name=='plotting':
                shutil.copy2(Path(folder)/'check.png',self.output/'rendering-check.png')
            return output.splitlines()[-1] if output.strip() else 'Passed'

    def architecture(self):
        packages=[json.loads(p.read_text()) for p in (PREFIX/'conda-meta').glob('*.json')]
        subdirs=Counter(p.get('subdir','unknown') for p in packages)
        assert not (set(subdirs)-{'osx-arm64','noarch'}),f'Unexpected platforms: {subdirs}'
        binaries=[]
        seen=set()
        for path in PREFIX.rglob('*'):
            if not path.is_file():continue
            resolved=path.resolve()
            if resolved in seen:continue
            seen.add(resolved)
            with path.open('rb') as stream: arch=cpu_types(stream.read(4096))
            if arch:
                assert 0x0100000C in arch,f'Not ARM compatible: {path}'
                binaries.append(str(path))
        info=json.loads((PREFIX/'share/insar-arm/build-info.json').read_text())
        external=set()
        for i in range(0,len(binaries),100):
            result=subprocess.run(['/usr/bin/otool','-l',*binaries[i:i+100]],capture_output=True,text=True,check=True)
            for kind,path in runtime_paths(result.stdout):
                assert info['build_directory'] not in path,'A runtime load path refers to the disposable build directory.'
                if kind!='LC_RPATH' and path.startswith('/'):
                    if kind=='LC_LOAD_WEAK_DYLIB' and not Path(path).exists():continue
                    if not path.startswith((str(PREFIX)+'/', '/usr/lib/', '/System/Library/')):
                        external.add(path)
        for path in external:
            with open(path,'rb') as stream: arch=cpu_types(stream.read(4096))
            assert 0x0100000C in arch,f'External library not ARM compatible: {path}'
        return dict(conda_platforms=dict(subdirs),native_files=len(binaries),external_libraries=sorted(external))

    def report(self):
        passed=all(r['status']=='PASS' for r in self.results)
        report=dict(passed=passed,platform=platform.platform(),prefix=str(PREFIX),
                    created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=self.results,
                    scope='Installation, CLI startup and synthetic numerical tests. Full real-data sensor workflows are not certified.')
        (self.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        esc=html.escape
        rows=''.join(f'<tr><td><span class="{r["status"].lower()}">{r["status"]}</span></td><td><a href="{esc(r["log"])}">{esc(r["name"])}</a></td><td>{r["seconds"]} s</td><td><pre>{esc(json.dumps(r["details"],ensure_ascii=False,indent=2))}</pre></td></tr>' for r in self.results)
        document='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>InSAR ARM — Validation report</title><style>
body{font:16px system-ui,sans-serif;margin:40px auto;padding:0 24px;max-width:1180px;color:#20312e;background:#f6f8f7}h1{font-size:32px}p{line-height:1.6}.pass{color:#11633d;font-weight:700}.fail{color:#ad263d;font-weight:700}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;text-align:left;border-bottom:1px solid #dce4df;vertical-align:top}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px ui-monospace,monospace;max-height:180px;overflow:auto;margin:0}a{color:#17634a}.note{padding:16px;background:#e6eeea;border-radius:8px}img{image-rendering:pixelated;max-width:160px}</style>'''
        document+=f'<h1>InSAR ARM · {"Passed" if passed else "Needs attention"}</h1><p>{esc(str(PREFIX))}<br>{esc(platform.platform())}</p><p class="note">{esc(report["scope"])}<br>此報告驗證安裝、命令列啟動與小型數值運算，不代表所有衛星資料的完整研究流程均已驗證。報告含本機路徑，分享前請檢查。</p><table><thead><tr><th>Status</th><th>Check / log</th><th>Time</th><th>Details</th></tr></thead><tbody>{rows}</tbody></table><p><a href="report.json">Machine-readable JSON</a></p>'
        if (self.output/'rendering-check.png').exists():document+='<p>Rendering test:<br><img src="rendering-check.png" alt="Synthetic phase rendering"></p>'
        (self.output/'index.html').write_text(document+'</html>')
        print(f'Report: {self.output}/index.html',flush=True)
        return passed


def main():
    if not __debug__:
        print('Verification requires normal Python mode. Unset PYTHONOPTIMIZE and do not use -O.',file=sys.stderr)
        return 2
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path.home()/'Library/Logs/insar-arm'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    args=parser.parse_args()
    v=Verify(args.output.expanduser().resolve())
    v.check('environment',v.environment)
    v.check('imports',v.imports)
    apps='lib/python3.12/site-packages/isce/applications/'
    for name,path in [('topsApp',apps+'topsApp.py'),('alos2App',apps+'alos2App.py'),('stripmapApp',apps+'stripmapApp.py'),
                      ('topsStack','share/isce2/topsStack/stackSentinel.py'),('alosStack','share/isce2/alosStack/create_cmds.py'),
                      ('stripmapStack','share/isce2/stripmapStack/stackStripMap.py')]:
        v.check(name,lambda path=path:v.entry(path))
    v.check('shell-selectors',v.selectors)
    for name in ('generator','kernels','plotting','mintpy'):
        v.check(name,lambda name=name:v.probe(name))
    v.check('pip-dependencies',lambda:v.run([sys.executable,'-m','pip','check']))
    v.check('architecture',v.architecture)
    return 0 if v.report() else 1


if __name__=='__main__':
    sys.exit(main())
