#!/usr/bin/env python3
"""Reject Intel-only binaries and non-system absolute dependencies outside a prefix.

Run after installing packages into a different Conda prefix. This static audit
must accompany runtime/numerical tests, not replace them.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from insar_arm.verify import cpu_types, runtime_paths


def audit(prefix):
    prefix = prefix.resolve()
    if not (prefix / 'conda-meta').is_dir():
        raise ValueError('Expected a Conda environment prefix')
    errors, binaries, seen = [], [], set()
    for record in (prefix / 'conda-meta').glob('*.json'):
        metadata = json.loads(record.read_text())
        if metadata.get('subdir') not in ('osx-arm64', 'noarch'):
            errors.append('Unexpected package platform: ' + record.name)
    for path in prefix.rglob('*'):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        with path.open('rb') as stream:
            architectures = cpu_types(stream.read(4096))
        if architectures:
            if 0x0100000C not in architectures:
                errors.append('No ARM64 slice: ' + str(path))
            binaries.append(str(path))
    for start in range(0, len(binaries), 100):
        result = subprocess.run(['/usr/bin/otool', '-l', *binaries[start:start+100]],
                                capture_output=True, text=True, check=True)
        for kind, path in runtime_paths(result.stdout):
            if path.startswith('/') and not path.startswith((str(prefix)+'/', '/usr/lib/', '/System/Library/')):
                errors.append('External runtime path: ' + kind + ' ' + path)
    return {'prefix': str(prefix), 'native_files': len(binaries),
            'passed': not errors, 'errors': sorted(set(errors)),
            'scope': 'Static ARM and absolute runtime-path audit; relative-path resolution and numerical tests still required.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix', type=Path)
    args = parser.parse_args()
    report = audit(args.prefix)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['passed'] else 1)
