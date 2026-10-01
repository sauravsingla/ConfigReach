---
license: mit
pretty_name: ConfigReach Curated 50K Benchmark
language:
  - en
size_categories:
  - 10K<n<100K
tags:
  - datasets
  - tabular
  - benchmark
  - software-engineering
  - developer-tools
  - software-testing
  - testing
  - devops
  - ci-cd
  - configuration
  - configuration-testing
  - configuration-coverage
  - static-analysis
  - reproducibility
  - environment-variables
  - feature-flags
configs:
  - config_name: default
    data_files:
      - split: validation
        path: data/configreach_50k_scenarios.jsonl
---

# ConfigReach Curated 50K Benchmark

The **ConfigReach Curated 50K Benchmark** is the committed controlled benchmark used to evaluate ConfigReach configuration-input detection across supported programming languages and configuration formats.

It contains **{{SCENARIOS}} scenarios** with deterministic ground-truth labels: **{{POSITIVE}} positive** and **{{NEGATIVE}} negative** cases across **{{GROUPS}} language/configuration groups**. The benchmark is scored through the production `{{SCANNER_ENTRY_POINT}}` entry point.

**Project hub:** [ConfigReach — Configuration Coverage collection](https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage)

## Measured result

| Metric | Result |
|---|---:|
| Scenarios | **{{SCENARIOS}}** |
| True positives | **{{TP}}** |
| False positives | **{{FP}}** |
| True negatives | **{{TN}}** |
| False negatives | **{{FN}}** |
| Precision | **{{PRECISION}}** |
| Recall | **{{RECALL}}** |
| F1 | **{{F1}}** |
| Accuracy | **{{ACCURACY}}** |

- Repository package metadata: **v{{SOURCE_VERSION}}**
- Semantic engine: **{{SEMANTIC_ENGINE}}**
- Dataset SHA-256: `{{DATA_SHA256}}`

> **Scope:** this is the measured result on the committed controlled curated benchmark. It is not a claim of universal real-world accuracy.

## What is in the dataset?

Each row is one independent detection scenario with these fields:

- `scenario_id` — stable benchmark case identifier
- `group` — programming language or configuration-format family
- `variant` — scenario pattern within the group
- `expected_detect` — deterministic ground-truth detection label
- `expected_key` — expected configuration key when detection is positive
- `suggested_filename` — filename/extension used when materializing the scenario
- `snippet` — source/configuration snippet presented to the scanner

The benchmark includes true configuration accesses/declarations as well as adversarial negatives such as comments, inert strings, custom look-alike APIs, dynamically computed names, quoted shell literals, and structured-configuration value-only cases.

The corpus is generated programmatically from explicit, version-controlled scenario families in `validation/curated_50k/generate_dataset.py`. The labels are deterministic; this dataset is **not described as independently human-labelled**.

## Reproducibility evidence

This Hugging Face repository is generated from evidence committed in the ConfigReach GitHub repository. In addition to the 50K JSONL corpus, the published snapshot includes:

- `metadata/manifest.json` — corpus counts, per-group counts, byte size and SHA-256
- `metadata/results.json` — aggregate, per-group and per-variant benchmark results
- `metadata/summary.json` — compact publication summary and scanner provenance
- `evidence/configreach_50k_predictions.csv` — row-level predictions used to derive the aggregate metrics

## Load with 🤗 Datasets

```python
from datasets import load_dataset

ds = load_dataset("sauravsingla08/configreach-validation", split="validation")
print(ds)
print(ds[0])
```

A simple analysis example:

```python
from datasets import load_dataset

rows = load_dataset("sauravsingla08/configreach-validation", split="validation")
positives = rows.filter(lambda row: row["expected_detect"])
negatives = rows.filter(lambda row: not row["expected_detect"])
print(len(rows), len(positives), len(negatives))
```

## Suitable uses

This benchmark is intended for:

- reproducible regression testing of configuration-detection tooling;
- precision/recall experiments on a controlled labelled corpus;
- cross-language and cross-format static-analysis research;
- evaluation of false-positive suppression for comments, strings and look-alike APIs;
- teaching and examples for environment-variable, feature-flag and configuration analysis.

## Limitations

The benchmark is controlled and programmatically generated from explicit scenario families. It is useful for deterministic regression evidence, but it should not be treated as a representative sample of all real-world software or as evidence of universal ConfigReach accuracy.

## Project links

- Hugging Face Collection: https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage
- Hugging Face Space: https://huggingface.co/spaces/sauravsingla08/ConfigReach
- GitHub: https://github.com/sauravsingla/ConfigReach
- 50K benchmark source: https://github.com/sauravsingla/ConfigReach/tree/main/validation/curated_50k
- Measured result: https://github.com/sauravsingla/ConfigReach/blob/main/validation/results/curated_50k.md
- PyPI: https://pypi.org/project/configreach/
