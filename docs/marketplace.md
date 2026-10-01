# ConfigReach GitHub Action

ConfigReach is a deterministic configuration-coverage action for GitHub repositories. It measures which environment variables, feature flags, configuration values and configuration-dependent branches have test/runtime evidence.

## Marketplace listing copy

### Name

**ConfigReach Configuration Coverage**

### Short description

**Find untested env vars, feature flags and configuration states in CI.**

### Longer description

ConfigReach adds configuration coverage to CI. It discovers runtime configuration inputs such as environment variables, feature flags, CLI options and configuration declarations, maps them to test/runtime evidence, and reports coverage gaps without an LLM, GPU, API key or hosted service.

Use it to complement code coverage with evidence about whether the configuration states that change application behaviour are actually exercised.

### Suggested categories

- Testing
- Continuous integration
- Code quality
- Developer tools

### Search phrases

- configuration coverage
- environment variable test coverage
- feature flag test coverage
- configuration testing
- CI configuration validation
- static analysis
- GitHub Actions testing

## Recommended usage

```yaml
name: Configuration coverage

on:
  pull_request:

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

For immutable release pinning, use `sauravsingla/ConfigReach@v0.9.5`. High-assurance organizations may instead pin the exact approved commit SHA according to their supply-chain policy.

## What the listing should highlight

- Deterministic, CPU-only analysis
- Python 3.10–3.14 compatibility
- Standard-library runtime on Python 3.11+; only the pinned `tomli` backport on Python 3.10
- No LLM, API key, telemetry or hosted service required
- Works directly inside pull-request CI
- Supports environment variables, feature flags, configuration declarations, CLI options and multiple ecosystems
- Markdown, JSON, SARIF and HTML output
- Committed 50,000-case curated benchmark with deterministic labels and production-engine scoring
- Enterprise intake guidance, immutable project workflow pins, full-history secret scanning and non-root container release
- Reproducible public validation evidence
- Archived software record on Zenodo

## Release copy

**ConfigReach v0.9.5 — configuration coverage for CI**

ConfigReach complements code coverage by checking whether the environment variables, feature flags and configuration states that change application behaviour have test/runtime evidence. v0.9.5 includes the curated 50K benchmarked implementation and enterprise software-intake hardening.

Quick start:

```yaml
- uses: sauravsingla/ConfigReach@v0
  with:
    path: .
    format: markdown
    fail-on: error
```

Project hub:

- GitHub: https://github.com/sauravsingla/ConfigReach
- Hugging Face Collection: https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage
- Hugging Face Space: https://huggingface.co/spaces/sauravsingla08/ConfigReach
- Validation Dataset: https://huggingface.co/datasets/sauravsingla08/configreach-validation
- PyPI: https://pypi.org/project/configreach/
- Enterprise Security: https://github.com/sauravsingla/ConfigReach/blob/main/docs/enterprise-security.md
- Zenodo: https://zenodo.org/records/23038726

## Marketplace readiness

The repository contains a root `action.yml` with a Marketplace-oriented name and description, documented inputs, composite implementation and branding. The current release line also maintains a floating `v0` tag for stable pre-1.0 usage.

ConfigReach v0.9.5 is the current GitHub Marketplace release line. The repository metadata, release line and installation documentation are synchronized by the verified release workflow.
