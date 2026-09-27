import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch

from insar_arm.installer import Install, ROOT, safe_extract, capture, resolve_prefix
from insar_arm.verify import cpu_types, runtime_paths


class SourceSafety(unittest.TestCase):
    def test_successful_stderr_warning_does_not_corrupt_json(self):
        import sys
        output=capture([sys.executable,'-c','import sys; print("{\\"ok\\":true}"); print("system warning",file=sys.stderr)'])
        self.assertEqual(json.loads(output),{'ok':True})

    def test_default_does_not_shadow_existing_named_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            existing=root/'second/insar_arm'
            existing.mkdir(parents=True)
            info=json.dumps({'envs_dirs':[str(root/'first'),str(root/'second')]})
            with patch('insar_arm.installer.capture',return_value=info):
                self.assertEqual(resolve_prefix(argparse.Namespace(prefix=None),Path('/unused/conda')),existing.resolve())

    def archive(self, folder, entries):
        archive=folder/'source.tar.gz'
        with tarfile.open(archive,'w:gz') as stream:
            for name,kind in entries:
                item=tarfile.TarInfo(name)
                if kind=='link':
                    item.type=tarfile.SYMTYPE
                    item.linkname='/tmp/external'
                    stream.addfile(item)
                else:
                    item.size=4
                    stream.addfile(item,io.BytesIO(b'test'))
        return archive

    def test_single_root_extracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            safe_extract(self.archive(root,[('upstream/a.txt','file')]),root/'source')
            self.assertEqual((root/'source/a.txt').read_text(),'test')

    def test_unsafe_archives_rejected(self):
        for name,kind in [('../escape','file'),('/absolute','file'),('upstream/link','link')]:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                with self.assertRaises(RuntimeError):
                    safe_extract(self.archive(root,[(name,kind)]),root/'source')
                self.assertFalse((root/'source').exists())

    def test_source_and_wheel_pins(self):
        for filename in ('sources.json','wheels-osx-arm64-py312.json'):
            records=json.loads((ROOT/'locks'/filename).read_text())
            self.assertEqual(len(records),len({r['filename'] for r in records}))
            for record in records:
                self.assertTrue(record['url'].startswith('https://'))
                self.assertRegex(record['sha256'],r'^[0-9a-f]{64}$')
        for line in (ROOT/'locks/conda-osx-arm64.lock').read_text().splitlines():
            if line.startswith('https://'):
                self.assertRegex(line,r'^https://conda.anaconda.org/conda-forge/(osx-arm64|noarch)/[^/]+#[0-9a-f]{32}$')


