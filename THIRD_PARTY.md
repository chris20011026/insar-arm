# Third-party software and attribution

This project automates existing software. It does not claim to invent ISCE2,
MintPy, SNAPHU, or native Apple Silicon compilation of ISCE2. It does not vendor
their source trees or compiled environments into this repository.

The Apple Silicon build follows the approach documented by
[lijun99/isce2-install](https://github.com/lijun99/isce2-install), using official
ISCE2 CMake support and existing Homebrew/MacPorts Motif patches.

| Component | Source / attribution | License / notes |
|---|---|---|
| ISCE2 2.6.5 | https://github.com/isce-framework/isce2 | Upstream license notices apply; Apache-2.0 package, with third-party components retaining their notices. Public-source build uses `ISCE2_WITH_STANFORD=OFF`. |
| MintPy 1.6.4.post3 | https://github.com/insarlab/MintPy | GPL-3.0-or-later. Exact commit and archive hash pinned. |
| Motif 2.3.8 | https://sourceforge.net/projects/motif/ | LGPL licensing and notices included in upstream source. |
| Motif patches | https://github.com/Homebrew/homebrew-core and https://github.com/macports/macports-ports | Downloaded from pinned commits, retaining upstream provenance. See `locks/sources.json`. |
| SNAPHU 2.0.7 | https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/ | Custom Stanford terms in the upstream README. CS2 solver has separate noncommercial restrictions. The installer preserves the README under `$CONDA_PREFIX/share/snaphu`. |
| Conda packages | https://conda-forge.org/ | Each package has its own license and metadata; the installer license does not replace them. |
| Additional Python wheels | https://pypi.org/ | Exact distribution URLs and SHA256 hashes in `locks/wheels-osx-arm64-py312.json`; individual package licenses apply. |

SNAPHU is built with the upstream CS2 option available to retain the solver
functionality. Do not describe the complete installed environment as having a
single MIT license or as unrestricted for commercial use. The source archive's
README is the authoritative notice. ISCE2 also incorporates third-party code;
its downloaded source retains those notices.

No research imagery, account credentials, private NAS files, or personal build
logs are intended for distribution. `.work/` and generated reports are ignored.

Upstream references useful for environment maintenance:
- https://github.com/yunjunz/conda-envs
- https://github.com/conda-forge/isce2-feedstock
- https://mintpy.readthedocs.io/
