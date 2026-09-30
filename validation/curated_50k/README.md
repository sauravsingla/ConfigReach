# Curated 50K detection benchmark

This directory defines a **50,000-case controlled curated benchmark** for ConfigReach configuration-input detection. It contains exactly **25,000 positive** and **25,000 negative** scenarios with unique scenario IDs and unique expected keys.

The benchmark spans Python, JavaScript, TypeScript, Go, Java, Kotlin, C#, Rust, Ruby, PHP, Shell, dotenv, JSON, TOML, INI/CFG, Java properties, YAML, Docker/Containerfile, Kubernetes, Helm, GitHub Actions, Make, Terraform, and JSON Schema. Negative cases include comments, string lookalikes, custom APIs, plain literals, dynamic names, and format-specific value-only decoys.

## Materialize the dataset

```bash
python validation/curated_50k/generate_dataset.py
```

This deterministically writes `validation/curated_50k/data/configreach_50k_scenarios.jsonl` and refreshes `manifest.json`. The manifest records the row count, class balance, unique-ID/key counts, group distribution, byte size, and SHA-256 of the generated JSONL.

## Run the benchmark

```bash
python validation/curated_50k/generate_dataset.py
python validation/curated_50k/run_benchmark.py
```

The benchmark calls the production `configreach.engine.scan()` entry point and writes aggregate/per-group/per-variant evidence to `validation/results/curated_50k.json`, a human-readable summary to `validation/results/curated_50k.md`, and row-level classifications to `validation/results/curated_50k_predictions.csv`.

## Interpretation

This is a controlled curated benchmark with deterministic ground-truth labels. It is designed for precision/recall regression and adversarial stress testing. It is **not** an independently human-labelled real-world corpus and should not be presented as universal real-world accuracy.
