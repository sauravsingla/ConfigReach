#!/usr/bin/env python3
"""Build the public Hugging Face dataset from the committed curated 50K evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "validation/curated_50k/data/configreach_50k_scenarios.jsonl"
MANIFEST_PATH = ROOT / "validation/curated_50k/manifest.json"
RESULT_PATH = ROOT / "validation/results/curated_50k.json"
PREDICTIONS_PATH = ROOT / "validation/results/curated_50k_predictions.csv"
PROJECT_PATH = ROOT / "pyproject.toml"
CARD_TEMPLATE_PATH = ROOT / "huggingface-dataset/README.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def pct(value: float) -> str:
    return f"{value * 100:.4f}%"


def build(output_dir: Path) -> None:
    manifest = load_json(MANIFEST_PATH)
    result = load_json(RESULT_PATH)
    project = tomllib.loads(PROJECT_PATH.read_text(encoding="utf-8"))

    require(DATA_PATH.is_file(), "curated 50K JSONL is missing")
    require(PREDICTIONS_PATH.is_file(), "curated 50K row-level predictions are missing")

    raw = DATA_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(len(raw) == int(manifest["jsonl_bytes"]), "curated 50K byte size does not match manifest")
    require(digest == manifest["jsonl_sha256"], "curated 50K SHA-256 does not match manifest")

    scenario_ids: set[str] = set()
    expected_keys: set[str] = set()
    groups: Counter[str] = Counter()
    positive = 0
    negative = 0
    rows = 0

    for line_number, line in enumerate(DATA_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid JSONL row {line_number}: {exc}") from exc
        rows += 1
        scenario_ids.add(str(row["scenario_id"]))
        expected_keys.add(str(row["expected_key"]))
        groups[str(row["group"])] += 1
        if row["expected_detect"] is True:
            positive += 1
        elif row["expected_detect"] is False:
            negative += 1
        else:
            raise SystemExit(f"row {line_number} has non-boolean expected_detect")

    require(rows == int(manifest["scenario_count"]) == 50000, "scenario count is not exactly 50,000")
    require(positive == int(manifest["expected_positive"]) == 25000, "positive count is not exactly 25,000")
    require(negative == int(manifest["expected_negative"]) == 25000, "negative count is not exactly 25,000")
    require(len(scenario_ids) == int(manifest["unique_scenario_ids"]) == 50000, "scenario IDs are not unique")
    require(len(expected_keys) == int(manifest["unique_expected_keys"]) == 50000, "expected keys are not unique")
    require(dict(sorted(groups.items())) == manifest["group_counts"], "per-group counts do not match manifest")

    require(int(result["scenario_count"]) == rows, "result scenario_count does not match dataset")
    overall = result["overall"]
    require(int(overall["tp"]) + int(overall["fn"]) == positive, "positive confusion-matrix total is inconsistent")
    require(int(overall["tn"]) + int(overall["fp"]) == negative, "negative confusion-matrix total is inconsistent")
    require(int(overall["tp"]) == 25000, "expected TP=25,000")
    require(int(overall["fp"]) == 0, "expected FP=0")
    require(int(overall["tn"]) == 25000, "expected TN=25,000")
    require(int(overall["fn"]) == 0, "expected FN=0")

    scanner = result["scanner"]
    require(scanner.get("entry_point") == "configreach.engine.scan", "unexpected benchmark scanner entry point")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "data").mkdir(parents=True)
    (output_dir / "metadata").mkdir(parents=True)
    (output_dir / "evidence").mkdir(parents=True)

    shutil.copy2(DATA_PATH, output_dir / "data/configreach_50k_scenarios.jsonl")
    shutil.copy2(PREDICTIONS_PATH, output_dir / "evidence/configreach_50k_predictions.csv")
    shutil.copy2(MANIFEST_PATH, output_dir / "metadata/manifest.json")
    shutil.copy2(RESULT_PATH, output_dir / "metadata/results.json")

    source_version = str(project["project"]["version"])
    summary = {
        "source_version": source_version,
        "scenario_count": rows,
        "expected_positive": positive,
        "expected_negative": negative,
        "groups": len(groups),
        "dataset_sha256": digest,
        "scanner": scanner,
        "overall": overall,
    }
    write_json(output_dir / "metadata/summary.json", summary)
    (output_dir / "VERSION").write_text(source_version + "\n", encoding="utf-8")

    replacements = {
        "{{SOURCE_VERSION}}": source_version,
        "{{SCENARIOS}}": f"{rows:,}",
        "{{POSITIVE}}": f"{positive:,}",
        "{{NEGATIVE}}": f"{negative:,}",
        "{{GROUPS}}": f"{len(groups):,}",
        "{{TP}}": f"{int(overall['tp']):,}",
        "{{FP}}": f"{int(overall['fp']):,}",
        "{{TN}}": f"{int(overall['tn']):,}",
        "{{FN}}": f"{int(overall['fn']):,}",
        "{{PRECISION}}": pct(float(overall["precision"])),
        "{{RECALL}}": pct(float(overall["recall"])),
        "{{F1}}": pct(float(overall["f1"])),
        "{{ACCURACY}}": pct(float(overall["accuracy"])),
        "{{DATA_SHA256}}": digest,
        "{{SCANNER_ENTRY_POINT}}": str(scanner["entry_point"]),
        "{{SEMANTIC_ENGINE}}": str(scanner["semantic_engine"]),
    }

    card = CARD_TEMPLATE_PATH.read_text(encoding="utf-8")
    for token, value in replacements.items():
        card = card.replace(token, value)
    unresolved = sorted(token for token in replacements if token in card)
    require(not unresolved, "dataset card has unresolved placeholders: " + ", ".join(unresolved))
    require("{{" not in card and "}}" not in card, "dataset card contains an unknown placeholder")
    (output_dir / "README.md").write_text(card, encoding="utf-8")

    print(
        "Built Hugging Face curated 50K dataset: "
        f"{rows:,} rows, {positive:,} positive, {negative:,} negative, "
        f"{len(groups)} groups, SHA-256 {digest}; "
        f"TP={overall['tp']} FP={overall['fp']} TN={overall['tn']} FN={overall['fn']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / ".hf-dataset",
        help="Directory to create (default: .hf-dataset)",
    )
    args = parser.parse_args()
    build(args.output.resolve())


if __name__ == "__main__":
    main()
