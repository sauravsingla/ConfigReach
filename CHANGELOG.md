# Changelog

All notable ConfigReach changes are documented here. The project follows semantic versioning while pre-1.0 APIs remain explicitly marked as evolving.

## [Unreleased]

## [0.9.5] - 2026-10-01

### Added
- Added the committed 50,000-case curated benchmark with deterministic ground-truth labels and production-engine scoring evidence.
- Added synchronized Hugging Face Space and Dataset publication for the curated 50K benchmark.
- Added an enterprise security gate with full-history secret scanning, workflow-pin policy enforcement, untrusted-repository boundary regressions and non-root/offline container tests.
- Added `docs/enterprise-security.md` with a regulated-enterprise software-intake checklist and restrictive deployment profile.

### Changed
- Made the release container run as a dedicated non-root user and verify non-root operation after publication.
- Converted 50K, measured-accuracy and reviewed validation evidence workflows to read-only reproducibility gates rather than allowing generated evidence to be pushed directly to `main`.
- Pinned external GitHub Actions used by project workflows to immutable commit SHAs and added an automated policy check to prevent mutable references from returning.
- Replaced Hugging Face CLI bootstrap via remote shell script with a pinned `huggingface_hub` package installation.
- Extended the release synchronizer so PyPI, GHCR, GitHub Release/`v0`, GitHub Pages, Hugging Face Space and the Hugging Face 50K Dataset are refreshed from the same released source.

### Security
- Closed a repository-file symlink boundary gap in later semantic and precision-hardening passes by propagating symlink ignores before those passes and excluding symlinked workspace/.NET manifests.
- Added regression coverage proving production scans do not read repository-controlled file symlinks outside the scan root.
- Added core invariants that reject network-client imports, `os.system` and `subprocess(..., shell=True)` in the scanner core.
- Made fixed HIGH/CRITICAL container vulnerabilities fail the Trivy security gate instead of remaining report-only.
- Added full-history Gitleaks secret scanning and explicit enterprise data-handling/runtime-execution guidance.

## [0.9.4] - 2026-09-30

### Added
- Added first-class CPython 3.10, 3.11, 3.12, 3.13 and 3.14 compatibility matrices across core tests, wheel/sdist validation, example plugins, the composite GitHub Action and Docker builds.
- Added mandatory cross-version `pip-audit` vulnerability checks and dependency-license policy checks for the supported Python matrix.
- Added post-publication PyPI installation, metadata and CLI verification across every supported Python version before the GitHub Release is created.

### Changed
- Set package metadata and documentation support policy to Python 3.10–3.14, intentionally excluding Python 3.8 and 3.9.
- Python 3.10 uses the pinned `tomli` backport while Python 3.11+ uses standard-library `tomllib`.
- Pinned release-critical GitHub Actions and compatibility-sensitive build/test dependencies.
- Hardened the release workflow so `pyproject.toml` metadata-only changes cannot accidentally republish an unchanged package version.

### Security
- Replaced unrestricted archive extraction fallbacks with a cross-version safe extractor that rejects traversal, absolute/drive paths, links, devices and special members.
- Prevented repository scans from following file symlinks outside the target repository.
- Constrained repository-controlled config/baseline paths to the repository root and validated Git revision arguments before subprocess use.
- Added regression coverage for archive traversal/link attacks, symlink escapes, path escapes and Git option injection.

## [0.9.3] - 2026-09-30

### Added
- Published ConfigReach Configuration Coverage to GitHub Marketplace.
- Added Zenodo archive/citation metadata and reusable distribution launch materials.

### Changed
- Synchronized package, runtime, citation, documentation and Hugging Face source-version metadata with the v0.9.3 release.

## [0.9.2] - 2026-09-29

### Added
- OpenSSF Scorecard, Dependabot, dependency review, container vulnerability scanning and GitHub Action smoke tests.
- GitHub Container Registry distribution with multi-architecture images, SBOM and provenance.
- Unified release automation for PyPI, GHCR, GitHub Releases, the floating `v0` GitHub Action tag, documentation and Hugging Face synchronization.
- Marketplace-ready GitHub Action metadata and installation documentation.

### Changed
- Hardened deterministic analysis for statically resolvable Python/Go environment-variable indirection and JavaScript `process.env` destructuring.
- Tightened feature-flag `variation()` detection to reduce unrelated-method false positives.
- Excluded standard `package.json` and `pyproject.toml` project metadata from runtime configuration declarations while preserving custom configuration sections.
- Branch-state inference now requires actual branch evidence rather than treating every boolean declaration as a branch.
- The committed hand-labelled benchmark now measures 37 labelled decisions with zero false positives or false negatives on that corpus; this is corpus-specific evidence, not a universal accuracy claim.
- Release publishing is now driven by a single version bump on `main`, avoiding duplicate tag-triggered release runs.

## [0.9.1] - 2026-09-29

### Added
- PyPI discoverability metadata and real-world developer search examples.
- Published hand-labelled precision/recall benchmark and 10-project real-world validation evidence.
- GitHub Pages and Hugging Face Space distribution.
- GitHub Container Registry package distribution.

### Changed
- Improved release metadata and synchronized GitHub/PyPI release information.

## [0.9.0] - 2026-09-29

### Added
- Reproducible wheel and normalized source-distribution build gates.
- Release manifests and compatibility corpus.
- Optional parser-backed adapter examples.
- Pinned release toolchain and independent wheel installation verification.

## [0.8.0]

### Added
- Explicit schema compatibility registry and structural validation CLI.
- JUnit and xUnit deterministic fixture exporters.
- Full semantic-engine polyglot performance budget.

## [0.7.0]

### Added
- Adapter API v1 with deterministic/capability metadata.
- Cross-platform reproducibility verification.
- Optional tree-sitter JavaScript adapter example.

[Unreleased]: https://github.com/sauravsingla/ConfigReach/compare/v0.9.5...HEAD
[0.9.5]: https://github.com/sauravsingla/ConfigReach/compare/v0.9.4...v0.9.5
[0.9.4]: https://github.com/sauravsingla/ConfigReach/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/sauravsingla/ConfigReach/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/sauravsingla/ConfigReach/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/sauravsingla/ConfigReach/releases/tag/v0.9.1
[0.9.0]: https://github.com/sauravsingla/ConfigReach/releases/tag/v0.9.0
