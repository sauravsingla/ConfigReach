from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from configreach.engine import scan

HERE = Path(__file__).resolve().parent
DEFAULT_DATASET = HERE / "data" / "configreach_50k_scenarios.jsonl"
DEFAULT_RESULT = HERE.parent / "results" / "curated_50k.json"
DEFAULT_MARKDOWN = HERE.parent / "results" / "curated_50k.md"
DEFAULT_PREDICTIONS = HERE.parent / "results" / "curated_50k_predictions.csv"


def metrics(tp: int, fp: int, tn: int, fn: int) -> dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if tp + fp + tn + fn else 1.0
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}


def load_rows(path: Path) -> list[dict[str, object]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [str(row["scenario_id"]) for row in rows]
    keys = [str(row["expected_key"]) for row in rows]
    if len(rows) != 50_000 or len(set(ids)) != 50_000 or len(set(keys)) != 50_000:
        raise SystemExit("dataset integrity failure: expected 50,000 rows with unique scenario IDs and expected keys")
    positives = sum(bool(row["expected_detect"]) for row in rows)
    if positives != 25_000:
        raise SystemExit(f"dataset integrity failure: expected 25,000 positives, found {positives}")
    return rows


def materialize(rows: list[dict[str, object]], root: Path) -> None:
    for row in rows:
        case_dir = root / str(row["scenario_id"])
        target = case_dir / str(row["suggested_filename"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(row["snippet"]), encoding="utf-8")


def classify(rows: list[dict[str, object]], detected: set[str]) -> tuple[list[dict[str, object]], dict[str, object]]:
    counts = Counter()
    group_counts: dict[str, Counter[str]] = defaultdict(Counter)
    variant_counts: dict[str, Counter[str]] = defaultdict(Counter)
    predictions: list[dict[str, object]] = []
    for row in rows:
        expected = bool(row["expected_detect"])
        key = str(row["expected_key"])
        actual = key in detected
        cls = "tp" if expected and actual else "fn" if expected else "fp" if actual else "tn"
        counts[cls] += 1
        group = str(row["group"])
        variant = f"{group}::{row['variant']}"
        group_counts[group][cls] += 1
        variant_counts[variant][cls] += 1
        predictions.append({
            "scenario_id": row["scenario_id"],
            "group": group,
            "variant": row["variant"],
            "expected_key": key,
            "expected_detect": expected,
            "actual_detect": actual,
            "classification": cls.upper(),
        })

    overall = metrics(counts["tp"], counts["fp"], counts["tn"], counts["fn"])
    by_group = {name: metrics(c["tp"], c["fp"], c["tn"], c["fn"]) for name, c in sorted(group_counts.items())}
    by_variant = {name: metrics(c["tp"], c["fp"], c["tn"], c["fn"]) for name, c in sorted(variant_counts.items())}
    return predictions, {"scenario_count": len(rows), "overall": overall, "by_group": by_group, "by_variant": by_variant}


def write_markdown(result: dict[str, object], path: Path) -> None:
    overall = result["overall"]
    assert isinstance(overall, dict)
    lines = [
        "# ConfigReach Curated 50K Benchmark",
        "",
        "This result is measured by `configreach.engine.scan()` against the committed 50,000-case controlled curated benchmark.",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Scenarios | {result['scenario_count']:,} |",
        f"| TP | {overall['tp']:,} |",
        f"| FP | {overall['fp']:,} |",
        f"| TN | {overall['tn']:,} |",
        f"| FN | {overall['fn']:,} |",
        f"| Precision | {overall['precision']:.4%} |",
        f"| Recall | {overall['recall']:.4%} |",
        f"| F1 | {overall['f1']:.4%} |",
        f"| Accuracy | {overall['accuracy']:.4%} |",
        "",
        "> Scope: controlled curated benchmark. This is not a claim of universal real-world accuracy and is separate from independently labelled external validation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--keep-corpus", type=Path)
    args = parser.parse_args()

    rows = load_rows(args.dataset)
    temp = Path(tempfile.mkdtemp(prefix="configreach-curated-50k-"))
    try:
        materialize(rows, temp)
        report = scan(temp, use_cache=False)
        predictions, result = classify(rows, set(report.keys))
        result["scanner"] = {
            "entry_point": "configreach.engine.scan",
            "semantic_engine": report.to_dict()["summary"].get("semantic_engine"),
        }
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(result, args.markdown)
        with args.predictions.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["scenario_id", "group", "variant", "expected_key", "expected_detect", "actual_detect", "classification"])
            writer.writeheader()
            writer.writerows(predictions)
        print(json.dumps(result["overall"], indent=2, sort_keys=True))
    finally:
        if args.keep_corpus:
            if args.keep_corpus.exists():
                shutil.rmtree(args.keep_corpus)
            shutil.move(str(temp), str(args.keep_corpus))
        else:
            shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    main()
