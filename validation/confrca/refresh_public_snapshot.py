from __future__ import annotations

import csv
import hashlib
import json
import random
import time
import urllib.error
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
BENCHMARK_CONFIG = "confrca_bench"
BENCHMARK_SPLIT = "train"
EXPECTED_LABEL_ROWS = 2374


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _get_json_with_retry(url: str, *, attempts: int = 8) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ConfigReach/0.9.3 external-validation",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as response:  # nosec B310
                payload = json.load(response)
            if not isinstance(payload, dict):
                raise RuntimeError(f"expected JSON object from {url}")
            return payload
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            retryable = not isinstance(exc, urllib.error.HTTPError) or exc.code in {
                408,
                425,
                429,
                500,
                502,
                503,
                504,
            }
            if not retryable or attempt == attempts:
                raise
            delay = min(2 ** (attempt - 1), 30) + random.random()
            print(
                f"Transient dataset-viewer error ({exc}); retry {attempt}/{attempts} "
                f"after {delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)
    raise RuntimeError(f"unreachable retry loop for {url}: {last_error}")


def _download_label_rows() -> tuple[list[dict], list[str], int]:
    rows: list[dict] = []
    urls: list[str] = []
    offset = 0
    page_size = 100
    total: int | None = None

    while total is None or offset < total:
        query = urllib.parse.urlencode(
            {
                "dataset": DATASET_ID,
                "config": BENCHMARK_CONFIG,
                "split": BENCHMARK_SPLIT,
                "offset": offset,
                "length": page_size,
            }
        )
        url = f"{DATASETS_ROWS_ENDPOINT}?{query}"
        payload = _get_json_with_retry(url)

        if total is None:
            total = int(payload.get("num_rows_total", 0))
            if total <= 0:
                raise RuntimeError("ConfRCA viewer returned no benchmark rows")
            if total != EXPECTED_LABEL_ROWS:
                raise RuntimeError(
                    "ConfRCA benchmark row count changed; review upstream before refreshing: "
                    f"expected={EXPECTED_LABEL_ROWS}, observed={total}"
                )

        page = payload.get("rows", [])
        if not page:
            raise RuntimeError(
                f"ConfRCA viewer stopped early at offset={offset}; expected_total={total}"
            )

        for item in page:
            raw = item.get("row", item)
            missing = [column for column in LABEL_COLUMNS if column not in raw]
            if missing:
                raise RuntimeError(f"ConfRCA benchmark row is missing columns: {missing}")
            rows.append({column: raw.get(column) for column in LABEL_COLUMNS})

        urls.append(url)
        offset += len(page)
        print(f"Fetched ConfRCA rows {offset}/{total}", flush=True)

    if len(rows) != total:
        raise RuntimeError(
            f"ConfRCA row-count mismatch: downloaded={len(rows)}, expected={total}"
        )
    return rows, urls, total


def _derive_labelled_configuration_rows(label_rows: list[dict]) -> list[dict]:
    unique: dict[tuple[str, str, str], dict] = {}
    for row in label_rows:
        project = str(row.get("project") or "").strip()
        version = str(row.get("version") or "").strip()
        for key in ("config1_id", "config2_id"):
            name = str(row.get(key) or "").strip()
            if not (project and version and name):
                continue
            identity = (project, version, name)
            unique[identity] = {
                "id": name,
                "project": project,
                "version": version,
                "config_file": "",
                "name": name,
                "value": "",
                "description": "Derived from a human-labelled ConfRCA dependency-pair endpoint.",
            }
    return [unique[key] for key in sorted(unique)]


def _write_csv(path: Path, rows: list[dict], columns: tuple[str, ...]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    return len(rows)


def refresh_public_snapshot(data_dir: Path) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)

    label_rows, page_urls, label_count_expected = _download_label_rows()
    registry_rows = _derive_labelled_configuration_rows(label_rows)

    registry_csv = data_dir / "config_version.csv"
    labels_csv = data_dir / "confrca_labels.csv"
    registry_count = _write_csv(registry_csv, registry_rows, REGISTRY_COLUMNS)
    label_count = _write_csv(labels_csv, label_rows, LABEL_COLUMNS)
    registry_sha = _sha256(registry_csv)
    labels_sha = _sha256(labels_csv)

    source = {
        "schema_version": 2,
        "dataset": DATASET_ID,
        "dataset_page": DATASET_PAGE,
        "upstream_revision": (
            "public Dataset Viewer snapshot; exact reduced snapshot pinned by SHA-256"
        ),
        "license": DATASET_LICENSE,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "External validation of ConfigReach configuration discovery and "
            "pairwise dependency-scope signal on the human-labelled ConfRCA benchmark."
        ),
        "transport": {
            "service": "Hugging Face datasets-server /rows",
            "authentication": "none",
            "config": BENCHMARK_CONFIG,
            "split": BENCHMARK_SPLIT,
            "page_size": 100,
            "pages_fetched": len(page_urls),
            "retry_policy": "8 attempts for transient 408/425/429/5xx errors",
        },
        "files": {
            "config_version": {
                "provenance": (
                    "Derived positive configuration set: unique config1_id/config2_id values "
                    "from the human-labelled confrca_bench rows, grouped by project/version."
                ),
                "scope": "configs appearing in labelled ConfRCA pairs; not the full upstream registry",
                "vendored_sha256": registry_sha,
                "vendored_rows": registry_count,
                "vendored_file": registry_csv.name,
                "vendored_columns": list(REGISTRY_COLUMNS),
            },
            "confrca_bench": {
                "upstream_config": BENCHMARK_CONFIG,
                "upstream_split": BENCHMARK_SPLIT,
                "upstream_rows": label_count_expected,
                "vendored_sha256": labels_sha,
                "vendored_rows": label_count,
                "vendored_file": labels_csv.name,
                "vendored_columns": list(LABEL_COLUMNS),
            },
        },
        "claim_boundary": (
            "Configuration-discovery recall is measured only over configuration keys that appear "
            "in ConfRCA's human-labelled dependency pairs. It must not be described as recall over "
            "the complete config_version.parquet registry. Pair classification uses all 2,374 "
            "human-labelled confrca_bench rows."
        ),
        "redistribution_note": (
            "The repository vendors only the reduced columns needed for evaluation. Original "
            "ConfRCA data remain CC-BY-4.0 and attributable to ConfRCA."
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
                "labelled_configuration_rows": snapshot["files"]["config_version"]["vendored_rows"],
                "label_rows": snapshot["files"]["confrca_bench"]["vendored_rows"],
                "registry_sha256": snapshot["files"]["config_version"]["vendored_sha256"],
                "labels_sha256": snapshot["files"]["confrca_bench"]["vendored_sha256"],
            },
            sort_keys=True,
        )
    )
