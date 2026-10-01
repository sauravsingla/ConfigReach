---
title: ConfigReach — Configuration Coverage
emoji: 🎯
colorFrom: blue
colorTo: green
sdk: static
app_file: index.html
fullWidth: true
header: mini
pinned: true
license: mit
short_description: CPU-only configuration coverage with a curated 50K benchmark.
datasets:
  - sauravsingla08/configreach-validation
tags:
  - developer-tools
  - software-testing
  - testing
  - devops
  - ci-cd
  - configuration
  - configuration-testing
  - configuration-coverage
  - static-analysis
  - github-actions
  - benchmark
  - reproducibility
  - cpu
  - environment-variables
  - feature-flags
---

# ConfigReach — Configuration Coverage

**Codecov for configuration space.**

ConfigReach is a deterministic, CPU-only configuration coverage analyzer for software repositories. It shows which environment variables, feature flags, CLI options, configuration values, branches, and configuration combinations your tests actually exercise.

**Project hub:** [ConfigReach — Configuration Coverage collection](https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage)

## Curated 50K benchmark

ConfigReach is evaluated on a committed **50,000-case controlled curated benchmark** with deterministic ground-truth labels. The corpus is balanced with **25,000 positive** and **25,000 negative** scenarios across supported programming languages and configuration formats.

The benchmark is scored through the production **`configreach.engine.scan`** entry point.

| Metric | Result |
|---|---:|
| Scenarios | **50,000** |
| True positives | **25,000** |
| False positives | **0** |
| True negatives | **25,000** |
| False negatives | **0** |
| Precision | **100.0000%** |
| Recall | **100.0000%** |
| F1 | **100.0000%** |
| Accuracy | **100.0000%** |

The full 50K corpus and row-level evidence are published in the linked Hugging Face Dataset and committed in GitHub.

> **Scope:** this is the measured result on the committed controlled curated benchmark. It is not a claim of universal real-world accuracy. The benchmark is programmatically generated from explicit version-controlled scenario families with deterministic labels; it is not described as independently human-labelled.

## Explore the benchmark

- [Hugging Face 50K dataset](https://huggingface.co/datasets/sauravsingla08/configreach-validation)
- [GitHub benchmark source](https://github.com/sauravsingla/ConfigReach/tree/main/validation/curated_50k)
- [Measured result](https://github.com/sauravsingla/ConfigReach/blob/main/validation/results/curated_50k.md)
- [Machine-readable result](https://github.com/sauravsingla/ConfigReach/blob/main/validation/results/curated_50k.json)
- [Row-level predictions](https://github.com/sauravsingla/ConfigReach/blob/main/validation/results/curated_50k_predictions.csv)

## Try ConfigReach

Released package:

```bash
python -m pip install --upgrade configreach
configreach scan .
configreach coverage .
```

To reproduce the exact currently committed benchmark source before the next package release, install from `main`:

```bash
python -m pip install --upgrade "git+https://github.com/sauravsingla/ConfigReach.git@main"
```

ConfigReach requires no GPU, LLM, API key, hosted service, telemetry, or paid dependency. Static analysis does not execute the target repository.

## Current repository metadata

The current repository package metadata is **ConfigReach v0.9.4** and supports **Python 3.10–3.14**. The 50K evidence above is tied to the committed `main` implementation and its production scanner entry point.

## Project links

- [ConfigReach Hugging Face collection](https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage)
- [Hugging Face curated 50K dataset](https://huggingface.co/datasets/sauravsingla08/configreach-validation)
- [GitHub repository](https://github.com/sauravsingla/ConfigReach)
- [PyPI package](https://pypi.org/project/configreach/)
- [50K benchmark methodology](https://github.com/sauravsingla/ConfigReach/blob/main/validation/curated_50k/README.md)
- [50K benchmark manifest](https://github.com/sauravsingla/ConfigReach/blob/main/validation/curated_50k/manifest.json)

This Space is published automatically from GitHub using Hugging Face Trusted Publishers and GitHub Actions OIDC. No long-lived Hugging Face token is stored in GitHub.
