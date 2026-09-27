import subprocess
import numpy as np
help_result = subprocess.run(['snaphu', '-h'], capture_output=True, text=True)
assert help_result.returncode == 1  # Upstream returns 1 for help.
assert 'snaphu v2.0.7' in help_result.stdout + help_result.stderr
y, x = np.mgrid[:64, :64]
phase = (.17*x + .12*y).astype(np.float32)
np.exp(1j*phase).astype(np.complex64).tofile('wrapped.int')
subprocess.run(['snaphu', '-s', 'wrapped.int', '64', '-o', 'unwrapped.bin',
                '-C', 'OUTFILEFORMAT FLOAT_DATA'], check=True, timeout=60)
delta = np.fromfile('unwrapped.bin', np.float32).reshape(64, 64) - phase
delta -= np.median(delta)
error = float(np.max(np.abs(delta)))
assert error < 1e-4, error
print('SNAPHU synthetic maximum phase error:', error)
