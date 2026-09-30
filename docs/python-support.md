# Python compatibility and lifecycle

ConfigReach supports CPython **3.10, 3.11, 3.12, 3.13 and 3.14**. The supported-version contract is enforced by package metadata and CI jobs that install ConfigReach, run the full tests and CLI integrations, build/install distribution artifacts, exercise example plugins, and build/smoke-test the Dockerfile for every listed interpreter.

## Runtime compatibility

| Python | ConfigReach support | TOML implementation | Upstream Python lifecycle (2026-09-30) |
|---|---|---|---|
| 3.10 | Tested | `tomli` 2.2.1 backport | Security-only; scheduled EOL October 2026 |
| 3.11 | Tested | standard-library `tomllib` | Security fixes |
| 3.12 | Tested | standard-library `tomllib` | Security fixes |
| 3.13 | Tested | standard-library `tomllib` | Bugfix/security fixes |
| 3.14 | Tested | standard-library `tomllib` | Bugfix/security fixes |

ConfigReach compatibility with an interpreter does **not** extend that interpreter's upstream security-support lifetime. Production users should prefer an actively maintained Python release appropriate for their deployment policy.

## Dependency policy

ConfigReach keeps runtime dependencies minimal. Python 3.10 installs the pinned `tomli==2.2.1` backport because `tomllib` entered the standard library in Python 3.11. Python 3.11 and newer have no third-party runtime dependency from ConfigReach itself.

Build and development tooling is pinned to versions that support the complete Python 3.10-3.14 matrix. This keeps CI reproducible and prevents resolver drift from silently changing the release toolchain.

## Optional parser plugins

The example tree-sitter plugins use pinned parser/grammar versions compatible with Python 3.10-3.14. CI imports, discovers and executes these plugins on every supported interpreter.

## Archive safety

ConfigReach does not rely on unrestricted `tarfile.extractall()` for repository snapshots. A shared compatibility helper accepts only regular files/directories and rejects absolute paths, drive-qualified paths, `..` traversal, symbolic links, hard links, devices and other special members before writing anything to disk. This keeps the same traversal protections on Python 3.10 and 3.11 as on newer runtimes.
