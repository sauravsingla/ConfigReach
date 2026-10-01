# Security policy

## Supported versions

Security fixes are applied to the latest published ConfigReach release. Pre-1.0 users should upgrade to the newest release before reporting a version-specific issue.

ConfigReach supports Python 3.10 through 3.14 at the package level. Compatibility support does not extend CPython's own upstream security-support lifetime, so security-sensitive deployments should use a maintained Python release appropriate for their environment.

## Reporting

Please report potential security vulnerabilities privately through GitHub's security advisory mechanism rather than a public issue. Include the affected ConfigReach version, a minimal reproduction and the security impact where possible.

## Data handling and repository boundaries

The normal static analyzer reads supported files from the target repository and does not make network requests or execute target application code. Repository scans ignore repository-controlled file symlinks across discovery, semantic analysis, precision hardening and workspace detection so a repository cannot redirect the scanner to arbitrary host files. Repository-controlled baseline/trace paths are constrained to the repository root. Git revision arguments are validated before they are passed to Git subprocesses. Archive snapshots are extracted with ConfigReach's cross-version safe extractor, which rejects traversal, absolute/drive paths, links and special members on every supported Python version.

Dynamic Python tracing is explicit opt-in. `configreach trace` executes the command supplied by the operator and must therefore only be used where that command is already trusted to run. Trace evidence stores configuration key names plus SHA-256-derived value fingerprints; it does not intentionally persist raw runtime values. Sensitive-looking static defaults are redacted in report output.

ConfigReach is a developer-analysis tool, not a sandbox, malware scanner, secrets manager or substitute for a dedicated secret scanner.

## Supply-chain controls

The repository uses:

- CodeQL analysis;
- Gitleaks full-history secret scanning;
- OpenSSF Scorecard reporting;
- Dependabot for Python, GitHub Actions and Docker updates;
- GitHub pull-request dependency review when the repository Dependency Graph is available;
- enforced `pip-audit` vulnerability checks and dependency-license checks across Python 3.10 through 3.14;
- Trivy scanning that fails the container security gate on fixed HIGH/CRITICAL findings;
- immutable commit-SHA pins for external GitHub Actions, enforced by `tools/check_workflow_pins.py`;
- read-only validation workflows that verify committed evidence rather than writing generated results directly to `main`;
- security regressions for symlink isolation, no-network core imports and prohibition of `shell=True`/`os.system` in core code;
- reproducible wheel/source-distribution verification;
- post-publication PyPI install/CLI verification on Python 3.10 through 3.14 before a GitHub Release is created;
- a dedicated non-root release container and an offline/read-only container smoke test;
- OCI SBOM and provenance generation for container releases;
- PyPI Trusted Publishing/OIDC rather than a long-lived PyPI token;
- Hugging Face Trusted Publishing/OIDC rather than a long-lived Hub token.

Release artifacts and container images are built by GitHub Actions from the public repository. High-assurance deployments should independently rebuild from a pinned source revision, run their own SCA/malware/container tooling and mirror an approved wheel/image into internal registries.

See [`docs/enterprise-security.md`](docs/enterprise-security.md) for an enterprise software-intake checklist and restrictive deployment profile, and `docs/threat-model.md` for the broader analysis threat model.
