#!/usr/bin/env python3
"""Create a small, deterministic source release; never include build data."""
import argparse
import hashlib
from pathlib import Path
import stat
import zipfile

ROOT=Path(__file__).resolve().parents[1]
INCLUDE=('README.md','LICENSE','THIRD_PARTY.md','CHANGELOG.md','.gitignore',
         'insar-arm','install.sh','install-binary.sh','locks','insar_arm','tests','docs','tools','packaging','.github','.gitattributes')


def package(output):
    output.mkdir(parents=True,exist_ok=True)
    target=output/'insar-arm-0.2.0b1.zip'
    files=[]
    for name in INCLUDE:
        path=ROOT/name
        files.extend([path] if path.is_file() else sorted(p for p in path.rglob('*') if p.is_file()))
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(files):
            if '__pycache__' in path.parts or path.suffix=='.pyc' or path.name=='.DS_Store':continue
            relative=path.relative_to(ROOT)
            content=path.read_bytes()
            # Local machine paths/logs must not slip into a public source release.
            for marker in (b'/' + b'Users/', b'/' + b'Volumes/'):
                if marker in content:
                    raise RuntimeError(f'Local path found in release file: {relative}')
            entry=zipfile.ZipInfo('insar-arm-0.2.0b1/'+relative.as_posix(),date_time=(2026,9,28,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            entry.create_system=3
            entry.external_attr=(stat.S_IFREG|stat.S_IMODE(path.stat().st_mode))<<16
            archive.writestr(entry,content)
    checksum=hashlib.sha256(target.read_bytes()).hexdigest()
    (output/'SHA256SUMS').write_text(f'{checksum}  {target.name}\n')
    print(f'{target} ({target.stat().st_size:,} bytes)\nSHA256 {checksum}')
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    package(parser.parse_args().output.resolve())
