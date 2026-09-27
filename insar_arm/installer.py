#!/usr/bin/env python3
"""Build a new, isolated Apple Silicon InSAR environment from locked inputs."""
from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.0'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def clean_env(prefix=None):
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(('PYTHON', 'DYLD_', 'ISCE', 'CMAKE_', 'PIP_')) or key in (
            'LD_LIBRARY_PATH', 'CPATH', 'LIBRARY_PATH', 'CFLAGS', 'CXXFLAGS',
            'FFLAGS', 'CPPFLAGS', 'LDFLAGS', 'PKG_CONFIG_PATH', 'MAGICK_CONFIGURE_PATH'):
            env.pop(key, None)
    env['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'
    env['CONDA_SUBDIR'] = 'osx-arm64'
    env['PYTHONNOUSERSITE'] = '1'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    if prefix:
        env['PATH'] = str(prefix/'bin') + ':' + env['PATH']
    return env


def capture(argv):
    # Successful stderr warnings must never be mixed into JSON/version stdout.
    return subprocess.run(list(map(str, argv)), text=True, capture_output=True,
                          env=clean_env(), check=True).stdout.strip()


def find_conda(explicit=None):
    candidate = explicit or os.environ.get('CONDA_EXE') or shutil.which('conda')
    if not candidate:
        for base in ('miniforge3', 'miniconda3', 'anaconda3'):
            p = Path.home()/base/'bin/conda'
            if p.is_file():
                candidate = str(p)
                break
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError('Conda not found. Install Miniforge, or pass --conda /path/to/bin/conda. See README.md.')
    return Path(candidate).resolve()


def resolve_prefix(args, conda):
    if args.prefix:
        return Path(args.prefix).expanduser().resolve()
    info = json.loads(capture([conda, 'info', '--json']))
    # Prefer an existing name so install refuses it instead of creating a second,
    # shadowing environment when Conda changes the writable env-directory order.
    for directory in info['envs_dirs']:
        existing=Path(directory)/'insar_arm'
        if existing.exists():
            return existing.resolve()
    return (Path(info['envs_dirs'][0])/'insar_arm').resolve()


def preflight(args):
    if sys.platform != 'darwin' or platform.machine() != 'arm64':
        raise RuntimeError('Stage 1 supports native Apple Silicon macOS only. Run outside Rosetta; Linux/Intel/Windows are not supported by this profile.')
    if tuple(map(int, platform.mac_ver()[0].split('.')[:2])) < (14, 5):
        raise RuntimeError('This locked profile requires macOS 14.5 or newer.')
    capture(['/usr/bin/xcrun', '--show-sdk-path'])
    conda = find_conda(args.conda)
    if args.gcc_prefix:
        gcc = Path(args.gcc_prefix).expanduser().resolve()
    else:
        brew = shutil.which('brew') or '/opt/homebrew/bin/brew'
        try:
            gcc = Path(capture([brew, '--prefix', 'gcc@14'])).resolve()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError('GCC 14 is required. Install Homebrew gcc@14 or pass --gcc-prefix. The installer does not modify Homebrew.') from exc
    for name in ('gcc-14', 'g++-14', 'gfortran-14'):
        compiler = gcc/'bin'/name
        if not compiler.is_file():
            raise RuntimeError(f'Missing compiler: {compiler}')
        if not capture([compiler, '-dumpfullversion']).startswith('14.'):
            raise RuntimeError(f'{name} is not GCC 14.')
        if not capture([compiler, '-dumpmachine']).startswith(('aarch64-', 'arm64-')):
            raise RuntimeError(f'{name} is not an ARM compiler.')
    return conda, gcc


def safe_extract(archive, target):
    """Extract only a single-root source archive without links or special files."""
    if target.exists():
        raise RuntimeError(f'Extraction target already exists: {target}')
    with tempfile.TemporaryDirectory(dir=target.parent, prefix='.extract-') as temporary:
        temporary = Path(temporary)
        with tarfile.open(archive) as stream:
            members = stream.getmembers()
            roots = set()
            for m in members:
                p = Path(m.name)
                if p.is_absolute() or '..' in p.parts or not (m.isdir() or m.isfile()):
                    raise RuntimeError(f'Unsafe source archive member: {m.name}')
                if p.parts:
                    roots.add(p.parts[0])
            if len(roots) != 1:
                raise RuntimeError('Expected one source directory in archive.')
            stream.extractall(temporary, members=members)
        (temporary/roots.pop()).rename(target)


class Install:
    def __init__(self, args, conda, gcc):
        self.args, self.conda, self.gcc = args, conda, gcc
        self.prefix = resolve_prefix(args, conda)
        self.cache = Path(args.cache).expanduser().resolve()
        self.work = self.cache/'builds'/hashlib.sha256(str(self.prefix).encode()).hexdigest()[:16]
        self.sources = self.work/'sources'
        self.logs = self.work/'logs'
        self.env = clean_env(self.prefix)
        self.env['MPLCONFIGDIR'] = str(self.work/'matplotlib')
        self.statefile = self.work/'state.json'
        inputs = {str(p.relative_to(ROOT)): digest(p)
                  for d in ('locks', 'insar_arm') for p in sorted((ROOT/d).rglob('*'))
                  if p.is_file() and '__pycache__' not in p.parts}
        self.identity = {'prefix': str(self.prefix), 'gcc': str(gcc), 'inputs': inputs}
        self.state = {'identity': self.identity, 'completed': [], 'version': VERSION}

    def run(self, argv, cwd=None, env=None):
        argv = list(map(str, argv))
        with self.log.open('a') as output:
            output.write('$ ' + shlex.join(argv) + '\n')
            output.flush()
            result = subprocess.run(argv, cwd=cwd or self.work, env=env or self.env,
                                    stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            tail = '\n'.join(self.log.read_text(errors='replace').splitlines()[-20:])
            raise RuntimeError(f'Command failed ({result.returncode}). Log: {self.log}\n{tail}')

    def fetch(self, item):
        downloads = self.cache/'downloads'
        downloads.mkdir(parents=True, exist_ok=True)
        with (downloads/'.download.lock').open('w') as guard:
            fcntl.flock(guard, fcntl.LOCK_EX)
            return self._fetch_locked(item, downloads)

    def _fetch_locked(self, item, downloads):
        target = downloads/item['filename']
        if target.exists() and digest(target) == item['sha256']:
            return target
        part = target.with_suffix(target.suffix + '.part')
        self.run(['/usr/bin/curl', '--fail', '--location', '--proto', '=https',
                  '--retry', '3', '--connect-timeout', '30', '--max-time', '1800',
                  '--output', part, item['url']])
        if digest(part) != item['sha256']:
            raise RuntimeError(f'Checksum mismatch: {item["filename"]}; refusing to use it.')
        part.replace(target)
        return target

    def downloads(self):
        self.sources.mkdir(parents=True, exist_ok=True)
        for item in json.loads((ROOT/'locks/sources.json').read_text()):
            archive = self.fetch(item)
            if item['filename'].endswith('.tar.gz'):
                destination = self.sources/item['name']
                # Only disposable installer-owned extraction directories are replaced.
                if destination.exists():
                    shutil.rmtree(destination)
                safe_extract(archive, destination)
        for item in json.loads((ROOT/'locks/wheels-osx-arm64-py312.json').read_text()):
            self.fetch(item)
        for name, level in [('configure-big_sur.diff', '1'), ('patch-lib-xm-vendor.diff', '0'),
                            ('fix-anti-aliasing-performance.patch', '1')]:
            self.run(['/usr/bin/patch', '--batch', '-p'+level, '-i', self.cache/'downloads'/name],
                     cwd=self.sources/'motif')

    def conda_environment(self):
        if self.prefix.exists():
            raise RuntimeError('Target already exists before Conda creation. Choose a new prefix; partial Conda creation is never overwritten automatically.')
        self.run([self.conda, 'create', '--yes', '--prefix', self.prefix,
                  '--file', ROOT/'locks/conda-osx-arm64.lock'], env=clean_env())
        save_json(self.prefix/'.insar-arm-install.json', self.identity)

    def motif(self):
        env = self.env.copy()
        env.update(CC='/usr/bin/clang', CFLAGS='-O2 -Wno-implicit-function-declaration -Wno-incompatible-function-pointer-types',
                   CPPFLAGS=f'-I{self.prefix}/include',
                   LDFLAGS=f'-L{self.prefix}/lib -Wl,-rpath,{self.prefix}/lib',
                   PKG_CONFIG_PATH=str(self.prefix/'lib/pkgconfig'))
        source = self.sources/'motif'
        self.run([source/'configure', f'--prefix={self.prefix}', f'--x-includes={self.prefix}/include',
                  f'--x-libraries={self.prefix}/lib', '--disable-printing', '--enable-xft', '--enable-jpeg', '--enable-png'], cwd=source, env=env)
        self.run(['make', f'-j{self.args.jobs}'], cwd=source, env=env)
        self.run(['make', 'install'], cwd=source, env=env)

    def isce(self):
        self.run(['cmake', '-S', self.sources/'isce2', '-B', self.work/'isce-build', '-G', 'Ninja',
                  f'-DCMAKE_INSTALL_PREFIX={self.prefix}', '-DPYTHON_MODULE_DIR=lib/python3.12/site-packages',
                  f'-DPython_ROOT_DIR={self.prefix}', f'-DPython_EXECUTABLE={self.prefix}/bin/python3',
                  f'-DCMAKE_PREFIX_PATH={self.prefix}', '-DCMAKE_FIND_FRAMEWORK=NEVER',
                  f'-DCMAKE_C_COMPILER={self.gcc}/bin/gcc-14', f'-DCMAKE_CXX_COMPILER={self.gcc}/bin/g++-14',
                  f'-DCMAKE_Fortran_COMPILER={self.gcc}/bin/gfortran-14', '-DCMAKE_BUILD_TYPE=Release',
                  '-DCMAKE_Fortran_FLAGS=-fallow-argument-mismatch', f'-DMOTIF_INCLUDE_DIR={self.prefix}/include',
                  f'-DMOTIF_LIBRARIES={self.prefix}/lib/libXm.dylib', '-DISCE2_WITH_STANFORD=OFF'])
        self.run(['cmake', '--build', self.work/'isce-build', '-j', str(self.args.jobs)])
        self.run(['cmake', '--install', self.work/'isce-build'])
        self.run(['ctest', '--test-dir', self.work/'isce-build', '--output-on-failure', '-j', str(self.args.jobs)])

    def mintpy(self):
        wheels = json.loads((ROOT/'locks/wheels-osx-arm64-py312.json').read_text())
        self.run([self.prefix/'bin/python', '-m', 'pip', 'install', '--no-index', '--no-deps',
                  *[self.cache/'downloads'/w['filename'] for w in wheels]])
        env = self.env.copy()
        env['SETUPTOOLS_SCM_PRETEND_VERSION_FOR_MINTPY'] = '1.6.4.post3'
        self.run([self.prefix/'bin/python', '-m', 'pip', 'install', '--no-index', '--no-deps',
                  '--no-build-isolation', self.sources/'mintpy'], env=env)

    def snaphu(self):
        # Compile the upstream source locally; do not ship a machine-specific binary.
        self.run(['make', '-B', f'-j{self.args.jobs}', 'CC=/usr/bin/clang',
                  'CFLAGS=-O2 -arch arm64'], cwd=self.sources/'snaphu/src')
        shutil.copy2(self.sources/'snaphu/bin/snaphu', self.prefix/'bin/snaphu')
        dest = self.prefix/'share/snaphu'
        dest.mkdir(parents=True, exist_ok=True)
        for name in ('README', 'config', 'man'):
            src = self.sources/'snaphu'/name
            if src.is_dir():
                shutil.copytree(src, dest/name, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest/name)

    def configure(self):
        site = self.prefix/'lib/python3.12/site-packages'
        alias = site/'isce'
        if alias.exists() and alias.resolve() != (site/'isce2').resolve():
            raise RuntimeError('An unexpected ISCE installation exists in the target.')
        if not alias.exists():
            alias.symlink_to('isce2', target_is_directory=True)
        for tree in ('stack', 'timeseries'):
            shutil.copytree(self.sources/'isce2/contrib'/tree, self.prefix/'share/isce2', dirs_exist_ok=True)
        for phase in ('activate', 'deactivate'):
            target = self.prefix/f'etc/conda/{phase}.d'
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/f'insar_arm/{phase}.sh', target/'insar-arm.sh')
        font = self.prefix/'fonts/DejaVuSans.ttf'
        if not font.is_file():
            raise RuntimeError('Locked DejaVu font missing.')
        config = self.prefix/'etc/insar-arm-imagemagick'
        config.mkdir(parents=True, exist_ok=True)
        typemap = ET.Element('typemap')
        ET.SubElement(typemap, 'type', name='DejaVu-Sans', fullname='DejaVu Sans',
                      family='DejaVu Sans', style='normal', stretch='normal', weight='400', glyphs=str(font))
        ET.ElementTree(typemap).write(config/'type.xml', encoding='UTF-8', xml_declaration=True)
        (self.prefix/'.condarc').write_text('subdir: osx-arm64\nchannels:\n  - conda-forge\nchannel_priority: strict\n')
        (self.prefix/'conda-meta/pinned').write_text('python 3.12.*\nnumpy 1.26.4\ngdal 3.10.3\nimagecodecs 2024.9.22\n')
        check_dir = self.prefix/'share/insar-arm'
        check_dir.mkdir(parents=True, exist_ok=True)
        for name in ('verify.py', 'probes.py'):
            shutil.copy2(ROOT/'insar_arm'/name, check_dir/name)
        save_json(check_dir/'build-info.json', dict(version=VERSION, **self.identity,
                  build_directory=str(self.work),
                  gcc_version=capture([self.gcc/'bin/gfortran-14', '-dumpfullversion']),
                  snaphu_cs2=True, platform=platform.platform(), installed_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        wrapper = self.prefix/'bin/insar-check'
        wrapper.write_text('#!/bin/bash\nset -e\nbase="$(cd "$(dirname "$0")/.." && pwd)"\nexec "$base/bin/python" "$base/share/insar-arm/verify.py" "$@"\n')
        wrapper.chmod(0o755)

    def verify(self):
        self.run([self.conda, 'run', '--no-capture-output', '-p', self.prefix,
                  self.prefix/'bin/python', self.prefix/'share/insar-arm/verify.py',
                  '--output', self.work/'report'], env=clean_env())

    def install(self):
        if ' ' in str(self.prefix) or ' ' in str(self.cache):
            raise RuntimeError('Upstream build tools require installation/cache paths without spaces. Choose another --prefix / --cache.')
        self.work.mkdir(parents=True, exist_ok=True)
        with (self.work/'install.lock').open('w') as guard:
            try:
                fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Another installer is using this prefix.')
            if self.statefile.exists():
                if not self.args.resume:
                    raise RuntimeError(f'An installation record exists. Use --resume with the same inputs, or choose a new --prefix. Record: {self.statefile}')
                self.state = json.loads(self.statefile.read_text())
                if self.state['identity'] != self.identity:
                    raise RuntimeError('Installer inputs/compiler changed. Use a new prefix/cache build; do not resume incompatible builds.')
                if self.prefix.exists() and (not (self.prefix/'.insar-arm-install.json').exists()
                                            or json.loads((self.prefix/'.insar-arm-install.json').read_text()) != self.identity):
                    raise RuntimeError('Existing prefix is not owned by this completed Conda stage; refusing to overwrite it.')
                if 'conda_environment' in self.state['completed'] and not (self.prefix/'conda-meta/history').exists():
                    raise RuntimeError('Recorded environment is missing. Choose a new prefix.')
            elif self.prefix.exists():
                raise RuntimeError(f'Refusing to modify an existing environment: {self.prefix}. Choose a NEW --prefix.')
            self.logs.mkdir(parents=True, exist_ok=True)
            save_json(self.statefile, self.state)
            stages = ('downloads', 'conda_environment', 'motif', 'isce', 'mintpy', 'snaphu', 'configure', 'verify')
            for i, name in enumerate(stages, 1):
                if name in self.state['completed'] and name != 'verify':
                    print(f'[{i}/{len(stages)}] {name}: already completed', flush=True)
                    continue
                self.log = self.logs/f'{name}.log'
                print(f'[{i}/{len(stages)}] {name} — log: {self.log}', flush=True)
                started = time.time()
                try:
                    getattr(self, name)()
                except Exception as exc:
                    self.state['failure'] = dict(stage=name, error=str(exc))
                    save_json(self.statefile, self.state)
                    raise
                if name not in self.state['completed']:
                    self.state['completed'].append(name)
                self.state.setdefault('seconds', {})[name] = round(time.time()-started, 2)
                self.state.pop('failure', None)
                save_json(self.statefile, self.state)
            print(f'\nInstallation and checks passed.\nconda activate {shlex.quote(str(self.prefix))}\nuse_alosStack   # or use_topsStack / use_stripmapStack / use_mintpy\ninsar-check\nReport: {self.work}/report/index.html')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('plan', 'doctor', 'install', 'verify'):
        p = commands.add_parser(name)
        p.add_argument('--conda', help='Existing Conda executable (Miniforge recommended).')
        p.add_argument('--prefix', help='NEW environment prefix. Default: Conda envs directory / insar_arm.')
        p.add_argument('--gcc-prefix', help='GCC 14 installation root. Default: brew --prefix gcc@14.')
        p.add_argument('--cache', default=str(ROOT/'.work'), help='Download/build/log cache; not needed at runtime.')
        p.add_argument('--jobs', type=int, default=4)
        p.add_argument('--resume', action='store_true', help='Resume only an installation owned by these exact inputs.')
        p.add_argument('--output', help='Verification report directory.')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    try:
        if args.command == 'plan':
            print('Platform: Apple Silicon macOS >=14.5; Python 3.12; CPU only.\nPrerequisites: Conda, Apple command-line tools, native GCC 14.\nInstalls: locked Conda packages, Motif, ISCE2 2.6.5, MintPy 1.6.4.post3, SNAPHU 2.0.7.\nAlways creates a NEW environment. Never edits shell startup files or existing environments.\nRuns CTest, six entry-point checks, numerical probes and architecture audit.\nComplete real-data validation of every sensor/workflow is not claimed.')
        elif args.command == 'verify':
            conda = find_conda(args.conda)
            prefix = resolve_prefix(args, conda)
            command = [str(conda), 'run', '--no-capture-output', '-p', str(prefix),
                       str(prefix/'bin/python'), str(prefix/'share/insar-arm/verify.py')]
            if args.output:
                command += ['--output', args.output]
            return subprocess.call(command, env=clean_env())
        else:
            conda, gcc = preflight(args)
            if args.command == 'doctor':
                print(json.dumps(dict(platform=platform.platform(), conda=str(conda), gcc=str(gcc),
                                      gcc_version=capture([gcc/'bin/gfortran-14', '-dumpfullversion']),
                                      target=str(resolve_prefix(args, conda))), indent=2))
            else:
                Install(args, conda, gcc).install()
    except (RuntimeError, OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
