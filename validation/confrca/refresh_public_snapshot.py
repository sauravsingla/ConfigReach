from __future__ import annotations

import hashlib
import json
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _download_public_hub_file(
    filename: str,
    destination: Path,
    *,
    revision: str,
    cache_dir: Path,
) -> str:
    """Download one public ConfRCA file through the official Hub client.

    The Hub client is intentionally used instead of a hand-built /resolve URL. Public
    Hugging Face repositories may be served through Xet/CAS and require signed transport
    URLs that the client negotiates even when no authentication token is needed.
    """

    downloaded = Path(
        hf_hub_download(
            repo_id=DATASET_ID,
            filename=filename,
            repo_type="dataset",
            revision=revision,
            token=False,
            cache_dir=str(cache_dir),
            force_download=True,
        )
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(downloaded, destination)
    return _sha256(destination)


def refresh_public_snapshot(data_dir: Path) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)

    # Resolve main once, then download both files from the same immutable dataset commit.
    # This prevents a moving-main race between the registry and labelled benchmark files.
    dataset_info = HfApi().dataset_info(DATASET_ID, token=False)
    upstream_revision = str(dataset_info.sha)
    if not upstream_revision:
        raise RuntimeError("Hugging Face did not return an immutable ConfRCA revision SHA")

    with tempfile.TemporaryDirectory(prefix="configreach-confrca-public-") as tmp:
        tmpdir = Path(tmp)
        cache_dir = tmpdir / "hf-cache"
        registry_parquet = tmpdir / PUBLIC_FILES["config_version"]
        labels_parquet = tmpdir / PUBLIC_FILES["confrca_bench"]

        registry_sha = _download_public_hub_file(
            PUBLIC_FILES["config_version"],
            registry_parquet,
            revision=upstream_revision,
            cache_dir=cache_dir,
        )
        labels_sha = _download_public_hub_file(
            PUBLIC_FILES["confrca_bench"],
            labels_parquet,
            revision=upstream_revision,
            cache_dir=cache_dir,
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

        source = {
            "schema_version": 1,
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
                "authentication": "anonymous/public (token=False)",
                "reason": (
                    "Official Hub transport negotiates public Xet/CAS signed URLs; direct "
                    "/resolve URLs can return HTTP 401 on GitHub-hosted runners."
                ),
            },
            "files": {
                "config_version": {
                    "upstream_path": PUBLIC_FILES["config_version"],
                    "download_sha256": registry_sha,
                    "upstream_size": registry_parquet.stat().st_size,
                    "vendored_rows": registry_count,
                    "vendored_file": "config_version.csv",
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
                "upstream_revision": snapshot["upstream_revision"],
                "registry_rows": snapshot["files"]["config_version"]["vendored_rows"],
                "label_rows": snapshot["files"]["confrca_bench"]["vendored_rows"],
                "registry_sha256": snapshot["files"]["config_version"]["download_sha256"],
                "labels_sha256": snapshot["files"]["confrca_bench"]["download_sha256"],
            },
            sort_keys=True,
        )
    )
