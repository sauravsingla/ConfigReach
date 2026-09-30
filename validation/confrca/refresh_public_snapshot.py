from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

from run_confrca_benchmark import (
    DATASET_ID,
    DATASET_LICENSE,
    DATASET_PAGE,
    LABEL_COLUMNS,
    REGISTRY_COLUMNS,
    _write_csv,
)

PUBLIC_FILES = {
    "config_version": "config_version.parquet",
    "confrca_bench": "confrca_bench.parquet",
}
EXPECTED_REGISTRY_ROWS = 2213
EXPECTED_LABEL_ROWS = 2374


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _require_hf_token() -> str:
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "HF_TOKEN is required only to refresh the ConfRCA source snapshot. "
            "Use a Hugging Face token that can read iainzhang/confRCA. After the "
            "reduced snapshot is committed, rerunning the benchmark does not require "
            "Hugging Face credentials or network access."
        )
    return token


def _download_file(
    filename: str,
    destination: Path,
    *,
    revision: str,
    cache_dir: Path,
    token: str,
) -> str:
    downloaded = Path(
        hf_hub_download(
            repo_id=DATASET_ID,
            filename=filename,
            repo_type="dataset",
            revision=revision,
            token=token,
            cache_dir=str(cache_dir),
            force_download=True,
        )
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(downloaded, destination)
    return _sha256(destination)


def refresh_public_snapshot(data_dir: Path) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    token = _require_hf_token()

    # Resolve once and pin both benchmark files to the same immutable upstream revision.
    info = HfApi(token=token).dataset_info(DATASET_ID)
    upstream_revision = str(info.sha or "").strip()
    if not upstream_revision:
        raise RuntimeError("Hugging Face did not return an immutable ConfRCA revision SHA")

    with tempfile.TemporaryDirectory(prefix="configreach-confrca-") as tmp:
        tmpdir = Path(tmp)
        cache_dir = tmpdir / "hf-cache"
        registry_parquet = tmpdir / PUBLIC_FILES["config_version"]
        labels_parquet = tmpdir / PUBLIC_FILES["confrca_bench"]

        registry_sha = _download_file(
            PUBLIC_FILES["config_version"],
            registry_parquet,
            revision=upstream_revision,
            cache_dir=cache_dir,
            token=token,
        )
        labels_sha = _download_file(
            PUBLIC_FILES["confrca_bench"],
            labels_parquet,
            revision=upstream_revision,
            cache_dir=cache_dir,
            token=token,
        )

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

        if registry_count != EXPECTED_REGISTRY_ROWS:
            raise RuntimeError(
                "ConfRCA configuration registry changed; review upstream before refreshing: "
                f"expected={EXPECTED_REGISTRY_ROWS}, observed={registry_count}"
            )
        if label_count != EXPECTED_LABEL_ROWS:
            raise RuntimeError(
                "ConfRCA labelled benchmark changed; review upstream before refreshing: "
                f"expected={EXPECTED_LABEL_ROWS}, observed={label_count}"
            )

        source = {
            "schema_version": 4,
            "dataset": DATASET_ID,
            "dataset_page": DATASET_PAGE,
            "upstream_revision": upstream_revision,
            "license": DATASET_LICENSE,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "purpose": (
                "External validation of ConfigReach configuration discovery and "
                "pairwise dependency-scope signal."
            ),
            "transport": {
                "client": "huggingface_hub",
                "authentication": "caller-supplied Hugging Face read token for snapshot refresh",
                "stored_repository_secret_required": False,
                "note": (
                    "Only the refresh step requires upstream access. The reduced snapshot is "
                    "committed with an immutable upstream revision and SHA-256 hashes so ordinary "
                    "benchmark reproduction and verification are offline and credential-free."
                ),
            },
            "files": {
                "config_version": {
                    "upstream_path": PUBLIC_FILES["config_version"],
                    "download_sha256": registry_sha,
                    "upstream_size": registry_parquet.stat().st_size,
                    "vendored_rows": registry_count,
                    "vendored_file": "config_version.csv",
                    "vendored_columns": list(REGISTRY_COLUMNS),
                },
                "confrca_bench": {
                    "upstream_path": PUBLIC_FILES["confrca_bench"],
                    "download_sha256": labels_sha,
                    "upstream_size": labels_parquet.stat().st_size,
                    "vendored_rows": label_count,
                    "vendored_file": "confrca_labels.csv",
                    "vendored_columns": list(LABEL_COLUMNS),
                },
            },
            "claim_boundary": (
                "Configuration discovery is evaluated against the complete published "
                "config_version registry (2,213 rows). Dependency classification is evaluated "
                "against all 2,374 published human-labelled confrca_bench rows."
            ),
            "redistribution_note": (
                "The repository vendors the complete configuration registry and a column-reduced "
                "copy of the labelled benchmark required for evaluation. Original ConfRCA data "
                "remain CC-BY-4.0 and attributable to ConfRCA."
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
                "upstream_revision": snapshot["upstream_revision"],
                "registry_rows": snapshot["files"]["config_version"]["vendored_rows"],
                "label_rows": snapshot["files"]["confrca_bench"]["vendored_rows"],
                "registry_sha256": snapshot["files"]["config_version"]["download_sha256"],
                "labels_sha256": snapshot["files"]["confrca_bench"]["download_sha256"],
            },
            sort_keys=True,
        )
    )
