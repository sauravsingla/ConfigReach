# ConfRCA external validation

This directory contains a reproducible external validation of ConfigReach against the independently published **ConfRCA** dataset (`iainzhang/confRCA`, CC-BY-4.0).

The benchmark intentionally separates two questions:

1. **Configuration discovery recall.** `config_version` contains 2,213 externally curated configuration options across five Hadoop-ecosystem projects. ConfigReach detections that match this registry are true positives and missed registry options are false negatives. ConfigReach-only detections are reported as **out-of-registry** rather than automatically counted as false positives, because absence from a registry does not prove that a detected internal/test/deprecated/undocumented key is invalid.
2. **Human-labelled dependency-pair transfer evaluation.** `confrca_bench` contains 2,374 pairs with human `True`/`False` dependency labels. For this secondary evaluation only, ConfigReach predicts a positive when both keys occur in at least one existing ConfigReach dependency scope. This yields TP/FP/TN/FN, precision, recall and F1 against human labels. It evaluates the scope-co-occurrence signal and must not be presented as general scanner accuracy or causal-dependency classification capability.

## Vendored data

`data/config_version.csv` is the complete configuration registry required for the discovery benchmark. `data/confrca_labels.csv` is a column-reduced copy of the labelled pair table containing only the fields required for evaluation; the very large prompt and trace payloads are not duplicated in this repository. `data/SOURCE.json` records the immutable upstream revision, hashes, retrieval time, row counts, transport and licence.

The generated files preserve ConfRCA's CC-BY-4.0 licensing and attribution. The authoritative upstream dataset remains:

- https://huggingface.co/datasets/iainzhang/confRCA
- https://github.com/IainZhang/confRCA

## Reproduce

The data refresh uses the public Hugging Face Git repository plus Git LFS rather than depending on the live Dataset Viewer/REST endpoints.

```bash
python -m pip install -e ".[dev]" pyarrow
git lfs version
python validation/confrca/refresh_public_snapshot.py
python validation/confrca/run_confrca_benchmark.py
pytest -q tests/test_confrca_benchmark.py
```

Generated evidence is written to:

- `validation/confrca/data/config_version.csv`
- `validation/confrca/data/confrca_labels.csv`
- `validation/confrca/data/SOURCE.json`
- `validation/results/confrca.json`
- `validation/results/confrca.md`

The benchmark downloads the exact source-code versions named by ConfRCA, statically scans them, and does **not** execute target application code or install target project dependencies.

## Claim boundary

The registry supports **recall** against externally published positive configuration keys. ConfigReach-only detections are reported separately and are not called false positives without independent adjudication. The dependency-pair precision/recall/F1 numbers evaluate only the existing shared-scope co-occurrence signal against ConfRCA's human labels; they are not general scanner precision/recall or a claim that ConfigReach is a causal-dependency classifier.
