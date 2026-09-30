from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configreach import __version__
from configreach.engine import scan

DATASET_ID = "iainzhang/confRCA"
DATASET_PAGE = "https://huggingface.co/datasets/iainzhang/confRCA"
DATASET_API = "https://datasets-server.huggingface.co/parquet?dataset=iainzhang%2FconfRCA"
DATASET_META_API = "https://huggingface.co/api/datasets/iainzhang/confRCA"
DATASET_LICENSE = "CC-BY-4.0"

PROJECT_SPECS = {
    "hcommon": {"repo": "apache/hadoop", "scope": "hadoop-common-project/hadoop-common"},
    "hdfs": {"repo": "apache/hadoop", "scope": "hadoop-hdfs-project/hadoop-hdfs"},
    "mapreduce": {"repo": "apache/hadoop", "scope": "hadoop-mapreduce-project"},
    "yarn": {"repo": "apache/hadoop", "scope": "hadoop-yarn-project"},
    "hbase": {"repo": "apache/hbase", "scope": "."},
}

REGISTRY_COLUMNS = ("id", "project", "version", "config_file", "name", "value", "description")
LABEL_COLUMNS = (
    "prompt_id",
    "project",
    "version",
    "config1_id",
    "config2_id",
    "dep_label",
    "dep_type",
)


@dataclass(frozen=True)
class DatasetFile:
    config: str
    split: str
    url: str
    filename: str
    size: int


def _json_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "ConfigReach-ConfRCA-validation/1"})
    with urllib.request.urlopen(req, timeout=60) as response:  # nosec B310 - fixed HTTPS URLs
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object from {url}")
    return payload


