# Enterprise security and software-intake guide

ConfigReach is designed to be deployable in security-sensitive engineering environments such as banks, payment networks, regulated fintechs and large enterprises. This document maps common software-intake questions to concrete repository controls and gives security teams a reproducible way to validate the tool before internal approval.

## Security boundary

The normal ConfigReach static-analysis path is local and offline. It reads supported source and configuration files beneath the selected repository root, produces deterministic findings, and does not require a GPU, LLM, API key, telemetry endpoint or hosted service.

ConfigReach treats the repository being scanned as potentially untrusted input. Static scanning does not execute target application code. Repository-controlled file symlinks are ignored across discovery, semantic analysis, hardening and workspace detection so a repository cannot redirect the scanner to arbitrary host files. Repository-controlled baseline and trace paths are constrained to the repository root. Git revision arguments are validated before Git subprocess use, and archive snapshots use the safe extractor documented in `SECURITY.md`.

The optional `configreach trace` command is different: tracing explicitly runs the command supplied by the operator. It should therefore be treated like running that test command directly and should only be enabled for code the organization is already willing to execute.

## Data handling

Static scanning requires no outbound network access. Enterprise deployments can run the CLI or container with egress disabled. The release container is tested with `--network none`, a read-only root filesystem and a read-only mounted target repository.

ConfigReach does not intentionally persist raw runtime values during tracing. Trace evidence stores configuration key names and SHA-256-derived value fingerprints. Sensitive-looking static defaults are redacted in report output. Security teams should still classify generated reports according to their own source-code and configuration-data handling policies.

## Runtime permissions

The published container is intended to run as a dedicated non-root user. It does not require privileged mode, host networking, Docker socket access or write access to the repository for a normal `scan --no-cache` operation.

Recommended restrictive invocation:

```bash
docker run --rm \
  --network none \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=16m \
  -v "$PWD:/workspace:ro" \
  ghcr.io/sauravsingla/configreach:<approved-version> \
  scan . --no-cache --format json
```

For regulated environments, pin the image by digest after internal verification rather than relying on a floating tag.

## Supply-chain controls

The repository provides or enforces the following controls:

- MIT license and explicit project metadata;
- minimal runtime dependency surface: standard library on Python 3.11+ and the pinned `tomli` compatibility dependency on Python 3.10;
- CodeQL static analysis;
- Gitleaks full-history secret scanning;
- OpenSSF Scorecard reporting;
- Dependabot for Python, GitHub Actions and Docker;
- Python vulnerability and dependency-license audits across Python 3.10–3.14;
- container vulnerability scanning with Trivy;
- immutable commit-SHA pins for external GitHub Actions, enforced by `tools/check_workflow_pins.py`;
- reproducible wheel and source-distribution checks;
- cross-OS deterministic-output checks;
- non-root and offline/read-only container security tests;
- OCI SBOM and provenance generation for release containers;
- PyPI Trusted Publishing and Hugging Face OIDC publishing instead of long-lived publication tokens;
- a unified release workflow that verifies PyPI, GHCR and GitHub Release artifacts before moving the floating `v0` Action tag.

## Enterprise intake checklist

An intake team can use the following sequence without trusting project claims:

1. **Pin the source revision.** Record the approved Git commit and release tag.
2. **Review license/provenance.** Confirm `LICENSE`, `pyproject.toml`, `CITATION.cff` and dependency-license audit results.
3. **Run source security checks.** Review CodeQL, Gitleaks, dependency-review and OpenSSF Scorecard results for the approved revision.
4. **Rebuild internally.** Build the wheel and/or image from the approved source in the organization's own CI environment.
5. **Verify dependencies.** Run `pip check`, `pip-audit`, internal SCA tooling and any organization-specific malware scanner.
6. **Verify the container.** Confirm the image runs non-root, scan it with the organization's container scanner, inspect the SBOM/provenance, and pin the approved digest.
7. **Verify offline behavior.** Run ConfigReach with egress disabled against a non-sensitive sample repository.
8. **Verify untrusted-input boundaries.** Run `pytest -q tests/test_enterprise_security.py tests/test_python_compat_security.py`.
9. **Run functional validation.** Reproduce the committed 50,000-case curated benchmark using `.github/workflows/curated-50k-validation.yml` or the equivalent commands locally.
10. **Publish internally.** Promote the approved wheel/image to an internal registry and permit only the internally approved version/digest.

## Recommended enterprise deployment profile

For high-assurance environments:

- disable outbound network access for scan jobs;
- mount source repositories read-only;
- run the container as the image's non-root user;
- use `--no-cache` when no persistent scanner state is desired;
- keep optional plugins disabled unless separately reviewed;
- do not use `trace` on untrusted code;
- pin release artifacts by exact version and container digest;
- mirror approved artifacts into internal package/container registries;
- rerun SCA, secret scanning and container scanning on every version upgrade.

## Security claims and limits

The controls above reduce software-supply-chain and untrusted-input risk; they do not make ConfigReach a sandbox, malware scanner, secrets manager or runtime policy engine. Static scanning deliberately does not execute the target application. Optional tracing does execute an operator-supplied command and must be governed accordingly.

The 50,000-case benchmark is controlled, programmatically generated from explicit version-controlled scenario families, and deterministically labelled. Its measured result is evidence for that committed benchmark, not a claim of universal real-world accuracy.

See also [`SECURITY.md`](../SECURITY.md), [`docs/threat-model.md`](threat-model.md) and the repository's security workflows under [`.github/workflows`](../.github/workflows/).
