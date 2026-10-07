# ConfigReach

> **High code coverage does not guarantee high configuration coverage. ConfigReach measures the gap.**

**ConfigReach is “Codecov for configuration space.”** It finds environment variables, feature flags, CLI options and configuration values in a repository, then shows which states your tests actually exercise.

[![PyPI](https://img.shields.io/pypi/v/configreach.svg)](https://pypi.org/project/configreach/)
[![CI](https://github.com/sauravsingla/ConfigReach/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/ConfigReach/actions/workflows/ci.yml)
[![CodeQL](https://github.com/sauravsingla/ConfigReach/actions/workflows/codeql.yml/badge.svg)](https://github.com/sauravsingla/ConfigReach/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## The problem

A test suite can execute a configuration-dependent code path and still never exercise the configuration state that changes its behavior.

```python
mode = os.getenv("PAYMENT_MODE", "sandbox")
if mode == "live":
    charge_real_card()
else:
    simulate_charge()
```

Traditional code coverage can report this block as covered even when `PAYMENT_MODE=live` was never tested. ConfigReach turns that hidden configuration surface into something measurable.

## Try it in 30 seconds

```bash
python -m pip install --upgrade configreach
configreach scan .
configreach coverage .
```

ConfigReach is **offline, deterministic and CPU-only**. It needs no GPU, LLM, API key, hosted service or telemetry, and static analysis does not execute the target repository.

![ConfigReach terminal example](docs/demo.svg)

### What you get

- configuration-key and value coverage;
- boolean, enum and branch-state coverage;
- pairwise configuration-state coverage;
- `explain` output for individual keys;
- CI-friendly JSON, SARIF, HTML and Markdown output;
- GitHub Action, container and local CLI workflows.

**Best way to help:** run ConfigReach on a real repository and open an issue with a configuration pattern it misses or misclassifies.

## Questions ConfigReach answers

ConfigReach is designed to answer practical configuration-testing questions such as:

- **environment variable test coverage** — Which environment variables and known values are actually exercised by tests? Run `configreach coverage .`.
- **feature flag test coverage** — Are enabled/disabled states and known feature-flag values covered? Run `configreach matrix .`.
- **configuration testing** — Which configuration branches, defaults and expected values have test evidence? Run `configreach scan .`.
- **config coverage** — What percentage of discovered configuration inputs have detected test or runtime evidence? Run `configreach coverage .`.
- **test environment variables** — Where is a key such as `PAYMENT_MODE` read, declared, defaulted and tested? Run `configreach explain PAYMENT_MODE .`.
- **Kubernetes configuration testing** — Which Kubernetes-style environment declarations map to application configuration reads, and which lack test evidence? Run `configreach scan .`. ConfigReach performs static repository analysis; it does not claim to validate live-cluster behavior.

## Installation and CI options

### PyPI CLI

ConfigReach supports CPython **3.10 through 3.14**. The 50K-benchmarked enterprise-hardening changes are released in **v0.9.5**.

```bash
python -m pip install --upgrade configreach
configreach scan .
configreach coverage .
```

> **Interpreting 0% coverage:** if ConfigReach discovers configuration inputs but finds no recognized test files or runtime evidence, 0% coverage is an expected result, not a scan failure. Run from the repository root and include the project's tests for a meaningful coverage assessment.

### GitHub Container Registry

The image is public, multi-architecture (`linux/amd64` and `linux/arm64`), runs as a dedicated **non-root** user, and is published with SBOM/provenance:

```bash
docker pull ghcr.io/sauravsingla/configreach:latest
docker run --rm -v "$PWD:/workspace:ro" ghcr.io/sauravsingla/configreach:latest scan . --no-cache
```

For high-assurance environments, pin an approved version/digest and run with egress disabled and a read-only root filesystem; see [`docs/enterprise-security.md`](docs/enterprise-security.md).

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

For regulated internal workflows, pin the exact approved release or commit according to your supply-chain policy. See [`docs/marketplace.md`](docs/marketplace.md) for Action/Marketplace installation details.

### Development from source

```bash
git clone https://github.com/sauravsingla/ConfigReach.git
cd ConfigReach
python -m pip install -e .
```

## Maintainer validation benchmark

ConfigReach is evaluated on a committed **50,000-case curated benchmark** with deterministic ground-truth labels, split evenly into **25,000 positive** and **25,000 negative** scenarios. The benchmark is assembled from explicit, version-controlled scenario families and scored through the production `configreach.engine.scan()` entry point.

| Metric | Result |
|---|---:|
| Scenarios | **50,000** |
| TP | **25,000** |
| FP | **0** |
| TN | **25,000** |
| FN | **0** |
| Precision | **100%** |
| Recall | **100%** |
| F1 | **100%** |
| Accuracy | **100%** |

The benchmark data, aggregate results and row-level predictions are available in the [validation folder](validation/). The same 50K benchmark is also published as a [Hugging Face Dataset](https://huggingface.co/datasets/sauravsingla08/configreach-validation).

> Scope: this is the measured result on the committed controlled curated benchmark; it is not independently human-labelled evidence and is not a claim of universal real-world accuracy.


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

### What each command does

| Command | Purpose | Example |
|---|---|---|
| `scan` | Scan a repository, discover configuration inputs and report coverage/findings. | `configreach scan .` |
| `coverage` | Show configuration coverage for discovered inputs. | `configreach coverage .` |
| `explain` | Show where a specific configuration key is declared, read and tested. | `configreach explain PAYMENT_MODE .` |
| `matrix` | Show known values/states and which ones have test evidence. | `configreach matrix .` |
| `plan` | Generate bounded deterministic configuration test suggestions from known finite domains. | `configreach plan . --strength 2` |
| `plan --fixture` | Export suggested configuration cases as test scaffolding. | `configreach plan . --fixture pytest --output configreach_cases.py` |
| `workspace` | Analyze monorepo workspaces independently and report combined coverage. | `configreach workspace .` |
| `adapters` | List installed configuration-analysis adapters and capabilities. | `configreach adapters --format json` |
| `reproduce` | Repeat uncached scans and verify deterministic report digests. | `configreach reproduce . --runs 3` |
| `schema` | Inspect or validate ConfigReach machine-output schema versions. | `configreach schema --format json` |
| `diff` | Compare configuration coverage between Git revisions. | `configreach diff origin/main...HEAD .` |
| `pr-comment` | Produce a pull-request-friendly configuration-change summary. | `configreach pr-comment origin/main...HEAD .` |
| `doctor` | Check the target repository and local ConfigReach setup before analysis. | `configreach doctor .` |
| `export` | Produce machine-readable or shareable JSON, SARIF or HTML reports. | `configreach export . --format html --output configreach.html` |
| `baseline create` | Record an approved baseline so existing keys can be excluded from CI key-coverage gating. | `configreach baseline create .` |
| `cache clear` | Clear ConfigReach's local analysis cache. | `configreach cache clear .` |
| `init` | Initialize ConfigReach configuration for a repository. | `configreach init .` |
| `trace` | Explicitly run an operator-supplied test command and collect lightweight runtime configuration evidence. | `configreach trace --path . -- pytest -q` |

### Recommended first evaluation

Run these from the **repository root**, ideally in a project that contains both application code and tests:

```bash
configreach doctor .
configreach scan .
configreach coverage .
configreach matrix .
configreach plan . --strength 2
configreach export . --format html --output configreach.html
```

If the project has a trusted pytest suite and runtime evidence is useful, tracing is available as an explicit opt-in:

```bash
configreach trace --path . -- pytest -q
configreach scan .
```

`trace` executes the command supplied by the operator; use it only for code and tests that the environment already trusts to execute.

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

The base package has no optional external parser dependencies. Python 3.10 uses the pinned `tomli` TOML backport; Python 3.11+ uses the standard-library `tomllib`. External deterministic adapters can register through the `configreach.adapters` entry-point group. Adapter API v1 includes compatibility version, parser identity, determinism declaration and capability metadata.

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
configreach trace --path . -- pytest -q
configreach scan .
```

Tracing is explicit opt-in and executes the command supplied by the operator. Use it only for code your environment is already willing to execute. The Python tracer records key names plus short SHA-256-derived value fingerprints; it does not intentionally persist raw runtime values.

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

For high-assurance or regulated workflows, pin both third-party Actions and ConfigReach itself to reviewed immutable commit SHAs:

```yaml
name: Configuration coverage
on: [pull_request]

jobs:
  configreach:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: sauravsingla/ConfigReach@860618b95835fed8aba6bd0b8f8048e9bfdbeddd # v0.9.5
        with:
          path: .
          format: markdown
          fail-under: "60"
          fail-on: error
```

For convenience, `@v0` remains the stable released Action line and advances only through the verified release workflow. Regulated environments should pin the exact reviewed release commit shown above, or another internally approved immutable revision. Markdown output can be appended to the job summary, SARIF can be uploaded to Code Scanning, and the repository includes an optional PR-comment workflow.

## Supply-chain and security gates

The repository runs CodeQL, **Gitleaks full-history secret scanning**, OpenSSF Scorecard, Dependabot, GitHub dependency review when the Dependency Graph is available, mandatory cross-version Python vulnerability/license audits, fail-closed HIGH/CRITICAL container vulnerability scanning, action smoke tests, reproducible wheel/sdist builds and cross-OS report reproducibility. External GitHub Actions used by project workflows are required to be pinned to immutable commit SHAs. Validation jobs are read-only reproducibility gates rather than automated writers to `main`. GHCR images run non-root, are anonymously pull-tested, are published for amd64/arm64, and include SBOM/provenance from BuildKit.

For regulated-enterprise intake, threat boundaries, restrictive offline/container operation, internal rebuilding and approval steps, see [`docs/enterprise-security.md`](docs/enterprise-security.md). See also [`SECURITY.md`](SECURITY.md) and [`CHANGELOG.md`](CHANGELOG.md).

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

The suite covers language/config discovery, deployment sources, validators, Pydantic/feature flags, branch provenance, combination metrics, real Git PR comparison, baselines, cache behavior, workspace-local invalidation, planners, fixture exporters, plugin compatibility, schema compatibility, reproducibility, performance gating, HTML/SARIF/JSON/Markdown reporters, CLI policies and untrusted-repository security boundaries.

## Design principles

- CPU-only; standard-library runtime on Python 3.11+ and only the pinned `tomli` backport on Python 3.10.
- No network, telemetry, model inference or paid API in the core.
- Static scanning never executes target application code.
- Repository-controlled file symlinks are ignored by the production scanner.
- Runtime tracing is explicit opt-in and executes only the operator-supplied command.
- Unknown semantics stay unknown rather than being guessed.
- Machine output is designed for deterministic CI use.

See [docs/architecture.md](docs/architecture.md), [docs/threat-model.md](docs/threat-model.md), [docs/enterprise-security.md](docs/enterprise-security.md), [docs/schema-compatibility.md](docs/schema-compatibility.md), [docs/roadmap.md](docs/roadmap.md) and [CONTRIBUTING.md](CONTRIBUTING.md).