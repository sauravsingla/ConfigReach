from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from run_confrca_benchmark import (
    DATASET_ID,
    DATASET_LICENSE,
    DATASET_PAGE,
    LABEL_COLUMNS,
    REGISTRY_COLUMNS,
)

DATASETS_ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"
PUBLIC_CONFIGS = {
    "config_version": "config_version",
    "confrca_bench": "confrca_bench",
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


def _download_public_rows(config: str, columns: tuple[str, ...]) -> tuple[list[dict], list[str]]:
    """Fetch a complete public Hugging Face dataset config via datasets-server.

    The normal huggingface.co repository API currently returns HTTP 401 from GitHub-hosted
    runners for this otherwise public dataset. The public Dataset Viewer service is a
    separate, read-only endpoint and exposes the same tabular rows without a token.
    """

    rows: list[dict] = []
    urls: list[str] = []
    offset = 0
    page_size = 100
    total: int | None = None

    while total is None or offset < total:
        query = urllib.parse.urlencode(
            {
                "dataset": DATASET_ID,
                "config": config,
                "split": "train",
                "offset": offset,
                "length": page_size,
            }
        )
        url = f"{DATASETS_ROWS_ENDPOINT}?{query}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ConfigReach/0.9.3 external-validation",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=180) as response:  # nosec B310
            payload = json.load(response)

        if total is None:
            total = int(payload.get("num_rows_total", 0))
            if total <= 0:
                raise RuntimeError(f"datasets-server returned no rows for config={config!r}")

        page = payload.get("rows", [])
        if not page:
            raise RuntimeError(
                f"datasets-server stopped early for config={config!r}: "
                f"offset={offset}, expected_total={total}"
            )

        for item in page:
            raw = item.get("row", item)
            missing = [column for column in columns if column not in raw]
            if missing:
                raise RuntimeError(
                    f"datasets-server row for config={config!r} is missing columns: {missing}"
                )
            rows.append({column: raw.get(column) for column in columns})

        urls.append(url)
        offset += len(page)

    if len(rows) != total:
        raise RuntimeError(
            f"datasets-server row-count mismatch for config={config!r}: "
            f"downloaded={len(rows)}, expected={total}"
        )
    return rows, urls


def _write_csv(path: Path, rows: list[dict], columns: tuple[str, ...]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})
    return len(rows)


def refresh_public_snapshot(data_dir: Path) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)

    registry_rows, registry_urls = _download_public_rows(
        PUBLIC_CONFIGS["config_version"], REGISTRY_COLUMNS
    )
    label_rows, label_urls = _download_public_rows(
        PUBLIC_CONFIGS["confrca_bench"], LABEL_COLUMNS
    )

    registry_csv = data_dir / "config_version.csv"
    labels_csv = data_dir / "confrca_labels.csv"
    registry_count = _write_csv(registry_csv, registry_rows, REGISTRY_COLUMNS)
    label_count = _write_csv(labels_csv, label_rows, LABEL_COLUMNS)
    registry_sha = _sha256(registry_csv)
    labels_sha = _sha256(labels_csv)

    source = {
        "schema_version": 1,
        "dataset": DATASET_ID,
        "dataset_page": DATASET_PAGE,
        "upstream_revision": (
            "public datasets-server snapshot; exact vendored content is pinned by SHA-256"
        ),
        "license": DATASET_LICENSE,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "External validation of ConfigReach configuration discovery and "
            "pairwise dependency-scope signal."
        ),
        "transport": {
            "service": "Hugging Face datasets-server /rows",
            "authentication": "none",
            "reason": (
                "The huggingface.co repository API returned HTTP 401 from GitHub-hosted "
                "runners for this public dataset; the read-only public Dataset Viewer "
                "endpoint exposes the benchmark rows without credentials."
            ),
            "page_size": 100,
        },
        "files": {
            "config_version": {
                "upstream_config": PUBLIC_CONFIGS["config_version"],
                "upstream_split": "train",
                "pages_fetched": len(registry_urls),
                "vendored_sha256": registry_sha,
                "vendored_rows": registry_count,
                "vendored_file": registry_csv.name,
                "vendored_columns": list(REGISTRY_COLUMNS),
            },
            "confrca_bench": {
                "upstream_config": PUBLIC_CONFIGS["confrca_bench"],
                "upstream_split": "train",
                "pages_fetched": len(label_urls),
                "vendored_sha256": labels_sha,
                "vendored_rows": label_count,
                "vendored_file": labels_csv.name,
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
                "registry_sha256": snapshot["files"]["config_version"]["vendored_sha256"],
                "labels_sha256": snapshot["files"]["confrca_bench"]["vendored_sha256"],
            },
            sort_keys=True,
        )
    )
