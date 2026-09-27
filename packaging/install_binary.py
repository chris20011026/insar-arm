"""Install the tested binary environment into a new prefix, then verify it."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT/'locks/insar-arm-0.2.0b1-osx-arm64.lock'


def clean_env():
    return {k:v for k,v in os.environ.items() if not k.startswith(('PYTHON', 'DYLD_', 'ISCE'))}


def choose_prefix(conda, requested):
    if requested:
        return Path(requested).expanduser().resolve()
    result = subprocess.run([conda, 'info', '--json'], check=True, capture_output=True, text=True, env=clean_env())
    folders = [Path(p) for p in json.loads(result.stdout)['envs_dirs']]
    candidates = [p/'insar_arm' for p in folders]
    return next((p for p in candidates if p.exists()), candidates[0]).resolve()


def install(conda, prefix, lock=LOCK, output=None):
    if prefix.exists():
        raise RuntimeError(f'Existing path will not be overwritten: {prefix}. Use --prefix with a new path.')
    if not lock.is_file():
        raise RuntimeError('The release lock file is missing; use a complete release download.')
    lines = lock.read_text().splitlines()
    if '@EXPLICIT' not in lines:
        raise RuntimeError('Expected an explicit package lock.')
    urls = [s for s in lines if s and not s.startswith(('#','@'))]
    allowed = ('https://conda.anaconda.org/conda-forge/', 'https://chris20011026.github.io/insar-arm/')
    if not urls or any(not u.startswith(allowed) or not re.fullmatch(r'[0-9a-f]{32}', u.rsplit('#', 1)[-1]) for u in urls):
        raise RuntimeError('Lock contains an unexpected or unchecked package URL.')
    env = clean_env()
    env['CONDA_SUBDIR'] = 'osx-arm64'
    subprocess.run([conda, 'create', '--yes', '--prefix', str(prefix), '--file', str(lock), '--no-default-packages'], env=env, check=True)
    check = [conda, 'run', '--no-capture-output', '--prefix', str(prefix), 'insar-check']
    if output:
        check += ['--output', str(output)]
    subprocess.run(check, env=env, check=True)
    print(f'Installation and validation passed.\nconda activate {prefix}\nuse_alosStack  # or use_topsStack / use_stripmapStack / use_mintpy')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--conda', required=True)
    p.add_argument('--prefix', help='New environment path; defaults to Conda envs/insar_arm.')
    p.add_argument('--output', type=Path, help='Validation report directory.')
    a = p.parse_args()
    try:
        if platform.system() != 'Darwin' or platform.machine() != 'arm64':
            raise RuntimeError('This release requires native Apple Silicon macOS and native Conda.')
        version = tuple(map(int, platform.mac_ver()[0].split('.')[:2]))
        if version < (14,5):
            raise RuntimeError('This release requires macOS 14.5 or newer.')
        install(a.conda, choose_prefix(a.conda, a.prefix), output=a.output)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Installation stopped: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
