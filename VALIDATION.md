# ConfigReach validation and measured accuracy

ConfigReach publishes deliberately separate forms of evidence so repository-level configuration coverage is not confused with accuracy.

1. **Frozen external holdout:** static scans of pinned public repositories selected before results were examined. This measures discovered configuration inputs, linked test/runtime evidence, configuration coverage and runtime.
2. **External precision/recall evaluation:** reserved for independently labelled cases sampled from the frozen external holdout. No external precision/recall/F1 claim is made until that review is complete.
3. **Small hand-labelled accuracy benchmark:** a committed ground-truth corpus scored for precision, recall and F1 across environment-variable discovery, feature flags, configuration declarations, test evidence and branch inference.

These are different measurements. Configuration coverage observed in an external repository is not labelled ground truth.

## Frozen external holdout

The current frozen holdout contains **11 public repositories across 9 ecosystems**. Selection was frozen before ConfigReach results were examined, every target is pinned to an immutable full commit SHA, and the corpus has zero repository overlap with the earlier 10-project baseline.

Published aggregate results:

- **11 / 11** repository jobs completed successfully
- **96,845** configuration inputs discovered
- **5,539** inputs with detected test/runtime evidence
- **5.72%** aggregate observed configuration coverage
- **34,933.6 seconds (~9.70 cumulative scanner-hours)** summed across independently executed repository jobs
- **0** repository overlap with the historical baseline

The repositories are:

- `apache/airflow` — Python
- `PrefectHQ/prefect` — Python
- `vercel/next.js` — JavaScript/TypeScript
- `vitejs/vite` — JavaScript/TypeScript
- `argoproj/argo-cd` — Go/Kubernetes
- `spring-projects/spring-boot` — Java/Spring
- `dotnet/aspnetcore` — .NET/C#
- `astral-sh/uv` — Rust
- `rails/rails` — Ruby
- `laravel/framework` — PHP
- `terraform-aws-modules/terraform-aws-vpc` — Terraform

The exact immutable SHAs are committed in [`validation/external_holdout_projects.json`](validation/external_holdout_projects.json). Full per-repository results, runtimes and artifact provenance are published in [`validation/results/external-holdout-full.md`](validation/results/external-holdout-full.md) and [`validation/results/external-holdout-full.json`](validation/results/external-holdout-full.json).

Target repositories are statically scanned. ConfigReach does not execute target application code and does not install target dependencies during this validation.

### Claim boundary

The **5.72%** figure is configuration evidence coverage: the fraction of discovered configuration inputs for which ConfigReach linked test/runtime evidence. It is **not** scanner accuracy, precision, recall or F1.

## External precision & recall evaluation

External precision, recall and F1 will be reported only from independently labelled cases sampled from the frozen holdout. Until that review is complete, ConfigReach makes **no external precision/recall/F1 claim** from the 96,845 discovered inputs or the 5.72% configuration-coverage figure.

When published, the external accuracy report should include at minimum:

- reviewed sample size,
- true positives, false positives and false negatives,
- precision, recall and F1,
- repositories and ecosystems represented,
- sampling procedure,
- annotation protocol,
- reviewer/consensus procedure where applicable,
- frozen source revisions used for evaluation.

## Small hand-labelled accuracy benchmark

A separate committed ground-truth corpus measures five core analysis tasks. The current generated result reports zero false positives and zero false negatives on the committed benchmark cases:

| Task | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Environment-variable discovery | 100.0% | 100.0% | 100.0% | 11 | 0 | 0 |
| Feature flags | 100.0% | 100.0% | 100.0% | 2 | 0 | 0 |
| Configuration declarations | 100.0% | 100.0% | 100.0% | 11 | 0 | 0 |
| Test evidence | 100.0% | 100.0% | 100.0% | 6 | 0 | 0 |
| Branch inference | 100.0% | 100.0% | 100.0% | 7 | 0 | 0 |

Aggregate metrics on this committed corpus:

- **Micro precision:** 100.0%
- **Micro recall:** 100.0%
- **Micro F1:** 100.0%
- **Macro F1:** 100.0%
- **True positives:** 37
- **False positives:** 0
- **False negatives:** 0

See [`validation/results/accuracy.md`](validation/results/accuracy.md) and [`validation/results/accuracy.json`](validation/results/accuracy.json) for the exact generated evidence and label policy.

This benchmark is intentionally **small, transparent and corpus-specific**. It includes deliberately difficult positive and negative examples, but it is not claimed to estimate accuracy across all repositories, languages or configuration frameworks.

## Historical 10-project baseline

The earlier real-world suite remains published for historical comparison. Its current regenerated result contains:

- **10** pinned repositories
- **17,777** configuration inputs
- **639** inputs with detected test/runtime evidence
- **3.6%** aggregate observed key coverage
- **1,381.657 seconds** recorded total scan time

See [`validation/results/real-world.md`](validation/results/real-world.md) and [`validation/results/real-world.json`](validation/results/real-world.json). Do not combine this historical baseline with the frozen external holdout when reporting one aggregate result.

## Reproduce

Hand-labelled accuracy:

```bash
python validation/accuracy/run_accuracy.py \
  --corpus validation/accuracy/corpus.json \
  --json validation/results/accuracy.json \
  --markdown validation/results/accuracy.md
```

Frozen external holdout (network access required; the full corpus is computationally expensive):

```bash
python validation/run_external_holdout.py \
  --manifest validation/external_holdout_projects.json \
  --baseline-manifest validation/real_world_projects.json \
  --reviews validation/external_holdout_reviews.json \
  --profile full \
  --json validation/results/external-holdout-full.json \
  --markdown validation/results/external-holdout-full.md
```

Historical baseline:

```bash
python validation/run_real_world.py \
  --manifest validation/real_world_projects.json \
  --reviews validation/real_world_reviews.json \
  --json validation/results/real-world.json \
  --markdown validation/results/real-world.md
```

The dedicated external-holdout workflow validates the frozen manifest, checks baseline disjointness and runs smoke/full profiles. The Hugging Face publishing workflow separately verifies that the public Space metrics stay synchronized with the committed validation JSON before uploading.

## Claim boundaries

- External repository coverage is observational ConfigReach output, not independently labelled ground truth.
- External precision/recall/F1 is not claimed until an independently labelled holdout sample is completed.
- The small hand-labelled benchmark reports exactly the committed cases and does not imply universal 100% accuracy.
- Runtime measurements depend on repository size, scanner version and runner hardware; cumulative per-repository runtime is not parallel workflow wall-clock elapsed time.
- Upstream projects are external validation targets; their inclusion does not imply endorsement of ConfigReach by those projects.
