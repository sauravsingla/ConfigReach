# Validation

This directory keeps three deliberately different kinds of evidence separate:

1. **Real-world external-project scans** — ConfigReach is run against pinned commits from recognizable open-source projects. These runs measure discovered configuration inputs, detected test evidence, configuration coverage, scan runtime, findings and manually reviewed false-positive/false-negative examples. Target application code is not executed and target dependencies are not installed.
2. **Frozen external holdout** — a second, baseline-disjoint set of pinned public repositories selected before ConfigReach results are inspected. This tests out-of-sample behavior and scale without silently tuning the published real-world suite.
3. **Hand-labelled accuracy benchmark** — a small transparent corpus with labels committed independently of scanner output. The scorer publishes precision, recall and F1 for environment-variable discovery, feature flags, configuration declarations, test evidence and branch inference.

These should not be conflated. Repository-level configuration coverage describes what ConfigReach observes; it is **not** ground truth. Precision/recall claims come only from the hand-labelled corpus.

## Reproduce measured accuracy

```bash
python validation/accuracy/run_accuracy.py \
  --corpus validation/accuracy/corpus.json \
  --json validation/results/accuracy.json \
  --markdown validation/results/accuracy.md
```

The corpus includes deliberately difficult cases rather than only supported happy paths: dynamic environment-key construction, JavaScript `process.env` destructuring, Go variable-key lookups, unrelated `variation(...)` calls, project metadata that should not be treated as runtime configuration, helper-mediated test evidence and boolean domains without actual decision branches.

## Reproduce real-world validation

The external suite requires network access because it fetches pinned GitHub commits:

```bash
python validation/run_real_world.py \
  --manifest validation/real_world_projects.json \
  --reviews validation/real_world_reviews.json \
  --json validation/results/real-world.json \
  --markdown validation/results/real-world.md
```

Upstream projects are pinned by commit SHA so later upstream changes cannot silently change a published result.

## Reproduce the frozen external holdout

Validate corpus integrity without fetching any upstream repository:

```bash
python validation/run_external_holdout.py \
  --manifest validation/external_holdout_projects.json \
  --baseline-manifest validation/real_world_projects.json \
  --profile full \
  --validate-only
```

Run the normal CI smoke profile:

```bash
python validation/run_external_holdout.py \
  --profile smoke \
  --json validation/results/external-holdout-smoke.json \
  --markdown validation/results/external-holdout-smoke.md
```

Run every frozen holdout project:

```bash
python validation/run_external_holdout.py \
  --profile full \
  --json validation/results/external-holdout-full.json \
  --markdown validation/results/external-holdout-full.md
```

The holdout runner verifies full commit SHAs, profile integrity and zero repository overlap with `real_world_projects.json` before it fetches anything. See [`EXTERNAL_HOLDOUT.md`](EXTERNAL_HOLDOUT.md) for the selection policy, corpus, claim boundaries and update rules.

The dedicated `external-holdout.yml` workflow runs the smoke profile on relevant pull requests and pushes, the full profile monthly, and either profile on manual dispatch. Generated JSON and Markdown evidence are uploaded as workflow artifacts.

## Manual review policy

Real-world and holdout false positives and false negatives are reported as **targeted manual spot checks**, not as exhaustive error rates over an entire upstream repository. Every annotation must include the project, key/pattern and a short reason. The report explicitly states this limitation.

Precision/recall claims come only from the hand-labelled corpus, where the complete committed label set is available for inspection.

## Interpreting runtime

Runtime is wall-clock static scan time on the recorded GitHub-hosted runner. It is useful for reproducibility and order-of-magnitude comparison but is not a hardware-independent performance guarantee.
