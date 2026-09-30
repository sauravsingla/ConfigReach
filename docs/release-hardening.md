# Release hardening

ConfigReach v0.9 adds deterministic checks around the artifacts that would be published to a Python package index or attached to a GitHub release. These checks are development/release tooling only. Python 3.11+ uses the standard library at runtime; Python 3.8–3.10 adds only the pinned `tomli` TOML backport.

## Build twice and compare

```bash
python -m pip install -e ".[dev]"
python tools/release_repro.py --output release-repro.json --artifacts-dir dist
```

The harness sets a fixed `SOURCE_DATE_EPOCH`, `PYTHONHASHSEED=0` and UTC timezone, builds a wheel and source distribution twice in separate temporary directories, then normalizes only the **sdist archive container metadata** before comparison. The normalization fixes tar member mtime/owner/group/PAX metadata plus gzip mtime; file names, modes, links and file contents are preserved. This closes timestamp/host drift that can remain in otherwise identical setuptools sdists.

The harness compares:

- the exact SHA-256 of each final publishable artifact,
- a canonical SHA-256 of the files contained inside the wheel/sdist, ignoring archive timestamp/order metadata.

The release gate requires **exact byte reproducibility**. Canonical content comparison is retained as a diagnostic so a future packaging-tool change can distinguish container metadata drift from an actual content change.

## Inspect an existing release directory

```bash
configreach release dist
configreach release dist --format json --output release-manifest.json
```

Compare two prebuilt artifact directories:

```bash
configreach release dist-a --compare dist-b
```

`--allow-byte-differences` exists for diagnostics only; the repository release workflow does not use it.

## GitHub release gate

`.github/workflows/release-reproducibility.yml` performs the following on a GitHub-hosted CPU runner:

1. installs only pinned development build tools,
2. builds wheel and sdist twice,
3. normalizes deterministic sdist container metadata,
4. requires exact artifact hashes to match,
5. writes a machine-readable release manifest,
6. force-installs the generated wheel without dependencies,
7. runs a ConfigReach smoke scan from that installed wheel,
8. uploads the wheel, sdist and reproducibility evidence as workflow artifacts.

The publication workflow additionally installs the package from public PyPI on Python 3.8 through 3.14, runs `pip check`, validates package metadata and exercises the CLI before creating the GitHub Release/tag. A `pyproject.toml` metadata-only change does not publish a release unless the project version actually changes.

## Performance history

The Performance workflow produces `performance-history.json` with commit SHA, workflow run identifiers, runner OS, Python version, machine architecture and the synthetic polyglot budget result. GitHub retains each run's history artifact so regressions can be compared across commits without introducing telemetry or a hosted metrics service.
