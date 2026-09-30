# Security policy

## Supported versions

Security fixes are applied to the latest published ConfigReach release. Pre-1.0 users should upgrade to the newest release before reporting a version-specific issue.

ConfigReach supports Python 3.10 through 3.14 at the package level. Compatibility support does not extend CPython's own upstream security-support lifetime, so security-sensitive deployments should use a maintained Python release appropriate for their environment.

## Reporting

Please report potential security vulnerabilities privately through GitHub's security advisory mechanism rather than a public issue. Include the affected ConfigReach version, a minimal reproduction and the security impact where possible.

## Data handling and repository boundaries

The static analyzer reads files from the target repository and does not make network requests. Repository scans do not follow file symlinks outside the repository root, and repository-controlled baseline/trace paths are constrained to that root. Git revision arguments are validated before they are passed to Git subprocesses. Archive snapshots are extracted with ConfigReach's cross-version safe extractor, which rejects traversal, absolute/drive paths, links and special members on every supported Python version.

Dynamic Python tracing is explicit opt-in and stores configuration key names plus SHA-256-derived value fingerprints; it does not intentionally persist raw runtime values. Sensitive-looking static defaults are redacted in report output.

ConfigReach is a developer-analysis tool, not a secrets manager or a substitute for a dedicated secret scanner.

## Supply-chain controls

The repository uses:

- CodeQL analysis;
- OpenSSF Scorecard reporting;
- Dependabot for Python, GitHub Actions and Docker updates;
- GitHub pull-request dependency review when the repository Dependency Graph is available;
- enforced `pip-audit` vulnerability checks and dependency-license checks across Python 3.10 through 3.14;
- Trivy scanning for the published GHCR image;
- pinned compatibility-sensitive build/test dependencies and immutable SHA pins for release-critical GitHub Actions;
- reproducible wheel/source-distribution verification;
- post-publication PyPI install/CLI verification on Python 3.10 through 3.14 before a GitHub Release is created;
- OCI SBOM and provenance generation for container releases;
- PyPI Trusted Publishing/OIDC rather than a long-lived PyPI token;
- Hugging Face Trusted Publishing/OIDC rather than a long-lived Hub token.

Release artifacts and container images are built by GitHub Actions from the public repository. See `docs/threat-model.md` for the broader analysis threat model.
