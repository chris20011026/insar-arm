#!/bin/bash
set -euo pipefail
# Upstream predates Apple Silicon; use maintained GNU platform detection.
cp "$BUILD_PREFIX/share/gnuconfig/config.sub" ./config.sub
cp "$BUILD_PREFIX/share/gnuconfig/config.guess" ./config.guess
patch -p1 < "$RECIPE_DIR/configure-big_sur.diff"
patch -p0 < "$RECIPE_DIR/patch-lib-xm-vendor.diff"
patch -p1 < "$RECIPE_DIR/fix-anti-aliasing-performance.patch"
export CFLAGS="$CFLAGS -Wno-implicit-function-declaration -Wno-incompatible-function-pointer-types"
export CPPFLAGS="$CPPFLAGS -I$PREFIX/include"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig"
./configure --prefix="$PREFIX" --x-includes="$PREFIX/include" --x-libraries="$PREFIX/lib" --disable-printing --enable-xft --enable-jpeg --enable-png
make -j"${CPU_COUNT:-4}"
make install
