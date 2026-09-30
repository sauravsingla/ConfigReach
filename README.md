# ConfigReach

> **High code coverage does not guarantee high configuration coverage. ConfigReach measures the gap.**

**ConfigReach is a deterministic, CPU-only, offline configuration coverage analyzer that shows which runtime configuration inputs, values, branches and important combinations your tests actually exercise.** Think **Codecov for configuration space**.

[![PyPI](https://img.shields.io/pypi/v/configreach.svg)](https://pypi.org/project/configreach/)
[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Space-FFD21E?logo=huggingface&logoColor=000)](https://huggingface.co/spaces/sauravsingla08/ConfigReach)
[![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Dataset-FFD21E?logo=huggingface&logoColor=000)](https://huggingface.co/datasets/sauravsingla08/configreach-validation)
[![CI](https://github.com/sauravsingla/ConfigReach/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/ConfigReach/actions/workflows/ci.yml)
[![CodeQL](https://github.com/sauravsingla/ConfigReach/actions/workflows/codeql.yml/badge.svg)](https://github.com/sauravsingla/ConfigReach/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/sauravsingla/ConfigReach/badge)](https://scorecard.dev/viewer/?uri=github.com/sauravsingla/ConfigReach)
[![Reproducibility](https://github.com/sauravsingla/ConfigReach/actions/workflows/reproducibility.yml/badge.svg)](https://github.com/sauravsingla/ConfigReach/actions/workflows/reproducibility.yml)
[![Performance](https://github.com/sauravsingla/ConfigReach/actions/workflows/performance.yml/badge.svg)](https://github.com/sauravsingla/ConfigReach/actions/workflows/performance.yml)
[![Validation](https://github.com/sauravsingla/ConfigReach/actions/workflows/validation.yml/badge.svg)](https://github.com/sauravsingla/ConfigReach/actions/workflows/validation.yml)
[![GHCR](https://img.shields.io/badge/GHCR-configreach-blue.svg)](https://github.com/sauravsingla/ConfigReach/pkgs/container/configreach)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8–3.14](https://img.shields.io/badge/Python-3.8%E2%80%933.14-blue.svg)](https://www.python.org/)
[![Runtime dependencies: minimal](https://img.shields.io/badge/runtime%20dependencies-minimal-brightgreen.svg)](pyproject.toml)

ConfigReach needs **no GPU, no LLM, no API key, no hosted service, no telemetry and no paid dependency**. Python 3.11+ uses only the standard library at runtime; Python 3.8–3.10 adds the pinned `tomli` backport for TOML parsing. Static analysis does not execute the target repository. Machine-readable results are deterministic for the same repository state and configuration.

![ConfigReach terminal example](docs/demo.svg)

## Real-world validation & measured accuracy

ConfigReach publishes reproducible validation evidence instead of relying only on feature claims.

### Frozen external holdout — 11 repositories, 9 ecosystems

The current frozen holdout scans **11 pinned public open-source repositories** selected before ConfigReach results were examined. The corpus is disjoint from the earlier 10-project validation baseline and spans Python, JavaScript/TypeScript, Go/Kubernetes, Java/Spring, .NET/C#, Rust, Ruby, PHP and Terraform.

- **11 / 11 repository jobs completed successfully**
- **96,845** configuration inputs discovered
- **5,539** inputs with detected test/runtime evidence
- **5.72%** aggregate observed configuration coverage
- **34,933.6s (~9.70 cumulative scanner-hours)** across independently executed jobs; this is the sum of per-repository scanner runtimes, not workflow wall-clock elapsed time
- **0** repositories overlap the earlier validation baseline
- All targets are pinned to immutable upstream commit SHAs

| Ecosystem | Projects | Configs | Covered | Observed coverage |
|---|---:|---:|---:|---:|
| Python | 2 | 47,346 | 1,277 | 2.70% |
| JavaScript/TypeScript | 2 | 18,151 | 809 | 4.46% |
| Go/Kubernetes | 1 | 5,107 | 242 | 4.74% |
| Java/Spring | 1 | 4,464 | 673 | 15.08% |
| .NET/C# | 1 | 16,780 | 2,199 | 13.10% |
| Rust | 1 | 2,801 | 132 | 4.71% |
| Ruby | 1 | 199 | 148 | 74.37% |
| PHP | 1 | 1,707 | 59 | 3.46% |
| Terraform | 1 | 290 | 0 | 0.00% |

The 5.72% figure is **configuration evidence coverage, not precision, recall or F1**. It is the fraction of discovered configuration inputs for which ConfigReach linked test/runtime evidence. Precision/recall require independently labelled ground truth and are measured separately below.

Exact upstream SHAs, per-repository counts, runtimes, artifact IDs and SHA-256 artifact digests are published in [`validation/results/external-holdout-full.md`](validation/results/external-holdout-full.md) and [`validation/results/external-holdout-full.json`](validation/results/external-holdout-full.json). The successful full run is preserved in [GitHub Actions run 36588655396](https://github.com/sauravsingla/ConfigReach/actions/runs/36588655396).

The earlier 10-project baseline remains published for historical comparison in [`validation/results/real-world.md`](validation/results/real-world.md): **17,777** configuration inputs, **639** inputs with detected evidence and **3.6%** aggregate observed key coverage.

### External precision & recall evaluation

External precision, recall and F1 will be reported only from **independently labelled cases sampled from the frozen external holdout**. Until that review is complete, ConfigReach makes **no external precision/recall/F1 claim** from the 96,845 discovered inputs or the 5.72% configuration-coverage figure.

When external accuracy results are published, this section will report the reviewed sample size, TP, FP, FN, precision, recall, F1, repository/ecosystem coverage, sampling method and annotation protocol so the measurement can be interpreted and reproduced.

### Small hand-labelled accuracy benchmark

A separate small committed ground-truth corpus measures precision, recall and F1 for five core analysis tasks. On the current **37 labelled benchmark decisions**, the deterministic hardening pass produces zero false positives and zero false negatives:

| Task | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Environment-variable discovery | **100.0%** | **100.0%** | **100.0%** | 11 | 0 | 0 |
| Feature flags | **100.0%** | **100.0%** | **100.0%** | 2 | 0 | 0 |
| Configuration declarations | **100.0%** | **100.0%** | **100.0%** | 11 | 0 | 0 |
| Test evidence | **100.0%** | **100.0%** | **100.0%** | 6 | 0 | 0 |
| Branch inference | **100.0%** | **100.0%** | **100.0%** | 7 | 0 | 0 |

**Micro precision: 100.0% · Micro recall: 100.0% · Micro F1: 100.0% · Macro F1: 100.0% on this committed corpus.**

This is deliberately a **corpus-specific measurement, not a claim of universal 100% accuracy**. The benchmark remains intentionally small and transparent and contains difficult positives/negatives for indirect environment names, JavaScript destructuring, unrelated `variation()` calls, project metadata and branch inference. See [`validation/results/accuracy.md`](validation/results/accuracy.md) for exact scoring and [`VALIDATION.md`](VALIDATION.md) for methodology, reproduction steps and claim boundaries.

## Why configuration coverage?

Code coverage can tell you that a line executed. It cannot tell you whether the configuration states that change that line's behavior were exercised.

```python
mode = os.getenv("PAYMENT_MODE", "sandbox")
if mode == "live":
    charge_real_card()
else:
    simulate_charge()
```

A suite can execute that block every time and still never test `PAYMENT_MODE=live`. ConfigReach inventories configuration reads and declarations, maps them to test evidence, tracks known values and branches, measures configuration combinations, and reports the gaps.

## Problems developers actually search for

Different teams describe configuration-coverage gaps in different ways. ConfigReach is designed to answer questions behind searches like these:

- **environment variable test coverage** — Which environment variables and known values are actually exercised by tests? Run `configreach coverage .`.
- **feature flag test coverage** — Are enabled/disabled states and known feature-flag values covered? Run `configreach matrix .`.
- **configuration testing** — Which configuration branches, defaults and expected values have test evidence? Run `configreach scan .`.
- **config coverage** — What percentage of discovered configuration inputs have detected test or runtime evidence? Run `configreach coverage .`.
- **test environment variables** — Where is a key such as `PAYMENT_MODE` read, declared, defaulted and tested? Run `configreach explain PAYMENT_MODE .`.
- **Kubernetes configuration testing** — Which Kubernetes-style environment declarations map to application configuration reads, and which lack test evidence? Run `configreach scan .`. ConfigReach performs static repository analysis; it does not claim to validate live-cluster behavior.

## Quick start

### PyPI CLI

ConfigReach supports CPython **3.8 through 3.14**. Python 3.8 and 3.9 are upstream end-of-life, so maintained Python versions are recommended for security-sensitive environments.

```bash
python -m pip install --upgrade configreach
configreach scan .
configreach coverage .
```

### GitHub Container Registry

The image is public, multi-architecture (`linux/amd64` and `linux/arm64`), and published with SBOM/provenance:

```bash
docker pull ghcr.io/sauravsingla/configreach:latest
docker run --rm -v "$PWD:/workspace" ghcr.io/sauravsingla/configreach:latest scan .
```

### GitHub Action

Use the floating major tag for stable v0 updates:

```yaml
- uses: sauravsingla/ConfigReach@v0
  with:
    path: .
    format: markdown
    fail-under: "60"
    fail-on: error
```

See [`docs/marketplace.md`](docs/marketplace.md) for Action/Marketplace installation details.

### Development from source

```bash
git clone https://github.com/sauravsingla/ConfigReach.git
cd ConfigReach
python -m pip install -e .
```

Useful examples:

```bash
configreach scan examples/polyglot
configreach explain PAYMENT_MODE examples/polyglot
configreach matrix examples/polyglot
configreach scan examples/polyglot --format html --output configreach.html
configreach plan examples/combinations --format markdown
configreach plan examples/combinations --fixture pytest --output configreach_cases.py
configreach workspace . --format json --output configreach-workspaces.json
configreach adapters --format json
configreach reproduce examples/combinations --runs 3
configreach schema --format json
```

## Observable metrics — no opaque AI score

ConfigReach reports evidence-based metrics independently:

- **Key coverage** — discovered configuration inputs with detected test/runtime evidence.
- **Value coverage** — explicitly tested values / explicitly known values.
- **Boolean coverage** — tested `true`/`false` states where a boolean domain is known.
- **Enum coverage** — exercised known discrete values for non-boolean finite domains.
- **Branch-state coverage** — configuration-dependent branch states with explicit test-value evidence.
- **Pairwise key coverage** — interacting keys receiving joint test evidence.
- **Pairwise value-state coverage** — known value combinations observed together in the same detected test scenario.
- **Blast radius** — files and top-level modules reading a configuration key.
- **Workspace coverage** — weighted configuration coverage across independently cached monorepo workspaces.

Unknown domains remain unknown. ConfigReach never asks a model whether something is “probably covered.” See [docs/metrics.md](docs/metrics.md).

## Discovery coverage

### Runtime reads

| Ecosystem | Examples | Current analysis |
|---|---|---|
| Python | `os.getenv`, `os.environ[...]`, `os.environ.get`, `setdefault` | AST-backed |
| Pydantic Settings | `BaseSettings`, aliases, `Literal`, Enum, bool domains, Field validators | AST-backed |
| Python CLI | `argparse`, common Click/Typer option forms | AST-backed/conservative |
| Feature flags | `is_enabled`, `feature_enabled`, LaunchDarkly-style variation calls | AST + deterministic patterns |
| JavaScript / TypeScript | `process.env`, Deno/Bun environment access, function-scoped comparisons | deterministic semantic adapter |
| Zod | `z.enum`, `z.boolean`, `z.literal`, min/max/regex/url/email/nonempty | deterministic validator adapter |
| Go | `os.Getenv`, `os.LookupEnv`, `t.Setenv`, function-scoped comparisons | deterministic semantic adapter |
| Java / Spring | `System.getenv`, `System.getProperty`, `@Value`, `Environment.getProperty`, `@ConfigurationProperties` | deterministic semantic adapter |
| Java Bean Validation | `@Min`, `@Max`, `@Size`, `@Pattern`, null/blank/sign constraints on `@Value` fields | deterministic validator adapter |
| .NET / C# | environment variables, `IConfiguration`, `GetValue`, feature flags | deterministic semantic adapter |
| Rust | `env::var`, `env::var_os` | deterministic pattern adapter |
| Ruby | `ENV[...]`, `ENV.fetch(...)` | deterministic pattern adapter |
| PHP | `getenv(...)`, common `env(...)` | deterministic pattern adapter |
| Shell | `$VAR`, `${VAR}` | deterministic pattern adapter |

### Declarations, schemas and deployment sources

ConfigReach recognizes `.env.example`, `.env.template`, `.env*` templates, JSON, TOML, INI/CFG, Java properties, YAML environment declarations, Dockerfiles/Containerfiles, Docker Compose, Kubernetes-style environment declarations, Helm `values.yaml`, GitHub Actions `${{ vars.* }}` and `${{ secrets.* }}`, Terraform variables, Makefile variables, Pydantic settings, JSON Schema finite domains/validators, Zod schemas and CLI options.

## Commands

```bash
configreach scan [PATH]
configreach coverage [PATH]
configreach explain KEY [PATH]
configreach matrix [PATH]
configreach plan [PATH]
configreach plan [PATH] --strength 3 --max-cases 40
configreach plan [PATH] --fixture pytest|jest|go|shell|junit|xunit
configreach workspace [PATH]
configreach adapters
configreach reproduce [PATH] --runs 3
configreach schema
configreach schema --kind report --check configreach.json
configreach diff origin/main...HEAD [PATH]
configreach pr-comment origin/main...HEAD [PATH]
configreach doctor [PATH]
configreach export [PATH] --format json
configreach export [PATH] --format sarif
configreach export [PATH] --format html
configreach baseline create [PATH]
configreach cache clear [PATH]
configreach init [PATH]
configreach trace --path . -- pytest -q
```

## Deterministic test planning

`configreach plan` converts already-known finite configuration domains into bounded 1-wise, 2-wise or 3-wise suggestions. Existing test scenarios are subtracted first, sensitive-looking keys are excluded, and CPU-safety limits prevent Cartesian-product explosions.

```bash
configreach plan . --strength 2
configreach plan . --format json --output configreach-plan.json
```

The planner does not invent values, execute the application, synthesize assertions or call a model. See [docs/planning.md](docs/planning.md).

## Fixture exporters

Turn the deterministic plan into lightweight scaffolding for your own tests:

```bash
configreach plan . --fixture pytest --output test_configreach_cases.py
configreach plan . --fixture jest --output configreach.cases.ts
configreach plan . --fixture go --output configreach_cases_test.go
configreach plan . --fixture shell --output configreach_cases.sh
configreach plan . --fixture junit --output ConfigReachCases.java
configreach plan . --fixture xunit --output ConfigReachCases.cs
```

Exporters provide configuration cases only; they deliberately do not invent expected business outcomes. See [docs/fixtures.md](docs/fixtures.md).

## Monorepos and workspace-local incremental caching

`configreach workspace` detects Python, Node, Go, Rust, Maven/Gradle and `.csproj` workspace roots. Each workspace receives an independent `.configreach/cache/` boundary, so changing one package does not invalidate unrelated warmed workspace caches. Parent workspaces ignore nested workspace directories to avoid double counting.

```bash
configreach workspace .
configreach workspace . --format markdown
configreach workspace . --format json --output workspaces.json
```

The normal `configreach scan .` remains the combined repository view. See [docs/workspaces.md](docs/workspaces.md).

## Adapter API and optional parser-backed plugins

The base package has no optional external parser dependencies. Python 3.8–3.10 additionally uses the pinned `tomli` TOML backport; Python 3.11+ uses the standard-library `tomllib`. External deterministic adapters can register through the `configreach.adapters` entry-point group. Adapter API v1 includes compatibility version, parser identity, determinism declaration and capability metadata.

```bash
configreach adapters
configreach adapters --format json
```

ConfigReach rejects incompatible or explicitly non-deterministic plugins without crashing the core scanner. A real optional tree-sitter JavaScript adapter example lives under [`examples/plugins/tree_sitter_js`](examples/plugins/tree_sitter_js/); installing it is separate from installing ConfigReach. See [docs/plugin-sdk.md](docs/plugin-sdk.md) and [docs/adapter-capabilities.md](docs/adapter-capabilities.md).

## Reproducibility verification

```bash
configreach reproduce .
configreach reproduce . --runs 5 --format json --output repro.json
```

Repeated scans are uncached and converted to canonical JSON before SHA-256 hashing. Absolute root, timing and cache metadata are excluded because they are execution-environment metadata, not analysis semantics. The repository's reproducibility workflow compares canonical digests produced on **Ubuntu, macOS and Windows** and fails if they differ. See [docs/reproducibility.md](docs/reproducibility.md).

## Schema compatibility

ConfigReach publishes explicit versions for scan reports, workspace reports, deterministic plans, reproducibility results and adapter capability inventories.

```bash
configreach schema
configreach schema --format json
configreach schema --kind report --check configreach.json
```

The validator rejects unsupported future schemas instead of guessing their meaning. Report schemas 3-5 are accepted for structural compatibility checks, while new scan output remains report schema v5. Golden compatibility fixtures live in the test suite. See [docs/schema-compatibility.md](docs/schema-compatibility.md).

## CI gating

```bash
configreach scan . --fail-under 70
configreach scan . --fail-on error
configreach scan . --fail-on uncovered
configreach scan . --fail-on untested-values
configreach scan . --fail-on default-only
configreach scan . --fail-on global-env-overwrite
```

`--fail-under` gates key coverage. `--fail-on` can gate finding aliases, severities or exact `CRxxx` rule IDs.

## Pull-request configuration diff

```bash
configreach diff origin/main...HEAD
configreach pr-comment origin/main...HEAD --output /tmp/configreach-comment.md
```

ConfigReach resolves the local Git merge base, scans the base snapshot and current tree, and reports new/removed keys, changed domains/defaults, newly introduced untested configuration, new values without test evidence, changed-line configuration impact and blast radius. No external service is required.

## Searchable static HTML report

```bash
configreach scan . --format html --output configreach.html
```

The report is a single self-contained HTML file with no CDN/network dependency and includes searchable key/value/branch/combination evidence plus source links.

## Baselines and cache

```bash
configreach baseline create .
configreach scan . --no-cache
configreach cache clear .
```

Baseline keys remain visible but are excluded from CI key-coverage gating. Cache/timing state is excluded from JSON/SARIF result semantics. See [docs/baselines.md](docs/baselines.md).

## Optional lightweight runtime tracing

```bash
configreach trace -- pytest -q
configreach scan .
```

Tracing is explicit opt-in. The Python tracer records key names plus short SHA-256-derived value fingerprints; it does not persist raw runtime values.

## Deterministic findings

| Rule | Meaning | Default severity |
|---|---|---|
| `CR001` | configuration has no detected test/runtime evidence | warning |
| `CR002` | application read without a recognized declaration | warning |
| `CR003` | declaration without a recognized application read | note |
| `CR004` | known values are not all exercised | warning |
| `CR005` | sensitive-looking configuration has a non-empty static default | error |
| `CR006` | likely inconsistent names normalize to the same identifier | warning |
| `CR007` | production-like known value is not exercised | warning |
| `CR008` | explicit tests only exercise defaults | warning |
| `CR009` | a test mutates the global environment in a potentially leaky way | warning |

Every finding retains source provenance.

## GitHub Actions

```yaml
name: Configuration coverage
on: [pull_request]

jobs:
  configreach:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: sauravsingla/ConfigReach@v0
        with:
          path: .
          format: markdown
          fail-under: "60"
          fail-on: error
```

Markdown output can be appended to the job summary, SARIF can be uploaded to Code Scanning, and the repository includes an optional PR-comment workflow.

## Supply-chain and security gates

The repository runs CodeQL, OpenSSF Scorecard, Dependabot, GitHub dependency review when the Dependency Graph is available, mandatory cross-version Python vulnerability/license audits, container vulnerability scanning, action smoke tests, reproducible wheel/sdist builds and cross-OS report reproducibility. GHCR images are anonymously pull-tested, published for amd64/arm64, and include SBOM/provenance from BuildKit. See [`SECURITY.md`](SECURITY.md) and [`CHANGELOG.md`](CHANGELOG.md).

## Benchmark, performance budget and testing

```bash
python benchmarks/bench_scan.py 1000
python benchmarks/perf_budget.py --files 800 --min-files-per-second 150
python -m pip install -e ".[dev]"
pytest
python -m compileall -q src tests
configreach reproduce examples/combinations --runs 3
```

The dedicated performance workflow runs the full semantic engine over a synthetic Python/TypeScript/Go/Java/.NET repository and uses a deliberately conservative throughput floor to catch order-of-magnitude regressions without turning runner noise into flaky CI.

The suite covers language/config discovery, deployment sources, validators, Pydantic/feature flags, branch provenance, combination metrics, real Git PR comparison, baselines, cache behavior, workspace-local invalidation, planners, fixture exporters, plugin compatibility, schema compatibility, reproducibility, performance gating, HTML/SARIF/JSON/Markdown reporters and CLI policies.

## Design principles

- CPU-only; standard-library runtime on Python 3.11+ and only the pinned `tomli` backport on Python 3.8–3.10.
- No network, telemetry, model inference or paid API in the core.
- Static scanning never executes target application code.
- Runtime tracing is explicit opt-in.
- Unknown semantics stay unknown rather than being guessed.
- Machine output is designed for deterministic CI use.

See [docs/architecture.md](docs/architecture.md), [docs/threat-model.md](docs/threat-model.md), [docs/schema-compatibility.md](docs/schema-compatibility.md), [docs/roadmap.md](docs/roadmap.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
