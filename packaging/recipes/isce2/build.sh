#!/bin/bash
set -euo pipefail
export PATH="$BUILD_PREFIX/bin:$PREFIX/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig:$PREFIX/share/pkgconfig"
unset PYTHONPATH PYTHONHOME
# Retain the complete upstream source/notices with the binary distribution.
# Snapshot before CMake generates files; this list is the pinned archive's root.
mkdir -p "$PREFIX/share/isce2"
"$PYTHON" - <<'PYSOURCE'
import gzip, os, tarfile
from pathlib import Path
names = '.circleci .cmake .gitignore CMakeLists.txt CONTRIBUTING.md LICENSE LICENSE-2.0.html LICENSE-2.0.txt README.md SConstruct __init__.py applications components configuration contrib defaults docker docs examples library license.py release_history.py release_note.txt schema scons_tools sec.lst setup test'.split()
def normalize(info):
    info.uid = info.gid = 0
    info.uname = info.gname = ''
    info.mtime = 0
    return info
out = Path(os.environ['PREFIX'])/'share/isce2/upstream-source.tar.gz'
with out.open('wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as gz, tarfile.open(fileobj=gz, mode='w') as tar:
    for name in names:
        tar.add(name, arcname='isce2-2.6.5/'+name, filter=normalize)
PYSOURCE
cmake -S . -B build -G Ninja \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DPYTHON_MODULE_DIR="${SP_DIR#"$PREFIX"/}" \
  -DPython_ROOT_DIR="$PREFIX" -DPython_EXECUTABLE="$PYTHON" \
  -DCMAKE_PREFIX_PATH="$PREFIX" -DCMAKE_FIND_FRAMEWORK=NEVER \
  "-DCMAKE_IGNORE_PREFIX_PATH=/opt/homebrew;/usr/local" \
  -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" -DCMAKE_Fortran_COMPILER="$FC" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_Fortran_FLAGS="$FFLAGS -fallow-argument-mismatch" \
  -DMOTIF_INCLUDE_DIR="$PREFIX/include" -DMOTIF_LIBRARIES="$PREFIX/lib/libXm.dylib" \
  -DISCE2_WITH_STANFORD=OFF
cmake --build build -j"${CPU_COUNT:-4}"
cmake --install build
ctest --test-dir build --output-on-failure -j"${CPU_COUNT:-4}"
mkdir -p "$PREFIX/share/isce2"
cp -R contrib/stack/. "$PREFIX/share/isce2/"
cp -R contrib/timeseries/. "$PREFIX/share/isce2/"

# Conda omits empty directories, but ISCE applications require helper to exist.
# The upstream conda-forge recipe uses the same completion marker.
mkdir -p "$SP_DIR/isce2/helper"
touch "$SP_DIR/isce2/helper/completed"
