# InSAR ARM — English quick start

Stage 1 is a source-based installer plus locked environment inputs and validation.
It builds a **new** Apple Silicon Conda environment with ISCE2 2.6.5, MintPy
1.6.4.post3, SNAPHU 2.0.7, GDAL and working mdx / ImageMagick rendering.

This is a public-test candidate, not a claim that every satellite workflow has
been scientifically validated. Native Apple Silicon ISCE2 compilation is prior
community work; attribution and licenses are in [THIRD_PARTY.md](../THIRD_PARTY.md).

## Requirements

- Native Apple Silicon macOS 14.5+ (minimum from locked dependencies).
- Conda, preferably native arm64 Miniforge. The existing Conda installation is retained.
- Apple Command Line Tools (`xcode-select --install`).
- Native Homebrew GCC 14 (`brew install gcc@14`). The installer does not install or update Homebrew.
- Internet access and approximately 10 GB available space for environment and caches.
- Installation and cache paths without spaces; bash or zsh.

Only the host versions recorded in [VALIDATION.md](VALIDATION.md) have actually
been exercised. OS compatibility requirements are not an exhaustive test matrix.

## Install

From an extracted copy of this repository:

```sh
bash insar-arm doctor
bash install.sh
```

Default target: `insar_arm` in Conda's environment directory. Existing environments
are never overwritten. To select another target:

```sh
bash install.sh --prefix "$HOME/miniforge3/envs/insar_arm_new"
```

Optional `--conda /path/to/bin/conda`, `--gcc-prefix /path/to/gcc14`, `--jobs 4`,
and `--cache /path/to/build-cache` override discovery and defaults.

All source archives / patches and additional wheels have pinned SHA256 hashes.
Conda packages have exact URL / MD5 locks. The installer uses upstream sources,
not a copy of the author's local environment. No scientific algorithms are patched.

## Use

Follow the full environment path printed by the installer:

```sh
conda activate /path/to/environment
use_alosStack          # create_cmds.py
use_topsStack          # stackSentinel.py
use_stripmapStack      # stackStripMap.py
use_mintpy             # smallbaselineApp.py
insar-check
```

Choose one selector at a time. It adjusts command priority only; it does not
process data. This handles collisions such as the different `geocode.py` tools.
Pairwise applications `topsApp.py`, `alos2App.py`, `stripmapApp.py` are also installed.

`insar-check --output /path/to/report` writes HTML, JSON, per-check logs, and a
rendering example. Its default location is `~/Library/Logs/insar-arm/`.
Alternatively, `bash insar-arm verify --prefix /path/to/environment` activates
the environment in a child process and runs the checks.

## Validation scope

Checks include 53 upstream CTests during build; imports and architecture;
six CLI entry points; bash/zsh selectors; ALOS command generation with four
ionosphere flag combinations; synthetic multilooking, ion filtering, SNAPHU
unwrapping and image rendering; synthetic MintPy network inversion and velocity
against known answers; and Python dependency consistency.

**A CLI help check is not end-to-end real-data validation.** None of this certifies
all sensors, scientific results, atmospheric corrections or user-selected settings.
Some optional Stanford-licensed legacy ISCE components are omitted by the public
source build. CUDA, other operating systems and interactive X11 setup are outside
this profile. SNAP is a separate desktop application.

## Failures / repeatability

Read the printed stage log. To continue a partially completed installation with
the same inputs and compiler, repeat the command with `--resume`. Completed stages
are skipped and validation runs again. Input changes require a new prefix.
Incomplete Conda creation is never overwritten or deleted automatically.

The installer never edits shell startup files or changes an existing research
project. The environment includes its own checker and hooks and does not need
the source checkout at runtime. **Keep the selected environment directory and
GCC 14 runtime**. If a custom prefix is inside the cache, do not delete that cache
with the environment still in it. This is not yet a relocatable binary distribution.

Source-based reproducibility does not imply byte-identical binaries across SDKs
and compiler versions. Updating an installed environment invalidates the tested
package set; use a new environment and rerun validation.

## Development

```sh
python3 -m unittest discover -s tests -v
```

The lightweight CI tests do not install ISCE2. Full builds must be tested on an
eligible Mac. Keep private imagery, credentials, local paths and `.work/` out of
public contributions. The installer is MIT licensed; third-party software retains
its own terms, including the upstream SNAPHU / CS2 restrictions.
