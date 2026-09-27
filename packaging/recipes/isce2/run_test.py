from pathlib import Path
import subprocess
import numpy as np
import isce
from contrib.alos2proc.alos2proc import look

rng = np.random.default_rng(847)
a = (rng.random((64, 96)) + 1j*rng.random((64, 96))).astype(np.complex64)
a.tofile('input.slc')
look('input.slc', 'looks.slc', 96, 3, 4, ft=4, avg=1)
actual = np.fromfile('looks.slc', np.complex64).reshape(16, 32)
expected = a.astype(np.complex128).reshape(16, 4, 32, 3).mean(axis=(1, 3))
np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-7)
print('Multilook maximum error:', float(np.max(np.abs(actual-expected))))
(np.arange(256, dtype=np.float32)/256).tofile('phase')
subprocess.run(['mdx', 'phase', '-s', '16', '-r4', '-cmap', 'cmy',
                '-wrap', '6.283185307179586', '-P', '-workdir', '.'], check=True, timeout=60)
assert Path('out.ppm').read_bytes().startswith(b'P6')
print('mdx rendered a PPM image without an X server.')

import os
import sys
home = Path(isce.__file__).parent
stack = Path(sys.prefix)/'share/isce2'
env = os.environ.copy()
env['ISCE_HOME'] = str(home)
env['ISCE_STACK'] = str(stack)
env['PYTHONPATH'] = ':'.join(map(str, [home, home/'applications', home/'components', home/'library', stack]))
entries = [(home/'applications'/n, (0, 1)) for n in ['topsApp.py', 'alos2App.py', 'stripmapApp.py']]
entries += [(stack/n, (0,)) for n in ['topsStack/stackSentinel.py', 'alosStack/create_cmds.py', 'stripmapStack/stackStripMap.py']]
for script, allowed in entries:
    r = subprocess.run([sys.executable, str(script), '--help'], env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode in allowed and 'Traceback' not in r.stderr, r.stdout + r.stderr
    assert any(term in r.stdout.lower() for term in ['usage:', 'input file', 'configurable parameters']), r.stdout
    print('CLI passed:', script.name)
