#!/bin/bash
set -euo pipefail
export PATH="$BUILD_PREFIX/bin:$PREFIX/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig:$PREFIX/share/pkgconfig"
unset PYTHONPATH PYTHONHOME
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
