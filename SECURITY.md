# Security policy

## Supported versions

Security fixes are applied to the latest published ConfigReach release. Pre-1.0 users should upgrade to the newest release before reporting a version-specific issue.

## Reporting

Please report potential security vulnerabilities privately through GitHub's security advisory mechanism rather than a public issue. Include the affected ConfigReach version, a minimal reproduction and the security impact where possible.

## Data handling

The static analyzer reads files from the target repository and does not make network requests. Dynamic Python tracing is explicit opt-in and stores configuration key names plus SHA-256-derived value fingerprints; it does not intentionally persist raw runtime values. Sensitive-looking static defaults are redacted in report output.

ConfigReach is a developer-analysis tool, not a secrets manager or a substitute for a dedicated secret scanner.

## Supply-chain controls

The repository uses:

- CodeQL analysis;
- OpenSSF Scorecard reporting;
- Dependabot for Python, GitHub Actions and Docker updates;
- pull-request dependency review;
- Trivy scanning for the published GHCR image;
- reproducible wheel/source-distribution verification;
- OCI SBOM and provenance generation for container releases;
- PyPI Trusted Publishing/OIDC rather than a long-lived PyPI token;
- Hugging Face Trusted Publishing/OIDC rather than a long-lived Hub token.

Release artifacts and container images are built by GitHub Actions from the public repository. See `docs/threat-model.md` for the broader analysis threat model.
