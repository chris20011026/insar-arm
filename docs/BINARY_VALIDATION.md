# Binary beta 1 validation

Release: `0.2.0b1`, native Apple Silicon, macOS 14.5 or newer.

## Local fresh-prefix installation — 2026-09-28

A new environment was created exclusively from the four built Conda packages and conda-forge dependencies, separate from the existing research environments. Host: macOS 26.6.2, arm64.

- All **15 validation checks passed**: environment, scientific imports, six ISCE2 entry points, shell selectors, ALOS command generation, numerical kernels, plotting, MintPy inversion, Python dependencies and architecture.
- **381 Conda packages**: 290 osx-arm64 and 91 noarch. Exact URLs and checksums are in `locks/insar-arm-0.2.0b1-osx-arm64.lock`.
- **1,822 native files** passed architecture/loading-path inspection; no external non-system absolute library paths were reported.
- ISCE2 upstream build tests: **53 / 53 passed**. Its package tests also exercised entry points, multilooking and mdx PPM output.
- Maximum synthetic multilook error: `3.89e-8`.
- Maximum synthetic SNAPHU phase error: `1.91e-6` radians.
- Maximum synthetic MintPy time-series error: `9.18e-9` metres; velocity error: `1.29e-7` metres/year.

These are errors against small synthetic reference calculations, not claims of satellite measurement accuracy.

## Independent hosted ARM verification

The `Binary environment validation` GitHub Actions workflow installs the public lock on a fresh `macos-14` ARM VM using pinned native Miniforge and uploads the full report. Consult the linked workflow run/release notes for its actual status; the existence of a workflow is not a passing result.

## Scope and limitations

Six entry-point tests cover three pair processors and three stack processors, not six complete real-data pipelines. The ALOS generator test covers four ionospheric-estimation/correction combinations. Kernel and MintPy tests use synthetic data. No private SAR imagery is distributed or processed by these checks.

The architecture audit checks Mach-O architecture and absolute load paths. Successful runtime tests add evidence for exercised code paths; they do not prove every optional plugin or relative library dependency works. Interactive X11 mdx windows, external weather services, all satellite modes, GPU workflows and scientific results on research datasets are not certified.

Users should retain working environments and compare a representative real-data project before migration. This prerelease does not alter existing environments or the research workbench.
