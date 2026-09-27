# Native Conda packaging — beta 1

The binary release installs ISCE2 and the complete tested environment without local compilation or Homebrew runtime libraries. The stage 1 `install.sh` remains a source-build fallback. Start with [binary installation](../docs/BINARY_INSTALL.md) and [validation scope](../docs/BINARY_VALIDATION.md).

## Packages

- `insar-arm-motif` 2.3.8: pinned Motif source with the established Homebrew / MacPorts patches.
- `isce2` 2.6.5 build 1: Conda C/C++/Fortran toolchain, CMake, three pair processors and three stacks. Includes upstream source archive and third-party notices.
- `insar-arm-snaphu-cli` 2.0.7: standalone executable, retaining upstream CS2 functionality and its noncommercial restrictions.
- `insar-arm` 0.2.0b1: MintPy and scientific dependencies, activation hooks, selectors, fonts and standalone numerical checker.

The four artifact hashes are in `beta1-artifacts.json`. Exact tested runtime dependencies are in `../locks/insar-arm-0.2.0b1-osx-arm64.lock`; prototype JSON files document the earlier core-only experiment.

## Build

Use a separate native Conda environment with conda-build and conda-index. `build-tools-osx-arm64.lock` records the tool versions. Building needs Apple Command Line Tools / SDK; installing the released binaries does not invoke a compiler.

```sh
CONDA_BUILD_EXE=/path/to/build-env/bin/conda-build bash packaging/build-local.sh
```

Outputs default to ignored `.work/stage2-build`. The script builds sequentially to avoid shared Conda-cache locks and never installs into a research environment. `prepare-integration-recipe.py` copies the current checker and activation code into a self-contained recipe. SDK selection can be overridden with `CONDA_BUILD_SYSROOT`; other build inputs are in `conda_build_config.yaml` and each recipe.

## Release and verification

1. Build the packages and pass their package tests.
2. Install into a fresh prefix and run the complete `insar-check` suite.
3. Build a channel with `build-channel.py --output NEW_DIRECTORY` followed by explicit `.conda` package paths. Inspect the generated indexes and hashes before publishing.
4. Publish only those channel files to `gh-pages`. Keep package filenames immutable; a changed binary requires a new build number.
5. Record exact public URLs and checksums in the explicit lock, and verify installation on a fresh hosted ARM Mac with the binary-validation workflow.
6. Run `tools/package_release.py` for the small installer ZIP and `bundle-sources.py --cache SOURCE_CACHE --output NEW_SOURCE_ARCHIVE` for corresponding upstream archives, recipes and patches. Publish checksums with both.

Source origins and license details are in `../THIRD_PARTY.md` and `../locks/sources.json`. This is a community build, not an official conda-forge ISCE2 ARM distribution. It follows official ISCE2 CMake support and established ARM build work; it does not claim to invent that support.

[Conda relocation documentation](https://docs.conda.io/projects/conda-build/en/stable/resources/make-relocatable.html) describes prefix rewriting. `audit-prefix.py` checks native architecture and absolute load paths; actual numerical tests are required in addition. Core-only experiments can use `check-core.py`; release validation must use the full installed checker.
