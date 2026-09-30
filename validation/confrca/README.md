# ConfRCA external validation

This directory contains a reproducible external validation of ConfigReach against the independently published **ConfRCA** dataset (`iainzhang/confRCA`, CC-BY-4.0).

The benchmark intentionally separates two questions:

1. **Configuration discovery recall.** `config_version` contains 2,213 externally curated configuration options across five Hadoop-ecosystem projects. ConfigReach detections that match this registry are true positives and missed registry options are false negatives. ConfigReach-only detections are reported as **out-of-registry** rather than automatically counted as false positives, because absence from a registry does not prove that a detected internal/test/deprecated/undocumented key is invalid.
2. **Human-labelled dependency-pair transfer evaluation.** `confrca_bench` contains 2,374 pairs with human `True`/`False` dependency labels. For this secondary evaluation only, ConfigReach predicts a positive when both keys occur in at least one existing ConfigReach dependency scope. This yields TP/FP/TN/FN, precision, recall and F1 against human labels. It evaluates the scope-co-occurrence signal and must not be presented as general scanner accuracy or causal-dependency classification capability.

## Frozen evidence

`data/config_version.csv` is the complete configuration registry required for the discovery benchmark. `data/confrca_labels.csv` is a column-reduced copy of the labelled pair table containing only the fields required for evaluation; the large prompt and trace payloads are not duplicated in this repository. `data/SOURCE.json` records the immutable upstream revision, hashes, retrieval time, row counts, transport and licence.

The generated files preserve ConfRCA's CC-BY-4.0 licensing and attribution. The authoritative upstream dataset remains:

- https://huggingface.co/datasets/iainzhang/confRCA
- https://github.com/IainZhang/confRCA

## Refresh the source snapshot

Hugging Face currently returns HTTP 401 to anonymous requests from GitHub-hosted runners for this dataset, including the dataset page, Viewer API, raw-file endpoints and Git transport. ConfigReach therefore does **not** make normal CI depend on a live ConfRCA download.

To refresh the frozen snapshot, supply a Hugging Face token that can read `iainzhang/confRCA` in the local environment. This token is needed only for the refresh step and does not need to be stored as a repository secret.

```bash
python -m pip install -e ".[dev]" pyarrow huggingface_hub hf_xet
export HF_TOKEN="<hugging-face-read-token>"
python validation/confrca/refresh_public_snapshot.py
```

The refresher resolves one immutable upstream revision, downloads both benchmark files from that revision, verifies the expected 2,213 and 2,374 row counts, and writes SHA-256 provenance into `data/SOURCE.json`.

## Reproduce from frozen evidence

After the reduced snapshot has been committed, reproduction is offline with respect to Hugging Face and needs no Hugging Face credentials:

```bash
python -m pip install -e ".[dev]"
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
