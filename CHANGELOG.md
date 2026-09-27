# Changelog

## 0.2.0b1 — Native Conda binary prerelease

- Four relocatable osx-arm64 packages with a public Conda channel.
- Exact 381-package lock, new-prefix installer and automatic numerical validation.
- Integrated MintPy 1.6.4, environment selectors, font setup and standalone checker.
- Conda compiler/runtime build; no Homebrew libraries needed by the tested environment.
- Corresponding upstream source bundle and third-party notices, including CS2 restrictions.
- Independent hosted ARM installation workflow and explicit validation scope.

## 0.1.0 — Stage 1 public-test candidate

- New-environment-only Apple Silicon installation with fixed upstream inputs.
- Native Motif / ISCE2 / SNAPHU compilation and pinned MintPy installation.
- Environment-local activation and three Stack selectors plus a MintPy selector.
- Stack Python package root and same-name command routing configured automatically.
- Resumable stages with ownership, input identity and download integrity checks.
- Standalone installed validation tool with HTML / JSON diagnostics.
- Synthetic numerical checks and explicit scientific validation scope.
