from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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
    _write_csv,
)

PUBLIC_REPO = "https://huggingface.co/datasets/iainzhang/confRCA.git"
PUBLIC_FILES = {
    "config_version": "config_version.parquet",
    "confrca_bench": "confrca_bench.parquet",
}
EXPECTED_REGISTRY_ROWS = 2213
EXPECTED_LABEL_ROWS = 2374


def _run(command: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_real_parquet(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"ConfRCA file missing after public clone: {path.name}")
    if path.stat().st_size < 8:
        raise RuntimeError(f"ConfRCA file is unexpectedly small: {path.name}")
    with path.open("rb") as handle:
        if handle.read(4) != b"PAR1":
            raise RuntimeError(
                f"{path.name} is not materialized Parquet data. Git LFS/Xet content "
                "was not downloaded by the public clone."
            )


def refresh_public_snapshot(data_dir: Path) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="configreach-confrca-public-") as tmp:
        tmpdir = Path(tmp)
        checkout = tmpdir / "confRCA"

        # Hugging Face's normal REST/file endpoints currently reject anonymous requests
        # from GitHub-hosted runners for this public dataset. Public Git transport is
        # independent of those APIs and lets Git LFS/Xet materialize the repository files.
        _run(["git", "lfs", "install", "--local"])
        _run(["git", "clone", "--depth", "1", PUBLIC_REPO, str(checkout)])
        upstream_revision = _run(["git", "rev-parse", "HEAD"], cwd=checkout)

        registry_parquet = checkout / PUBLIC_FILES["config_version"]
        labels_parquet = checkout / PUBLIC_FILES["confrca_bench"]
        _assert_real_parquet(registry_parquet)
        _assert_real_parquet(labels_parquet)

        registry_sha = _sha256(registry_parquet)
        labels_sha = _sha256(labels_parquet)
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
                "ConfRCA configuration registry row count changed; review upstream before "
                f"refreshing evidence: expected={EXPECTED_REGISTRY_ROWS}, observed={registry_count}"
            )
        if label_count != EXPECTED_LABEL_ROWS:
            raise RuntimeError(
                "ConfRCA labelled benchmark row count changed; review upstream before "
                f"refreshing evidence: expected={EXPECTED_LABEL_ROWS}, observed={label_count}"
            )

        source = {
            "schema_version": 3,
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
                "client": "git + git-lfs",
                "source": PUBLIC_REPO,
                "authentication": "none (public repository)",
                "reason": (
                    "Uses the dataset repository's public Git transport rather than live REST "
                    "or Dataset Viewer endpoints, which can reject anonymous GitHub-runner traffic."
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
