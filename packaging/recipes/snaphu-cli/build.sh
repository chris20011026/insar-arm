#!/bin/bash
set -euo pipefail
# Preserve upstream CS2 behavior; its notices and restrictions accompany binary.
make -C src -B -j"${CPU_COUNT:-4}" CC="$CC" CFLAGS="$CFLAGS" LDFLAGS="$LDFLAGS"
mkdir -p "$PREFIX/bin" "$PREFIX/share/snaphu"
cp bin/snaphu "$PREFIX/bin/snaphu"
cp README "$PREFIX/share/snaphu/README"
cp -R config man "$PREFIX/share/snaphu/"
