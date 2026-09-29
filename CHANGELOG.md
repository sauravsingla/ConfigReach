# Changelog

All notable ConfigReach changes are documented here. The project follows semantic versioning while pre-1.0 APIs remain explicitly marked as evolving.

## [Unreleased]

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

[Unreleased]: https://github.com/sauravsingla/ConfigReach/compare/v0.9.2...HEAD
[0.9.2]: https://github.com/sauravsingla/ConfigReach/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/sauravsingla/ConfigReach/releases/tag/v0.9.1
[0.9.0]: https://github.com/sauravsingla/ConfigReach/releases/tag/v0.9.0
