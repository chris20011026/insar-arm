# Validation status

Version: 0.1.0 public-test candidate.

Validation date: 2026-09-27.

## Tested host and installation

- Apple Silicon, native ARM64, macOS 26.6.2.
- Apple Command Line Tools / SDK available on the host; Homebrew GCC 14.4.0.
- Installer launched with Apple's Python 3.9.6; environment uses Python 3.12.
- Full installation from the locked public archives and package set into a NEW
  prefix. No copying of the previously installed ISCE2 or MintPy environment.
- Repeat fresh build into a different prefix also completed; the final source
  build profile was rebuilt into the release-validation environment and all stages passed.
- After the complete build, default-prefix discovery was hardened to keep Conda
  stderr warnings out of its JSON and to avoid shadowing an existing named
  environment. These read-only discovery changes were covered by regression and
  extracted-release CLI tests; the compiled sources, build stages, environment
  hooks and installed validator did not change.
- Package/download caches were reused where their hashes matched. This was not
  a test of an empty network cache or a second physical Mac.
- Both previously existing research environments were retained. All 793 recorded
  package-metadata / activation-configuration fingerprints remained unchanged.

## Results

| Test | Result |
|---|---|
| Installer / safety / shell / release unit tests | 16 passed |
| Upstream ISCE2 CTest suite | 53 / 53 passed |
| Installed environment validation | 15 / 15 passed |
| Conda package architecture | 316 osx-arm64 + 86 noarch |
| Native binary architecture | 2,163 distinct Mach-O files contain ARM64; no Intel-only files found |
| External absolute library dependencies | GCC 14 libgfortran, libgomp, libquadmath and libstdc++ verified ARM64 |
| Runtime independence | Installed checker passed with its entire source/build directory temporarily unavailable |
| Environment-variable and command routing | bash / zsh Stack switches, MintPy switches and restoration passed |
| Synthetic ALOS command generation | Four combinations of ion-estimation / ion-correction flags passed |
| Synthetic multilooking | Maximum error against NumPy reference ≈ 3.89e-8 |
| Synthetic ion filtering | Constant-phase input retained within tolerance |
| Synthetic SNAPHU phase unwrapping | Maximum error after removing global phase offset ≈ 1.91e-6 radians |
| Synthetic MintPy time-series inversion | Maximum displacement error ≈ 9.18e-9 metres |
| Synthetic MintPy velocity | Maximum error ≈ 1.29e-7 metres/year |
| Plotting | Actual mdx PPM → labeled TIFF → PNG passed |

These numerical errors describe small synthetic tests, **not the accuracy of
real satellite displacement products**. The checks use limited BLAS thread counts
for reproducibility; they do not change users' normal processing thread settings.

The library audit distinguishes runtime dependencies from `LC_ID_DYLIB` identity
strings. Some upstream Conda binaries retain a build-machine identity; it is not
an external library dependency. A regression test covers that distinction.

## Workflow coverage

| Workflow | Current validation level |
|---|---|
| topsApp / Sentinel-1 pair | CLI startup; shared native modules |
| topsStack / Sentinel-1 stack | CLI startup, package imports and shell selection |
| alos2App / ALOS-2 pair | CLI startup; shared native modules |
| alosStack / ALOS-2 stack | CLI startup, synthetic command generation and selected numerical kernels |
| stripmapApp / stripmap pair | CLI startup; native focusing module imports |
| stripmapStack / stripmap stack | CLI startup, package imports and shell selection |
| MintPy | CLI/core imports, synthetic network inversion and velocity |

Full real-data cmd1–4, all supported sensors / data formats, interactive X11,
online atmospheric-data downloads, other macOS / SDK / GCC versions, and other
physical Macs remain outside the completed validation. Suitable public-data
end-to-end examples and additional host reports are the next validation work.

Generated detailed JSON/HTML reports contain local paths and remain outside the
source distribution. This summary intentionally omits personal filesystem paths
and private imagery. Users can generate their own reports with `insar-check`.

Levels used in this project:

1. **Installed / imports / CLI startup**: executable or module is present and loads.
2. **Synthetic numerical test**: a small deterministic input is compared to a known answer.
3. **Real-data end-to-end**: the complete scientific pipeline is executed and assessed.

Level 1 does not imply level 3. The stage-1 release does not claim level 3 coverage
for all six ISCE2 workflows.
