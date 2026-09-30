from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from run_confrca_benchmark import (
    DATASET_ID,
    DATASET_LICENSE,
    DATASET_PAGE,
    LABEL_COLUMNS,
    REGISTRY_COLUMNS,
    _download,
    _write_csv,
)

# ConfRCA publishes these Parquet files directly in the public dataset repository.
# Using the Hub's public file endpoint avoids the datasets-server /parquet API,
# which can require an HF token even for public datasets.
PUBLIC_FILES = {
    "config_version": "https://huggingface.co/datasets/iainzhang/confRCA/resolve/main/config_version.parquet",
    "confrca_bench": "https://huggingface.co/datasets/iainzhang/confRCA/resolve/main/confrca_bench.parquet",
}


def refresh_public_snapshot(data_dir: Path) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="configreach-confrca-public-") as tmp:
        tmpdir = Path(tmp)
        registry_parquet = tmpdir / "config_version.parquet"
        labels_parquet = tmpdir / "confrca_bench.parquet"

        registry_sha = _download(PUBLIC_FILES["config_version"], registry_parquet)
        labels_sha = _download(PUBLIC_FILES["confrca_bench"], labels_parquet)

        registry_rows = pq.read_table(
            registry_parquet, columns=list(REGISTRY_COLUMNS)
        ).to_pylist()
        label_rows = pq.read_table(
            labels_parquet, columns=list(LABEL_COLUMNS)
        ).to_pylist()

        registry_count = _write_csv(
            data_dir / "config_version.csv", registry_rows, REGISTRY_COLUMNS
        )
        label_count = _write_csv(
            data_dir / "confrca_labels.csv", label_rows, LABEL_COLUMNS
        )

        source = {
            "schema_version": 1,
            "dataset": DATASET_ID,
            "dataset_page": DATASET_PAGE,
            "upstream_revision": "main snapshot; exact downloaded content pinned by SHA-256 below",
            "license": DATASET_LICENSE,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "purpose": (
                "External validation of ConfigReach configuration discovery and "
                "pairwise dependency-scope signal."
            ),
            "files": {
                "config_version": {
                    "upstream_url": PUBLIC_FILES["config_version"],
                    "download_sha256": registry_sha,
                    "upstream_size": registry_parquet.stat().st_size,
                    "vendored_rows": registry_count,
                    "vendored_file": "config_version.csv",
                },
                "confrca_bench": {
                    "upstream_url": PUBLIC_FILES["confrca_bench"],
                    "download_sha256": labels_sha,
                    "upstream_size": labels_parquet.stat().st_size,
                    "vendored_rows": label_count,
                    "vendored_file": "confrca_labels.csv",
                    "vendored_columns": list(LABEL_COLUMNS),
                },
            },
            "redistribution_note": (
                "The repository vendors the complete config_version registry and a "
                "column-reduced copy of the human-labelled confrca_bench table needed "
                "for evaluation, rather than the large prompt/trace payload. Original "
                "data remain CC-BY-4.0 and attributable to ConfRCA."
            ),
        }
        (data_dir / "SOURCE.json").write_text(
            json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return source


if __name__ == "__main__":
    snapshot = refresh_public_snapshot(Path("validation/confrca/data"))
    print(
        json.dumps(
            {
                "dataset": snapshot["dataset"],
                "registry_rows": snapshot["files"]["config_version"]["vendored_rows"],
                "label_rows": snapshot["files"]["confrca_bench"]["vendored_rows"],
                "registry_sha256": snapshot["files"]["config_version"]["download_sha256"],
                "labels_sha256": snapshot["files"]["confrca_bench"]["download_sha256"],
            },
            sort_keys=True,
        )
    )