class Lifecycle(unittest.TestCase):
    def installer(self,tmp,resume=False):
        root=Path(tmp)
        args=argparse.Namespace(prefix=str(root/'env'),cache=str(root/'cache'),jobs=1,resume=resume)
        obj=Install(args,Path('/unused/conda'),Path('/unused/gcc'))
        self.calls=[]
        for name in ('downloads','motif','isce','mintpy','snaphu','configure','verify'):
            setattr(obj,name,lambda name=name:self.calls.append(name))
        def create():
            self.calls.append('conda_environment')
            (obj.prefix/'conda-meta').mkdir(parents=True)
            (obj.prefix/'conda-meta/history').write_text('test')
            (obj.prefix/'.insar-arm-install.json').write_text(json.dumps(obj.identity))
        obj.conda_environment=create
        return obj

    def test_existing_environment_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj=self.installer(tmp)
            obj.prefix.mkdir()
            (obj.prefix/'keep').write_text('original')
            with self.assertRaisesRegex(RuntimeError,'existing environment'):
                obj.install()
            self.assertEqual((obj.prefix/'keep').read_text(),'original')
            self.assertEqual(self.calls,[])

    def test_failed_build_resumes_after_completed_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj=self.installer(tmp)
            obj.isce=Mock(side_effect=RuntimeError('compiler failure'))
            with self.assertRaisesRegex(RuntimeError,'compiler failure'):obj.install()
            self.assertEqual(json.loads(obj.statefile.read_text())['completed'],['downloads','conda_environment','motif'])
            resumed=self.installer(tmp,resume=True)
            resumed.install()
            self.assertEqual(self.calls,['isce','mintpy','snaphu','configure','verify'])
            again=self.installer(tmp,resume=True)
            again.install()
            self.assertEqual(self.calls,['verify'])

    def test_resume_rejects_unknown_prefix_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj=self.installer(tmp)
            obj.install()
            (obj.prefix/'.insar-arm-install.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError,'refusing to overwrite'):
                self.installer(tmp,resume=True).install()

    def test_resume_rejects_changed_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj=self.installer(tmp)
            obj.install()
            state=json.loads(obj.statefile.read_text())
            state['identity']['inputs']['locks/sources.json']='changed'
            obj.statefile.write_text(json.dumps(state))
            with self.assertRaisesRegex(RuntimeError,'inputs/compiler changed'):
                self.installer(tmp,resume=True).install()

    def test_corrupt_download_is_not_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj=self.installer(tmp)
            item=dict(filename='test.tar.gz',url='https://example.invalid/source',sha256=hashlib.sha256(b'valid').hexdigest())
            def fake_download(argv,**kwargs):
                Path(argv[argv.index('--output')+1]).write_bytes(b'corrupt')
            obj.run=fake_download
            with self.assertRaisesRegex(RuntimeError,'Checksum mismatch'):obj.fetch(item)
            self.assertFalse((obj.cache/'downloads/test.tar.gz').exists())


class Architecture(unittest.TestCase):
    def test_dylib_identity_is_not_an_external_dependency(self):
        commands='''Load command 0
          cmd LC_ID_DYLIB
         name /upstream/build-machine/libexample.dylib (offset 24)
Load command 1
          cmd LC_LOAD_DYLIB
         name /opt/runtime/librequired.dylib (offset 24)
Load command 2
          cmd LC_RPATH
         path /opt/runtime (offset 12)
'''
        self.assertEqual(runtime_paths(commands),[('LC_LOAD_DYLIB','/opt/runtime/librequired.dylib'),('LC_RPATH','/opt/runtime')])

    def test_arm_intel_and_universal_headers(self):
        arm=0x0100000C
        intel=0x01000007
        self.assertEqual(cpu_types(b'\xcf\xfa\xed\xfe'+struct.pack('<I',arm)),[arm])
        self.assertEqual(cpu_types(b'\xcf\xfa\xed\xfe'+struct.pack('<I',intel)),[intel])
        fat=b'\xca\xfe\xba\xbe'+struct.pack('>I',2)
        fat+=struct.pack('>5I',arm,0,0,0,0)+struct.pack('>5I',intel,0,0,0,0)
        self.assertEqual(cpu_types(fat),[arm,intel])
        self.assertEqual(cpu_types(b'plain text'),[])


class Activation(unittest.TestCase):
    def test_launcher_ignores_foreign_pythonpath(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'json.py').write_text('raise RuntimeError("foreign module loaded")\n')
            env=os.environ.copy()
            env['PYTHONPATH']=tmp
            result=subprocess.run(['/bin/bash',str(ROOT/'insar-arm'),'plan'],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Installs:',result.stdout)

    def test_verifier_rejects_disabled_assertions(self):
        import sys
        result=subprocess.run([sys.executable,'-O',str(ROOT/'insar_arm/verify.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('normal Python mode',result.stderr)

    def test_bash_zsh_paths_and_restoration(self):
        for shell,flags in [('/bin/bash',['--noprofile','--norc']),('/bin/zsh',['-f'])]:
            if not Path(shell).exists():continue
            with self.subTest(shell=shell),tempfile.TemporaryDirectory() as tmp:
                prefix=Path(tmp)/'env'
                for name in ['bin/python3','bin/geocode.py','share/isce2/alosStack/geocode.py',
                             'share/isce2/topsStack/stackSentinel.py','share/isce2/stripmapStack/stackStripMap.py']:
                    path=prefix/name
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_text('#!/bin/sh\nexit 0\n')
                    path.chmod(0o755)
                script='''set -e
export PYTHONPATH="saved value"
unset ISCE_HOME
source "$1"
test "$ISCE_STACK" = "$CONDA_PREFIX/share/isce2"
case "$PYTHONPATH" in *"$ISCE_STACK"*) ;; *) exit 3;; esac
use_alosStack
test "$(command -v geocode.py)" = "$ISCE_STACK/alosStack/geocode.py"
use_topsStack
use_stripmapStack
use_mintpy
test "$(command -v geocode.py)" = "$CONDA_PREFIX/bin/geocode.py"
source "$2"
test "$PYTHONPATH" = "saved value"
test "${ISCE_HOME+yes}" = ""
case "$PATH" in *"$CONDA_PREFIX"*) exit 4;; esac
'''
                env=os.environ.copy()
                env.update(CONDA_PREFIX=str(prefix),PATH='/usr/bin:/bin')
                subprocess.run([shell,*flags,'-c',script,'test',str(ROOT/'insar_arm/activate.sh'),
                                str(ROOT/'insar_arm/deactivate.sh')],env=env,check=True,capture_output=True,text=True)


if __name__=='__main__':unittest.main()
