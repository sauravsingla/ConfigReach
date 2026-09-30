# Roadmap

## v0.1 — deterministic foundation ✅
- Python AST discovery for `os.getenv`, `os.environ`, argparse and comparisons.
- Cross-language environment-read detection for JavaScript/TypeScript, Go, Java, Rust, Ruby and PHP.
- dotenv, JSON, TOML, INI, YAML, Terraform and Make declaration discovery.
- Test-reference and static test-value evidence.
- text, JSON, Markdown and SARIF reporters.

## v0.2 — repository-scale coverage foundation ✅
- Pydantic settings and generic feature-flag discovery.
- Dockerfile, properties, Helm-values and GitHub Actions configuration discovery.
- Boolean/value coverage and deterministic pairwise key-combination coverage.
- Legacy baselines, persistent cache and package-root detection for monorepos.
- Searchable standalone HTML graph, PR comments and entry-point plugin SDK.
- Deterministic findings for untested values, sensitive defaults and naming inconsistencies.

## v0.3 — semantic coverage and PR deltas ✅
- Function-scoped Python configuration dependency graph.
- Branch source provenance.
- `Literal`, Enum and bool annotation domains for Python settings.
- Explicit pairwise value-state coverage based on test scenarios.
- Merge-base vs current-tree PR scanning for newly introduced keys, removed keys and changed value/default/branch domains.
- Findings for explicit default-only testing and global-environment test mutation.
- Initial cross-version cache schema invalidation and Python 3.11–3.13 CI coverage (later expanded to Python 3.10–3.14).

## v0.4 — deeper language and framework semantics ✅
- Function-scoped deterministic JavaScript/TypeScript and Go adapters while preserving a core without optional parser dependencies.
- Java Spring discovery for `@Value`, `Environment.getProperty`, `@ConfigurationProperties` and common feature-flag calls.
- .NET/C# discovery for environment variables, `IConfiguration`, `GetValue` defaults and feature flags.
- JSON Schema finite-domain/default/validator extraction.
- Terraform bool and finite validation-domain extraction.
- Changed-line PR dependency slicing with file-level fallback only where line provenance is unavailable.
- Root-level test-name detection for Go, Java, .NET, Python and JS/TS conventions.

## v0.5 — deterministic testing guidance ✅
- `configreach plan` for bounded deterministic 1-wise, 2-wise and 3-wise configuration planning.
- Greedy covering-array style selection with deterministic lexicographic tie-breaking.
- Existing test-scenario evidence removed from the required interaction set before planning.
- CPU-safety bounds for domain size, interaction count and generated case count.
- Sensitive-looking configuration excluded from suggested assignments.
- Structured JSON fixture suggestions plus text and Markdown renderers.
- Single-key missing finite values remain actionable even when no multi-key dependency scope is available.

## v0.6 — scale and ecosystem depth ✅
- `configreach workspace` with manifest-defined workspace detection and independent persistent cache boundaries.
- Parent workspaces ignore nested workspace roots, preventing double counting while preserving incremental invalidation.
- Richer deterministic validator extraction for Zod, Java Bean Validation, extended JSON Schema and Terraform constraints.
- Deterministic fixture exporters for pytest, Jest/TypeScript, Go and shell harnesses.
- Cross-version regression coverage for workspace cache invalidation and fixture generation.

## v0.7 — adapter ecosystem and reproducibility ✅
- Adapter API v1 with explicit compatibility version, parser identity, determinism declaration and capability metadata.
- `configreach adapters` machine-readable diagnostics for built-ins and installed plugins.
- Optional parser-backed tree-sitter JavaScript adapter example kept outside the core package dependency set.
- `configreach reproduce` canonical SHA-256 verification across repeated uncached scans.
- Cross-platform reproducibility workflow comparing Ubuntu, macOS and Windows canonical digests.
- Versioned built-in adapter capability schema.

## v0.8 — stabilization and compatibility ✅
- Central machine-readable schema registry for reports, workspaces, plans, reproducibility output and adapter capabilities.
- `configreach schema` compatibility diagnostics plus validation of saved JSON artifacts.
- Golden schema fixtures, including supported legacy report v3, to catch accidental contract breaks in CI.
- Deterministic JUnit 5 and .NET/xUnit fixture exporters without synthesized assertions.
- Full-engine synthetic polyglot performance budget with a dedicated GitHub-hosted CPU workflow.
- Explicit migration/compatibility guidance for downstream consumers.

## v0.9 — release hardening ✅
- Wheel and source-distribution reproducibility harness with exact SHA-256 and canonical archive-content comparison.
- `configreach release` manifests for independently inspecting built artifacts.
- Dedicated release workflow that builds twice, verifies reproducibility, installs the produced wheel and smoke-scans a fixture.
- Additional Adapter API v1 examples: parser-backed tree-sitter Go plus a custom `.featureflags` configuration provider.
- Offline compatibility corpus covering Python/env, polyglot deployment, Spring/.NET and JSON-Schema-style configuration surfaces.
- Provenance-rich performance history artifacts retained from GitHub-hosted CPU budget runs.
- Python 3.10–3.14 runtime, packaging, plugin, Action and container compatibility matrices, with `tomli` used only as the Python 3.10 backport.

## v1.0
- Stable report, workspace and planning schemas.
- Stable plugin contract based on adapter API v1 feedback.
- Versioned adapter capability matrix with compatibility policy.
- Reproducibility, release-artifact and performance suites as required release gates.
- Formal deprecation policy for machine-readable schemas and Adapter API changes.
