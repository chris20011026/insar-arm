# InSAR ARM 0.2.0 beta 1 — binary installation

A public beta for native Apple Silicon macOS 14.5+. Requires native ARM Conda. No Homebrew compiler or local ISCE2 compilation is needed. SNAP remains a separate desktop application.

Download `insar-arm-0.2.0b1.zip` from the [release](https://github.com/chris20011026/insar-arm/releases/tag/v0.2.0-beta.1), extract it, open a terminal in the folder, and run:

```sh
bash install-binary.sh --prefix "$HOME/conda-envs/insar_arm_beta"
conda activate "$HOME/conda-envs/insar_arm_beta"
use_alosStack
```

The installer uses an explicit package lock, refuses existing prefixes and runs `insar-check`. Use a new path without spaces. Failed partial environments are not deleted automatically.

Alternatively, let Conda solve the dependencies (these can change over time):

```sh
conda create -n insar_arm_beta --strict-channel-priority --override-channels \
  -c https://chris20011026.github.io/insar-arm -c conda-forge insar-arm=0.2.0b1
conda activate insar_arm_beta
insar-check
```

Select `use_alosStack`, `use_topsStack`, `use_stripmapStack` or `use_mintpy` as needed. Pair processors are `alos2App.py`, `topsApp.py` and `stripmapApp.py`. Activation is scoped to the current shell; no shell startup files are edited.

Includes ISCE2 2.6.5, conda-forge MintPy 1.6.4, SNAPHU CLI 2.0.7, Python 3.12 and NumPy 1.26.4. The separate `snaphu 0.4.1` Conda package is a Python binding. This release is CPU-only and does not target Intel Macs, Windows or Linux.

See [validation coverage](BINARY_VALIDATION.md). Successful CLI startup and synthetic numerical checks do not certify real-data processing for every sensor. Independent physical-Mac validation remains outstanding. Online data services may require your own credentials.

The helper code is MIT; third-party licenses remain separate. **CS2-containing SNAPHU/ISCE2 components carry noncommercial restrictions.** The release includes corresponding source archives, patches, build tools and checksums in `insar-arm-0.2.0b1-sources.tar.gz`. ISCE2 also installs a full upstream source snapshot under `share/isce2`; SNAPHU retains its original README. Dependencies are downloaded directly from conda-forge.

To help validate another Mac, run `insar-check --output "$HOME/insar-validation"`. Reports contain local paths: review before sharing. Include chip, macOS version and failed checks, without private imagery or credentials.
