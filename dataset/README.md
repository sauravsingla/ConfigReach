# ConfigReach Curated 50K Benchmark — Kaggle Package

A Kaggle-ready package of the ConfigReach controlled configuration-input detection benchmark.

## Dataset overview

- **50,000 scenarios**
- **25,000 positive** and **25,000 negative** cases
- **24 technology/configuration groups**
- **50,000 unique scenario IDs**
- **50,000 unique expected keys**
- Deterministic ground-truth labels for reproducible precision/recall evaluation

The benchmark covers Python, JavaScript, TypeScript, Go, Java, Kotlin, C#, Rust, Ruby, PHP, Shell, dotenv, JSON, TOML, INI/CFG, Java properties, YAML, Dockerfile/Containerfile, Kubernetes, Helm, GitHub Actions, Make, Terraform, and JSON Schema.

## Files

| File | Purpose |
|---|---|
| `configreach_50k_scenarios.jsonl` | Main labeled benchmark dataset (50,000 rows) |
| `configreach_50k_predictions.csv` | Row-level ConfigReach benchmark predictions and TP/FP/TN/FN classification |
| `manifest.json` | Dataset integrity, class balance, group counts, byte size, and SHA-256 |
| `benchmark.md` | Aggregate benchmark result summary |
| `dataset-metadata.json` | Kaggle CLI dataset metadata |
| `LICENSE` | MIT license |

## Main dataset schema

Each JSONL row contains:

- `scenario_id`: unique scenario identifier
- `group`: language or configuration format
- `variant`: positive/negative scenario pattern
- `expected_detect`: deterministic ground-truth boolean label
- `expected_key`: expected configuration key
- `suggested_filename`: representative filename for materialization
- `snippet`: source/configuration snippet used by the benchmark

## Reproducibility

The canonical generator lives at:

`validation/curated_50k/generate_dataset.py`

The benchmark runner lives at:

`validation/curated_50k/run_benchmark.py`

The committed manifest records the SHA-256 of the generated JSONL so users can verify that the Kaggle package is identical to the canonical ConfigReach benchmark.

## Kaggle upload

From the repository root:

```bash
kaggle datasets create -p dataset --public -t
```

The included `dataset-metadata.json` is prefilled for the `sauravsingla` Kaggle namespace. If the Kaggle account uses a different username or organization slug, change only the prefix of the `id` field before running the command.

## Important scope note

This is a **controlled curated benchmark with deterministic ground-truth labels**. It is intended for reproducible precision/recall regression testing and adversarial stress testing. It is **not** an independently human-labelled real-world corpus and should not be presented as universal real-world accuracy.

## License

MIT License. See `LICENSE`.