def _download(url: str, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    req = urllib.request.Request(url, headers={"User-Agent": "ConfigReach-ConfRCA-validation/1"})
    with urllib.request.urlopen(req, timeout=180) as response, destination.open("wb") as handle:  # nosec B310
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
            digest.update(chunk)
    return digest.hexdigest()


def _parquet_files() -> dict[str, DatasetFile]:
    payload = _json_get(DATASET_API)
    files: dict[str, DatasetFile] = {}
    for item in payload.get("parquet_files", []):
        if not isinstance(item, dict) or item.get("split") != "train":
            continue
        config = str(item.get("config", ""))
        if config in {"config_version", "confrca_bench"}:
            files[config] = DatasetFile(
                config=config,
                split="train",
                url=str(item["url"]),
                filename=str(item.get("filename", "0000.parquet")),
                size=int(item.get("size", 0)),
            )
    missing = {"config_version", "confrca_bench"} - set(files)
    if missing:
        raise RuntimeError(f"ConfRCA parquet API did not expose: {', '.join(sorted(missing))}")
    return files


def _write_csv(path: Path, rows: Iterable[dict], columns: tuple[str, ...]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
            count += 1
    return count


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def refresh_dataset(data_dir: Path) -> dict:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - exercised in benchmark workflow
        raise RuntimeError("ConfRCA refresh requires pyarrow: python -m pip install pyarrow") from exc

    files = _parquet_files()
    metadata = _json_get(DATASET_META_API)
    upstream_revision = str(metadata.get("sha", "unknown"))

    source_entries: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="configreach-confrca-download-") as tmp:
        tmpdir = Path(tmp)
        registry_parquet = tmpdir / "config_version.parquet"
        labels_parquet = tmpdir / "confrca_bench.parquet"

        registry_sha = _download(files["config_version"].url, registry_parquet)
        labels_sha = _download(files["confrca_bench"].url, labels_parquet)

        registry_table = pq.read_table(registry_parquet, columns=list(REGISTRY_COLUMNS))
        labels_table = pq.read_table(labels_parquet, columns=list(LABEL_COLUMNS))
        registry_rows = registry_table.to_pylist()
        label_rows = labels_table.to_pylist()

        registry_count = _write_csv(data_dir / "config_version.csv", registry_rows, REGISTRY_COLUMNS)
        label_count = _write_csv(data_dir / "confrca_labels.csv", label_rows, LABEL_COLUMNS)

        source_entries["config_version"] = {
            "upstream_url": files["config_version"].url,
            "download_sha256": registry_sha,
            "upstream_size": files["config_version"].size,
            "vendored_rows": registry_count,
            "vendored_file": "config_version.csv",
        }
        source_entries["confrca_bench"] = {
            "upstream_url": files["confrca_bench"].url,
            "download_sha256": labels_sha,
            "upstream_size": files["confrca_bench"].size,
            "vendored_rows": label_count,
            "vendored_file": "confrca_labels.csv",
            "vendored_columns": list(LABEL_COLUMNS),
        }

    source = {
        "schema_version": 1,
        "dataset": DATASET_ID,
        "dataset_page": DATASET_PAGE,
        "upstream_revision": upstream_revision,
        "license": DATASET_LICENSE,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "External validation of ConfigReach configuration discovery and pairwise dependency-scope signal.",
        "files": source_entries,
        "redistribution_note": (
            "The repository vendors the complete config_version registry and a column-reduced copy "
            "of the human-labelled confrca_bench table needed for evaluation, rather than the full "
            "large prompt/trace payload. Original data remain CC-BY-4.0 and attributable to ConfRCA."
        ),
    }
    (data_dir / "SOURCE.json").write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return source


def _canonical(value: object) -> str:
    return str(value or "").strip()


def _pair_key(left: object, right: object) -> tuple[str, str]:
    a, b = _canonical(left), _canonical(right)
    return (a, b) if a <= b else (b, a)


def _bool_label(value: object) -> bool:
    text = _canonical(value).lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise ValueError(f"unsupported ConfRCA dep_label: {value!r}")


def _safe_div(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _classification_metrics(tp: int, fp: int, tn: int, fn: int) -> dict:
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": _safe_div(tp + tn, tp + fp + tn + fn),
    }


def classify_registry(ground_truth: set[str], detected: set[str]) -> dict:
    true_positives = sorted(ground_truth & detected)
    false_negatives = sorted(ground_truth - detected)
    out_of_registry = sorted(detected - ground_truth)
    return {
        "ground_truth": len(ground_truth),
        "detected": len(detected),
        "tp": len(true_positives),
        "fn": len(false_negatives),
        "out_of_registry": len(out_of_registry),
        "recall": _safe_div(len(true_positives), len(ground_truth)),
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "out_of_registry_detections": out_of_registry,
        "claim_boundary": (
            "Out-of-registry detections are not automatically false positives: the external registry "
            "may omit internal, test-only, deprecated, dynamically constructed, or undocumented keys."
        ),
    }


def classify_pairs(rows: list[dict[str, str]], predicted_pairs: set[tuple[str, str]]) -> dict:
    tp = fp = tn = fn = 0
    examples = {"tp": [], "fp": [], "tn": [], "fn": []}
    for row in rows:
        pair = _pair_key(row.get("config1_id"), row.get("config2_id"))
        actual = _bool_label(row.get("dep_label"))
        predicted = pair in predicted_pairs
        bucket = "tp" if actual and predicted else "fn" if actual else "fp" if predicted else "tn"
        if bucket == "tp":
            tp += 1
        elif bucket == "fp":
            fp += 1
        elif bucket == "tn":
            tn += 1
        else:
            fn += 1
        if len(examples[bucket]) < 20:
            examples[bucket].append(
                {
                    "prompt_id": row.get("prompt_id"),
                    "project": row.get("project"),
                    "version": row.get("version"),
                    "config1": pair[0],
                    "config2": pair[1],
                    "dep_type": row.get("dep_type"),
                }
            )
    return {**_classification_metrics(tp, fp, tn, fn), "sample_examples": examples}


def _tag_candidates(repo: str, version: str) -> list[str]:
    if repo == "apache/hadoop":
        return [f"rel/release-{version}", f"release-{version}", f"rel/{version}", version]
    if repo == "apache/hbase":
        return [f"rel/{version}", f"rel/release-{version}", f"release-{version}", version]
    return [version]


def _run(command: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
    return completed.stdout.strip()


def _clone_version(repo: str, version: str, destination: Path) -> dict:
    url = f"https://github.com/{repo}.git"
    errors: list[str] = []
    for tag in _tag_candidates(repo, version):
        shutil.rmtree(destination, ignore_errors=True)
        command = ["git", "clone", "--depth", "1", "--filter=blob:none", "--branch", tag, url, str(destination)]
        try:
            _run(command)
            revision = _run(["git", "rev-parse", "HEAD"], cwd=destination)
            return {"repo": repo, "version": version, "tag": tag, "revision": revision}
        except subprocess.CalledProcessError as exc:
            errors.append(f"{tag}: {exc.stderr.strip()[-300:]}")
    raise RuntimeError(f"could not clone {repo} version {version}; attempts: {' | '.join(errors)}")


def _scan_project(source_root: Path, project: str) -> tuple[object, Path]:
    spec = PROJECT_SPECS[project]
    target = source_root / spec["scope"] if spec["scope"] != "." else source_root
    if not target.exists():
        raise FileNotFoundError(f"ConfRCA project scope does not exist: {target}")
    return scan(target, use_cache=False), target


def _project_versions(registry_rows: list[dict[str, str]], selected: set[str]) -> dict[str, str]:
    versions: dict[str, set[str]] = {}
    for row in registry_rows:
        project = _canonical(row.get("project"))
        version = _canonical(row.get("version"))
        if project in selected:
            versions.setdefault(project, set()).add(version)
    result: dict[str, str] = {}
    for project in selected:
        found = sorted(v for v in versions.get(project, set()) if v)
        if len(found) != 1:
            raise ValueError(f"expected exactly one ConfRCA version for {project}; found {found}")
        result[project] = found[0]
    return result


def _markdown(output: dict) -> str:
    pair = output["pairwise_dependency_signal"]["aggregate"]
    registry = output["configuration_registry"]["aggregate"]
    lines = [
        "# ConfigReach × ConfRCA external benchmark",
        "",
        "This benchmark uses the independently published ConfRCA dataset. It intentionally reports two different evaluations.",
        "",
        "## Configuration registry discovery",
        "",
        f"- Ground-truth registry options: **{registry['ground_truth']}**",
        f"- True positives: **{registry['tp']}**",
        f"- False negatives: **{registry['fn']}**",
        f"- Registry recall: **{registry['recall'] * 100:.2f}%**" if registry["recall"] is not None else "- Registry recall: n/a",
        f"- Out-of-registry detections: **{registry['out_of_registry']}**",
        "",
        "Out-of-registry detections are deliberately **not called false positives** without independent adjudication. ConfRCA's registry can be used as external positive ground truth for recall, but absence from that registry does not prove a ConfigReach detection is invalid.",
        "",
        "## Human-labelled dependency-pair transfer evaluation",
        "",
        "For each ConfRCA-labelled pair, ConfigReach predicts `dependent` when both keys occur in at least one ConfigReach dependency scope. This evaluates the existing scope-co-occurrence signal; ConfigReach is not presented as a dedicated causal-dependency classifier.",
        "",
        f"- Pairs evaluated: **{pair['tp'] + pair['fp'] + pair['tn'] + pair['fn']}**",
        f"- TP: **{pair['tp']}**",
        f"- FP: **{pair['fp']}**",
        f"- TN: **{pair['tn']}**",
        f"- FN: **{pair['fn']}**",
        f"- Precision: **{pair['precision'] * 100:.2f}%**" if pair["precision"] is not None else "- Precision: n/a",
        f"- Recall: **{pair['recall'] * 100:.2f}%**" if pair["recall"] is not None else "- Recall: n/a",
        f"- F1: **{pair['f1'] * 100:.2f}%**" if pair["f1"] is not None else "- F1: n/a",
        "",
        "## Per-project results",
        "",
        "| Project | Version | Registry TP | Registry FN | Recall | Extra | Pair TP | FP | TN | FN | Pair F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for project in output["projects"]:
        r = project["registry"]
        p = project["pairwise"]
        lines.append(
            f"| {project['project']} | {project['version']} | {r['tp']} | {r['fn']} | "
            f"{(r['recall'] or 0) * 100:.2f}% | {r['out_of_registry']} | {p['tp']} | {p['fp']} | "
            f"{p['tn']} | {p['fn']} | {(p['f1'] or 0) * 100:.2f}% |"
        )
    lines += [
        "",
        "## Claim boundaries",
        "",
        "1. `config_version` is treated as external positive ground truth for listed configuration options. It is not assumed to be exhaustive enough to label every ConfigReach-only detection as a false positive.",
        "2. The dependency-pair metrics use ConfRCA's human True/False labels, but the ConfigReach predictor is only shared-scope co-occurrence. These numbers must not be reported as general ConfigReach scanner precision/recall.",
        "3. Target repositories are statically scanned; their application code is not executed and their dependencies are not installed.",
        "4. Vendored CSVs are derived from ConfRCA under CC-BY-4.0. See `validation/confrca/data/SOURCE.json`.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python -m pip install -e . pyarrow",
        "python validation/confrca/run_confrca_benchmark.py --refresh-dataset",
        "```",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ConfigReach against the external ConfRCA dataset")
    parser.add_argument("--data-dir", type=Path, default=Path("validation/confrca/data"))
    parser.add_argument("--results-json", type=Path, default=Path("validation/results/confrca.json"))
    parser.add_argument("--results-markdown", type=Path, default=Path("validation/results/confrca.md"))
    parser.add_argument("--refresh-dataset", action="store_true")
    parser.add_argument("--project", action="append", choices=sorted(PROJECT_SPECS), default=[])
    args = parser.parse_args()

    if args.refresh_dataset:
        source = refresh_dataset(args.data_dir)
    else:
        required = [args.data_dir / "config_version.csv", args.data_dir / "confrca_labels.csv", args.data_dir / "SOURCE.json"]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError("vendored ConfRCA data missing; run with --refresh-dataset: " + ", ".join(missing))
        source = json.loads((args.data_dir / "SOURCE.json").read_text(encoding="utf-8"))

    registry_rows = _read_csv(args.data_dir / "config_version.csv")
    label_rows = _read_csv(args.data_dir / "confrca_labels.csv")
    selected = set(args.project or PROJECT_SPECS)
    versions = _project_versions(registry_rows, selected)

    projects: list[dict] = []
    clone_evidence: dict[tuple[str, str], dict] = {}

    with tempfile.TemporaryDirectory(prefix="configreach-confrca-sources-") as tmp:
        workspace = Path(tmp)
        roots: dict[tuple[str, str], Path] = {}
        for project in sorted(selected):
            spec = PROJECT_SPECS[project]
            repo, version = spec["repo"], versions[project]
            key = (repo, version)
            if key not in roots:
                destination = workspace / repo.replace("/", "__") / version
                destination.parent.mkdir(parents=True, exist_ok=True)
                clone_evidence[key] = _clone_version(repo, version, destination)
                roots[key] = destination
            report, scanned_path = _scan_project(roots[key], project)

            gt = {
                _canonical(row["name"])
                for row in registry_rows
                if _canonical(row.get("project")) == project and _canonical(row.get("version")) == version and _canonical(row.get("name"))
            }
            detected = {_canonical(item.name) for item in report.effective_keys if _canonical(item.name)}
            registry_result = classify_registry(gt, detected)

            pair_rows = [
                row
                for row in label_rows
                if _canonical(row.get("project")) == project and _canonical(row.get("version")) == version
            ]
            predicted_pairs = {_pair_key(a, b) for a, b in report.pairwise_pairs}
            pair_result = classify_pairs(pair_rows, predicted_pairs)

            projects.append(
                {
                    "project": project,
                    "version": version,
                    "source": clone_evidence[key],
                    "scan_scope": str(scanned_path.relative_to(roots[key])) if scanned_path != roots[key] else ".",
                    "configreach_keys": len(detected),
                    "configreach_pairwise_pairs": len(predicted_pairs),
                    "registry": registry_result,
                    "pairwise": pair_result,
                }
            )

    registry_aggregate = {
        "ground_truth": sum(item["registry"]["ground_truth"] for item in projects),
        "detected": sum(item["registry"]["detected"] for item in projects),
        "tp": sum(item["registry"]["tp"] for item in projects),
        "fn": sum(item["registry"]["fn"] for item in projects),
        "out_of_registry": sum(item["registry"]["out_of_registry"] for item in projects),
    }
    registry_aggregate["recall"] = _safe_div(registry_aggregate["tp"], registry_aggregate["ground_truth"])

    pair_tp = sum(item["pairwise"]["tp"] for item in projects)
    pair_fp = sum(item["pairwise"]["fp"] for item in projects)
    pair_tn = sum(item["pairwise"]["tn"] for item in projects)
    pair_fn = sum(item["pairwise"]["fn"] for item in projects)
    pair_aggregate = _classification_metrics(pair_tp, pair_fp, pair_tn, pair_fn)

    output = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "dataset": source,
        "tool": {"name": "ConfigReach", "version": __version__},
        "methodology": {
            "target_code_executed": False,
            "target_dependencies_installed": False,
            "registry_extra_detections_counted_as_false_positive": False,
            "pair_prediction_rule": "two keys share at least one ConfigReach dependency scope",
            "pair_labels": "ConfRCA human dep_label True/False",
        },
        "configuration_registry": {"aggregate": registry_aggregate},
        "pairwise_dependency_signal": {"aggregate": pair_aggregate},
        "projects": projects,
    }

    args.results_json.parent.mkdir(parents=True, exist_ok=True)
    args.results_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.results_json.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.results_markdown.write_text(_markdown(output), encoding="utf-8")
    print(json.dumps({"registry": registry_aggregate, "pairwise": pair_aggregate}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
