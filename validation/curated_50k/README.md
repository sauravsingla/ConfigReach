# ConfigReach Curated 50K Benchmark

This directory contains a **50,000-case curated benchmark** for deterministic precision/recall regression testing across ConfigReach-supported programming languages and configuration formats.

The benchmark deliberately mixes real configuration reads/declarations with adversarial negatives such as comments, string lookalikes, dynamic names, custom APIs, member-call lookalikes, and value-only configuration text.

## Corpus

- Scenarios: **50,000**
- Ground-truth positives: **25,000**
- Ground-truth negatives: **25,000**
- Unique scenario IDs: **50,000**
- Unique expected keys: **50,000**
- Languages/formats: Python, JavaScript, TypeScript, Go, Java, Kotlin, C#, Rust, Ruby, PHP, Shell, dotenv, JSON, TOML, INI/CFG, properties, YAML, Dockerfile, Kubernetes, Helm, GitHub Actions, Make, Terraform, JSON Schema

`generate_dataset.py` is the canonical deterministic definition. CI materializes the complete dataset at `data/configreach_50k_scenarios.jsonl`; `manifest.json` records its SHA-256 and counts.

## Run

```bash
python validation/curated_50k/generate_dataset.py
python validation/curated_50k/run_benchmark.py
```

The benchmark runner materializes each scenario in an isolated directory, invokes the real `configreach.engine.scan()` over the corpus, and scores each row by whether its `expected_key` appears in the report.

## Detection hardening under test

The accompanying production change adds a conservative lexical-hardening pass after ConfigReach's existing semantic/hardening passes. It suppresses built-in regex detections when API-looking tokens occur only in comments or other non-executable regions while preserving executable interpolation/template expressions and existing AST/structured/validator/runtime evidence.

The benchmark-specific result is written to `results/configreach_50k_runtime.json`. It should not be interpreted as a claim of universal real-world accuracy; external independently labelled real-world evaluation remains a separate requirement.
