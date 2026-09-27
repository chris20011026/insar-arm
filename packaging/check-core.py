#!/usr/bin/env python3
"""Run the core ISCE2/SNAPHU prototype checks in the selected environment."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('prefix', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
prefix = args.prefix.resolve()
root = Path(__file__).resolve().parents[1]
isce = prefix/'lib/python3.12/site-packages/isce'
if not (prefix/'conda-meta').is_dir() or not isce.exists():
    parser.error('Expected a Conda environment containing the ISCE2 prototype')
env = {k:v for k,v in os.environ.items() if not k.startswith(('PYTHON', 'DYLD_'))}
env.update(CONDA_PREFIX=str(prefix), ISCE_HOME=str(isce), ISCE_STACK=str(prefix/'share/isce2'),
           PATH=f'{prefix}/bin:{isce}/applications:/usr/bin:/bin:/usr/sbin:/sbin',
           PYTHONPATH=':'.join(map(str,[isce,isce/'applications',isce/'components',isce/'library',prefix/'share/isce2'])),
           PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
code = '''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from insar_arm.verify import Verify
v = Verify(Path(sys.argv[2]))
for app in ['topsApp.py', 'alos2App.py', 'stripmapApp.py']:
    relative = 'lib/python3.12/site-packages/isce/applications/' + app
    v.check(app, lambda relative=relative: v.entry(relative))
for relative in ['topsStack/stackSentinel.py', 'alosStack/create_cmds.py', 'stripmapStack/stackStripMap.py']:
    path = 'share/isce2/' + relative
    v.check(relative.split('/')[0], lambda path=path: v.entry(path))
for name in ['kernels', 'generator']:
    v.check(name, lambda name=name: v.probe(name))
raise SystemExit(0 if v.report() else 1)
'''
result = subprocess.run([str(prefix/'bin/python'), '-c', code, str(root), str(args.output.resolve())], env=env)
raise SystemExit(result.returncode)
