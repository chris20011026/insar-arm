#!/bin/bash
# Uses the Python shipped with the user's existing Conda, not Apple's SDK Python.
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"
conda_exe="${CONDA_EXE:-$(command -v conda || true)}"
if [ -z "$conda_exe" ]; then
  echo 'Please install native Apple Silicon Miniforge / Conda first.' >&2
  exit 1
fi
base="$("$conda_exe" info --base)"
exec "$base/bin/python" -I "$root/packaging/install_binary.py" --conda "$conda_exe" "$@"
