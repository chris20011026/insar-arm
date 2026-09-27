#!/bin/bash
# Developer entry point. Never installs into an existing research environment.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
: "${CONDA_BUILD_EXE:?Set CONDA_BUILD_EXE to the conda-build executable in a separate build environment}"
export CONDA_SUBDIR=osx-arm64
export CONDA_BUILD_SYSROOT="${CONDA_BUILD_SYSROOT:-$(xcrun --show-sdk-path)}"
export CPU_COUNT="${CPU_COUNT:-4}"
case "$(uname -m)" in arm64) ;; *) echo 'Native Apple Silicon required' >&2; exit 1;; esac
croot="${INSAR_CONDA_BUILD_ROOT:-$root/.work/stage2-build}"
mkdir -p "$croot"
croot="$(cd "$croot" && pwd)"
"$CONDA_BUILD_EXE" "$root/packaging/recipes/motif" -m "$root/packaging/conda_build_config.yaml" --override-channels -c conda-forge --croot "$croot"
"$CONDA_BUILD_EXE" "$root/packaging/recipes/isce2" -m "$root/packaging/conda_build_config.yaml" --override-channels -c "file://$croot" -c conda-forge --croot "$croot"
"$CONDA_BUILD_EXE" "$root/packaging/recipes/snaphu-cli" -m "$root/packaging/conda_build_config.yaml" --override-channels -c conda-forge --croot "$croot"
