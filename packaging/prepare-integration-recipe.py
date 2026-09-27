#!/usr/bin/env python3
"""Make a self-contained integration recipe from the checked-out tool sources."""
import argparse
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('destination', type=Path)
a = p.parse_args()
dest = a.destination.resolve()
if dest.exists():
    raise SystemExit('Choose a new destination; existing recipes are not overwritten.')
shutil.copytree(root/'packaging/recipes/environment', dest)
(dest/'payload').mkdir()
for name in ['verify.py', 'probes.py', 'activate.sh', 'deactivate.sh']:
    shutil.copy2(root/'insar_arm'/name, dest/'payload'/name)
shutil.copy2(root/'LICENSE', dest/'LICENSE')
print(dest)
