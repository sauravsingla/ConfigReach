# Python compatibility and lifecycle

ConfigReach supports CPython **3.8, 3.9, 3.10, 3.11, 3.12, 3.13 and 3.14**. The supported-version contract is enforced by the package metadata and by CI jobs that install ConfigReach, run the full tests and CLI integrations, build/install distribution artifacts, exercise example plugins, and build/smoke-test the Dockerfile for every listed interpreter.

## Runtime compatibility

| Python | ConfigReach support | TOML implementation | Upstream Python lifecycle (2026-09-30) |
|---|---|---|---|
| 3.8 | Tested | `tomli` 2.2.1 backport | End-of-life |
| 3.9 | Tested | `tomli` 2.2.1 backport | End-of-life |
| 3.10 | Tested | `tomli` 2.2.1 backport | Security-only; scheduled EOL October 2026 |
| 3.11 | Tested | standard-library `tomllib` | Security fixes |
| 3.12 | Tested | standard-library `tomllib` | Security fixes |
| 3.13 | Tested | standard-library `tomllib` | Bugfix/security fixes |
| 3.14 | Tested | standard-library `tomllib` | Bugfix/security fixes |

ConfigReach compatibility with an interpreter does **not** extend that interpreter's upstream security-support lifetime. Python 3.8 and 3.9 no longer receive CPython security fixes, so production users should prefer a maintained Python release even though ConfigReach continues to test compatibility with those versions.

## Dependency policy

ConfigReach keeps runtime dependencies minimal. Python 3.8-3.10 install the pinned `tomli==2.2.1` backport because `tomllib` entered the standard library in Python 3.11. Python 3.11 and newer have no third-party runtime dependency from ConfigReach itself.

Build and development tooling uses environment markers so older interpreters receive the newest pinned toolchain line that still supports them, while newer interpreters use the current pinned toolchain. This prevents the resolver from selecting releases whose own `Requires-Python` excludes Python 3.8 or 3.9.

## Optional parser plugins

The example tree-sitter plugins use interpreter-specific, pinned parser/grammar versions. Python 3.8 uses the final compatible 0.21-series bindings/grammars and the adapter bridges the legacy parser-construction API. Python 3.9 and Python 3.10+ use newer pinned parser/grammar lines. CI imports, discovers and executes these plugins on every supported interpreter.

## Archive safety on older Python

ConfigReach does not fall back to unrestricted `tarfile.extractall()` on pre-3.12 runtimes. Repository snapshots are extracted by a shared compatibility helper that accepts only regular files/directories and rejects absolute paths, drive-qualified paths, `..` traversal, symbolic links, hard links, devices and other special members before writing anything to disk.
