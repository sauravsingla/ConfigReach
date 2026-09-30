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

For immutable pinning, use a full release tag such as `sauravsingla/ConfigReach@v0.9.2`.

## What the listing should highlight

- Deterministic, CPU-only analysis
- Zero runtime dependencies
- No LLM, API key, telemetry or hosted service required
- Works directly inside pull-request CI
- Supports environment variables, feature flags, configuration declarations, CLI options and multiple ecosystems
- Markdown, JSON, SARIF and HTML output
- Reproducible public validation evidence
- Archived software record on Zenodo

## Release copy

**ConfigReach v0.9.2 — configuration coverage for CI**

ConfigReach complements code coverage by checking whether the environment variables, feature flags and configuration states that change application behaviour have test/runtime evidence.

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
- Zenodo: https://zenodo.org/records/23038726

## Marketplace readiness

The repository contains a root `action.yml` with a Marketplace-oriented name and description, documented inputs, composite implementation and branding. The current release line also maintains a floating `v0` tag for stable pre-1.0 usage.

The remaining Marketplace publication step is performed from the GitHub release/Marketplace interface. No additional runtime code change is required for the listing itself.
