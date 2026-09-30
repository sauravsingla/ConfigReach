# Curated 50K detection benchmark

This directory contains a **50,000-case controlled curated benchmark** for ConfigReach configuration-input detection. It has exactly **25,000 positive** and **25,000 negative** scenarios, with unique scenario IDs and unique expected keys.

The corpus spans Python, JavaScript, TypeScript, Go, Java, Kotlin, C#, Rust, Ruby, PHP, Shell, dotenv, JSON, TOML, INI/CFG, Java properties, YAML, Docker/Containerfile, Kubernetes, Helm, GitHub Actions, Terraform, Make, and JSON Schema. Negative cases include comments, string lookalikes, custom APIs, plain literals, dynamic names, and format-specific value-only decoys.

## Data integrity

The exact JSONL is transported in `data/shards/` as base64-encoded chunks of an XZ archive so the GitHub API can store it as UTF-8 text. Run:

```bash
python validation/curated_50k/rebuild_dataset.py
```

The rebuild script verifies every shard plus the reconstructed XZ and JSONL SHA-256 values recorded in `manifest.json`. The resulting file is `validation/curated_50k/data/configreach_50k_scenarios.jsonl`.

## Run the benchmark

```bash
python validation/curated_50k/rebuild_dataset.py
python validation/curated_50k/run_benchmark.py
```

The benchmark calls the production `configreach.engine.scan()` entry point and writes aggregate/per-group/per-variant evidence to `validation/results/curated_50k.json`, a human-readable summary to `validation/results/curated_50k.md`, and row-level classifications to `validation/results/curated_50k_predictions.csv`.

## Interpretation

This is a controlled curated benchmark with deterministic ground-truth labels. It is useful for precision/recall regression and adversarial stress testing, but it is **not** an independently human-labelled real-world corpus and should not be presented as universal real-world accuracy.
