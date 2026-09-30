# ConfigReach launch kit

Use this page as the source of truth for external launch copy. Keep claims aligned with the public validation evidence in the repository.

## Primary links

- GitHub: https://github.com/sauravsingla/ConfigReach
- Hugging Face Collection: https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage
- Hugging Face Space: https://huggingface.co/spaces/sauravsingla08/ConfigReach
- Validation Dataset: https://huggingface.co/datasets/sauravsingla08/configreach-validation
- PyPI: https://pypi.org/project/configreach/

## One-line positioning

**Codecov for configuration space: find environment variables, feature flags and configuration states your tests do not exercise.**

## Short technical description

ConfigReach is a deterministic, CPU-only configuration coverage analyzer. It discovers environment variables, feature flags, CLI options and configuration declarations, maps them to test/runtime evidence, and reports coverage gaps without requiring an LLM, GPU, API key or hosted service.

## Public validation snapshot

- 11 pinned public repositories
- 9 ecosystems
- 96,845 configuration inputs discovered
- 5,539 inputs with detected test/runtime evidence
- 5.72% aggregate observed configuration coverage on the frozen external holdout
- 34,933.6 seconds of cumulative scanner runtime across independently executed repository jobs
- Small committed hand-labelled benchmark: 37 TP / 0 FP / 0 FN across five core tasks

The 5.72% figure is configuration evidence coverage, not precision/recall/F1. The 100% precision/recall/F1 result applies only to the small committed hand-labelled corpus and is not a universal accuracy claim.

## Show HN

### Title

**Show HN: ConfigReach – Codecov for configuration space**

### Post

A test suite can have high code coverage while never exercising the configuration states that change how the code behaves.

For example, a line reading `PAYMENT_MODE` may execute on every test run while `PAYMENT_MODE=live` is never tested.

I built ConfigReach to measure that gap. It statically discovers environment variables, feature flags, CLI options and configuration declarations, then maps them to test/runtime evidence. It is deterministic, CPU-only, offline and requires no LLM, GPU, API key or hosted service.

The current frozen external holdout scans 11 pinned open-source repositories across 9 ecosystems and publishes the full evidence and provenance.

GitHub: https://github.com/sauravsingla/ConfigReach

Hugging Face project hub: https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage

Feedback on the metric design, false-positive boundaries and CI ergonomics would be especially useful.

## LinkedIn

High code coverage does not necessarily mean your tests exercised the configuration states that change application behaviour.

I have been building **ConfigReach**, an open-source configuration coverage analyzer for software repositories.

It discovers environment variables, feature flags, CLI options and configuration declarations, then maps them to test/runtime evidence — deterministically, on CPU, with no LLM, GPU, API key or hosted service required.

The current frozen external validation covers **11 pinned repositories across 9 ecosystems**, with full machine-readable evidence published alongside the project.

If you work on testing, DevOps, CI/CD, platform engineering or software reliability, I would value technical feedback on the approach.

Project collection: https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage

GitHub: https://github.com/sauravsingla/ConfigReach

#SoftwareTesting #DevOps #GitHubActions #OpenSource #StaticAnalysis #CICD

## Product Hunt

### Tagline

**Configuration coverage for env vars, feature flags and CI**

### Description

ConfigReach complements code coverage by showing which runtime configuration inputs, values and states your tests actually exercise. It is deterministic, CPU-only and works without an LLM, GPU, API key or hosted service.

### First comment

I built ConfigReach around a simple observation: executing a line of code does not prove that the configuration states controlling that line were tested.

The project publishes reproducible validation evidence, a Hugging Face dataset, a live project Space, PyPI package and GitHub Action integration. I would especially welcome feedback from teams using environment variables, feature flags and configuration-heavy CI pipelines.

## Reddit / developer communities

### Suggested title

**I built an open-source tool to measure configuration coverage, not just code coverage**

### Body

A recurring testing gap is that a line can be covered while the environment variables or feature-flag states controlling its behaviour remain untested.

ConfigReach tries to make that gap measurable. It performs deterministic static analysis of repository configuration inputs and links them to test/runtime evidence. It does not execute the target application and does not use an LLM.

The repository includes reproducible validation evidence and a frozen external holdout across 11 public repositories / 9 ecosystems.

GitHub: https://github.com/sauravsingla/ConfigReach

Validation collection: https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage

I would be interested in edge cases where the configuration model breaks down, especially in large monorepos or feature-flag-heavy systems.

Before posting, check the self-promotion rules of the target community.

## DEV / Hashnode article

### Suggested title

**Your tests have high code coverage — but did they test your configuration?**

### Suggested outline

1. Why line coverage misses configuration states
2. A minimal `PAYMENT_MODE=live` example
3. Environment variables, feature flags and CLI/config declarations
4. What configuration coverage should and should not claim
5. Running `configreach coverage .`
6. Adding ConfigReach to a pull-request workflow
7. Reproducible validation and limitations
8. Where ConfigReach can improve next

## GitHub Marketplace

Use the finalized listing copy in [`docs/marketplace.md`](marketplace.md).

Recommended installation snippet:

```yaml
- uses: sauravsingla/ConfigReach@v0
  with:
    path: .
    format: markdown
    fail-on: error
```

## Launch rule

Lead with the engineering problem and reproducible evidence. Avoid asking for stars as the primary call to action. Ask for technical feedback, reproductions, integrations and real repository examples; stars can follow naturally from useful adoption.
