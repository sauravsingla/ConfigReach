# External holdout validation

`external-holdout-v1` is a second external-project corpus designed to answer a narrower question than the existing real-world suite:

> Does the current ConfigReach implementation behave usefully on a frozen set of external repositories that was not used to develop or tune the published real-world benchmark?

The holdout is intentionally separate from `real_world_projects.json`. It is not a replacement for the hand-labelled accuracy corpus and it does not convert observed repository coverage into precision/recall.

## Integrity rules

The runner enforces these rules before any repository is fetched:

1. every project is pinned to a lowercase 40-character Git commit SHA;
2. every project includes source provenance and a selection rationale;
3. every project belongs to the `full` profile;
4. profile names must be declared by the suite;
5. repository names must be unique;
6. the holdout must have zero repository overlap with `validation/real_world_projects.json`;
7. the manifest declares that selection was frozen before ConfigReach results were inspected.

`--validate-only` checks all of these conditions without requiring network access.

## Frozen v1 corpus

The v1 corpus spans the built-in language/configuration adapters with public upstream projects:

| Project | Primary validation angle | Profiles |
|---|---|---|
| `apache/airflow` | Python + configuration-heavy application | full |
| `PrefectHQ/prefect` | Python settings/workflow configuration | smoke, full |
| `vercel/next.js` | JavaScript/TypeScript environment behavior | full |
| `vitejs/vite` | JavaScript/TypeScript + dotenv semantics | smoke, full |
| `argoproj/argo-cd` | Go + Kubernetes/YAML deployment configuration | full |
| `spring-projects/spring-boot` | Java/Spring configuration properties | full |
| `dotnet/aspnetcore` | .NET `IConfiguration` and environment patterns | full |
| `astral-sh/uv` | Rust environment-driven CLI behavior | full |
| `rails/rails` | Ruby `ENV` access patterns | full |
| `laravel/framework` | PHP `env(...)` and config patterns | smoke, full |
| `terraform-aws-modules/terraform-aws-vpc` | Terraform variables/defaults/validation | smoke, full |

Exact commit SHAs are the source of truth in `external_holdout_projects.json`.

The projects are validation targets only. Their inclusion does not imply endorsement of ConfigReach by the upstream projects.

## Profiles

The `smoke` profile is small enough for ordinary pull-request and push CI. It intentionally crosses multiple adapters and configuration formats.

The `full` profile contains every frozen holdout project. It runs on the monthly schedule and can also be launched manually from the `External holdout validation` workflow. Keeping the full suite off every pull request avoids turning large upstream clones and static scans into routine CI latency.

## Reproduce locally

Manifest integrity only, without fetching upstream repositories:

```bash
python validation/run_external_holdout.py \
  --manifest validation/external_holdout_projects.json \
  --baseline-manifest validation/real_world_projects.json \
  --profile full \
  --validate-only
```

Smoke scan:

```bash
python validation/run_external_holdout.py \
  --manifest validation/external_holdout_projects.json \
  --baseline-manifest validation/real_world_projects.json \
  --reviews validation/external_holdout_reviews.json \
  --profile smoke \
  --json validation/results/external-holdout-smoke.json \
  --markdown validation/results/external-holdout-smoke.md
```

Full scan:

```bash
python validation/run_external_holdout.py \
  --manifest validation/external_holdout_projects.json \
  --baseline-manifest validation/real_world_projects.json \
  --reviews validation/external_holdout_reviews.json \
  --profile full \
  --json validation/results/external-holdout-full.json \
  --markdown validation/results/external-holdout-full.md
```

A single frozen repository can be isolated for debugging without changing the manifest:

```bash
python validation/run_external_holdout.py \
  --profile full \
  --repo spring-projects/spring-boot
```

The runner still refuses repository names that are not already present in the frozen corpus.

## What the report means

The report records discovered configuration inputs, inputs with detected test/runtime evidence, observed key coverage, scanner runtime, findings, warnings and optional manual review annotations.

These are ConfigReach observations. They are useful for detecting regressions, adapter blind spots and scale problems across external codebases, but they are not labelled classification outcomes. Precision, recall and F1 remain sourced from `validation/accuracy/`.

## Updating the corpus

Do not silently replace projects because a ConfigReach result is inconvenient. Changes to the holdout require a new manifest revision or suite ID, a documented rationale and review of overlap with the baseline suite. Pin the replacement to an immutable commit before running ConfigReach on it.

This rule keeps the holdout useful as out-of-sample evidence rather than another tuning set.
