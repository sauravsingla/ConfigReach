# ConfigReach GitHub Action

ConfigReach is a deterministic configuration-coverage action for GitHub repositories. It measures which environment variables, feature flags, configuration values and configuration-dependent branches have test/runtime evidence.

## Marketplace description

**Codecov for configuration space.** Find environment variables, feature flags and configuration states that your tests do not exercise.

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

For immutable pinning, use a full release tag such as `sauravsingla/ConfigReach@v0.9.2` after that release is published.

## Marketplace readiness

The repository contains a root `action.yml` with a name, concise description, inputs, composite implementation and branding. Release automation also maintains a floating `v0` tag for the current pre-1.0 action line.

Publishing the listing itself is a GitHub Marketplace UI approval attached to a release. It does not change the action runtime or package artifacts.
