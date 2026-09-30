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
short_description: CPU-only config coverage for env vars, feature flags & CI.
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

## Try ConfigReach on your repository

Run it locally in under a minute:

```bash
python -m pip install --upgrade configreach
configreach scan .
configreach coverage .
```

Or add it to GitHub Actions:

```yaml
- uses: sauravsingla/ConfigReach@v0
  with:
    path: .
    format: markdown
```

The Hugging Face Space is the public project/demo page. Repository scanning runs locally, in CI, or from the public container; ConfigReach does not require a GPU, LLM, API key, hosted service, telemetry, or paid dependency.

## Current source version

**ConfigReach v0.9.3** is the current repository version.

```bash
pip install --upgrade configreach
```

## Published external validation

The current frozen external holdout scans **11 pinned public open-source repositories across 9 ecosystems**. The repositories were selected before ConfigReach results were examined and are disjoint from the earlier 10-project baseline.

**Validation provenance:** this frozen holdout and the accompanying hand-labelled accuracy corpus were produced with **ConfigReach v0.9.2**. ConfigReach v0.9.3 is the current source release; historical validation evidence is intentionally not relabelled when the software version advances.

- **11 / 11** repository jobs completed successfully
- **96,845** configuration inputs discovered
- **5,539** inputs with detected test/runtime evidence
- **5.72%** aggregate observed configuration coverage
- **34,933.6s (~9.70 cumulative scanner-hours)** across independently executed repository jobs
- **0** repository overlap with the earlier validation baseline

The 5.72% figure is **configuration evidence coverage, not precision, recall or F1**. It is the fraction of discovered configuration inputs for which ConfigReach linked test/runtime evidence.

## Accuracy evidence

### External precision & recall

External precision, recall and F1 will be published only after independently labelled cases from the frozen external holdout are reviewed. Until then, ConfigReach makes **no external precision/recall/F1 claim** from the 96,845-input holdout.

### Small hand-labelled benchmark

A separate committed benchmark covers five core analysis tasks and currently reports:

- **100.0% micro precision**
- **100.0% micro recall**
- **100.0% micro F1**
- **100.0% macro F1**
- **37 true positives, 0 false positives, 0 false negatives**

This is deliberately a **small corpus-specific measurement, not a claim of universal 100% accuracy**.

## Project links

- [ConfigReach Hugging Face collection](https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage)
- [Hugging Face validation dataset](https://huggingface.co/datasets/sauravsingla08/configreach-validation)
- [GitHub repository](https://github.com/sauravsingla/ConfigReach)
- [PyPI package](https://pypi.org/project/configreach/)
- [Validation methodology](https://github.com/sauravsingla/ConfigReach/blob/main/VALIDATION.md)
- [Full frozen external holdout](https://github.com/sauravsingla/ConfigReach/blob/main/validation/results/external-holdout-full.md)
- [Machine-readable external holdout](https://github.com/sauravsingla/ConfigReach/blob/main/validation/results/external-holdout-full.json)
- [Measured hand-labelled accuracy](https://github.com/sauravsingla/ConfigReach/blob/main/validation/results/accuracy.md)
- [Historical 10-project baseline](https://github.com/sauravsingla/ConfigReach/blob/main/validation/results/real-world.md)
- [GitHub Pages site](https://sauravsingla.github.io/ConfigReach/)

This Space is published automatically from GitHub using Hugging Face Trusted Publishers and GitHub Actions OIDC. No long-lived Hugging Face token is stored in GitHub.
