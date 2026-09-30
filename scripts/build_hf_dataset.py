#!/usr/bin/env python3
"""Build the public Hugging Face validation dataset from committed evidence.

The generated payload contains only ConfigReach-derived measurements and
provenance metadata. It never copies source files from scanned repositories.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.8-3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_PATH = ROOT / "validation/results/external-holdout-full.json"
ACCURACY_PATH = ROOT / "validation/results/accuracy.json"
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


def build(output_dir: Path) -> None:
    holdout = load_json(HOLDOUT_PATH)
    accuracy = load_json(ACCURACY_PATH)
    project = tomllib.loads(PROJECT_PATH.read_text(encoding="utf-8"))

    source_version = project["project"]["version"]
    holdout_tool = holdout.get("tool", {})
    accuracy_tool = accuracy.get("tool", {})
    validation_version = holdout_tool.get("version")

    require(bool(validation_version), "external holdout tool version is missing")
    require(
        accuracy_tool.get("version") == validation_version,
        "accuracy tool version does not match external holdout tool version",
    )

    projects = holdout["projects"]
    summary = holdout["summary"]
    execution = holdout["execution"]
    methodology = holdout["methodology"]
    selection = holdout.get("selection", {})
    ecosystem_summary = holdout["ecosystem_summary"]

    require(projects, "external holdout has no project rows")
    require(execution.get("all_jobs_succeeded") is True, "external holdout contains a failed job")
    require(methodology.get("pinned_commits") is True, "external holdout is not pinned to commits")
    require(methodology.get("baseline_disjoint") is True, "external holdout is not baseline-disjoint")
    require(selection.get("baseline_overlap_count", 0) == 0, "external holdout overlaps the baseline")

    total_inputs = sum(int(item["configuration_inputs"]) for item in projects)
    covered_inputs = sum(int(item["covered_inputs"]) for item in projects)
    uncovered_inputs = sum(int(item["uncovered_inputs"]) for item in projects)
    runtime_seconds = sum(float(item["runtime_seconds"]) for item in projects)

    require(total_inputs == covered_inputs + uncovered_inputs, "holdout totals are inconsistent")
    require(summary["configuration_inputs"] == total_inputs, "summary configuration_inputs is stale")
    require(summary["covered_inputs"] == covered_inputs, "summary covered_inputs is stale")
    require(summary["projects_scanned"] == len(projects), "summary projects_scanned is stale")
    require(summary["projects_requested"] == len(projects), "summary projects_requested is stale")
    require(
        math.isclose(float(summary["runtime_seconds"]), runtime_seconds, rel_tol=0.0, abs_tol=1e-6),
        "summary runtime_seconds is stale",
    )

    source_revision = (
        execution.get("source_revision")
        or holdout_tool.get("source_revision")
        or accuracy_tool.get("source_revision")
    )
    require(bool(source_revision), "validation source revision is missing")

    aggregate = accuracy["aggregate"]
    require(int(aggregate["true_positives"]) > 0, "accuracy corpus has no true positives")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "data").mkdir(parents=True)
    (output_dir / "metadata").mkdir(parents=True)

    rows: list[dict[str, Any]] = []
    for item in projects:
        require(bool(item.get("repo")), "project row is missing repo")
        require(bool(item.get("commit")), f"{item.get('repo', '<unknown>')} is missing a pinned commit")
        require(bool(item.get("source_url")), f"{item['repo']} is missing source_url")
        require(
            int(item["configuration_inputs"])
            == int(item["covered_inputs"]) + int(item["uncovered_inputs"]),
            f"{item['repo']} has inconsistent coverage counts",
        )

        rows.append(
            {
                "repo": item["repo"],
                "commit": item["commit"],
                "ecosystem": item["ecosystem"],
                "configuration_inputs": item["configuration_inputs"],
                "covered_inputs": item["covered_inputs"],
                "uncovered_inputs": item["uncovered_inputs"],
                "configuration_coverage": item["configuration_coverage"],
                "files_scanned": item["files_scanned"],
                "tests_scanned": item["tests_scanned"],
                "runtime_seconds": item["runtime_seconds"],
                "source_url": item["source_url"],
                "warnings": item.get("warnings", []),
                "configreach_version": validation_version,
                "captured_at": holdout["captured_at"],
                "validation_source_revision": source_revision,
            }
        )

    data_path = output_dir / "data/external_holdout.jsonl"
    with data_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    write_json(output_dir / "metadata/accuracy.json", accuracy)
    write_json(output_dir / "metadata/ecosystem_summary.json", ecosystem_summary)
    write_json(
        output_dir / "metadata/methodology.json",
        {
            "methodology": methodology,
            "selection": selection,
            "execution": execution,
        },
    )
    write_json(
        output_dir / "metadata/summary.json",
        {
            "captured_at": holdout["captured_at"],
            "configreach_version": validation_version,
            "current_source_version": source_version,
            "source_revision": source_revision,
            "projects": len(projects),
            "ecosystems": len({item["ecosystem"] for item in projects}),
            "configuration_inputs": total_inputs,
            "covered_inputs": covered_inputs,
            "uncovered_inputs": uncovered_inputs,
            "configuration_coverage": covered_inputs / total_inputs if total_inputs else 1.0,
            "runtime_seconds": runtime_seconds,
            "accuracy": aggregate,
        },
    )
    write_json(output_dir / "metadata/external-holdout-full.json", holdout)
    (output_dir / "VERSION").write_text(str(validation_version) + "\n", encoding="utf-8")

    coverage_pct = covered_inputs / total_inputs * 100 if total_inputs else 100.0
    replacements = {
        "{{VERSION}}": str(validation_version),
        "{{CAPTURED_AT}}": str(holdout["captured_at"]),
        "{{PROJECTS}}": f"{len(projects):,}",
        "{{ECOSYSTEMS}}": f"{len({item['ecosystem'] for item in projects}):,}",
        "{{INPUTS}}": f"{total_inputs:,}",
        "{{COVERED}}": f"{covered_inputs:,}",
        "{{COVERAGE_PCT}}": f"{coverage_pct:.2f}%",
        "{{RUNTIME_SECONDS}}": f"{runtime_seconds:,.1f}",
        "{{SCANNER_HOURS}}": f"{runtime_seconds / 3600:.2f}",
        "{{SOURCE_REVISION}}": str(source_revision),
        "{{TP}}": f"{int(aggregate['true_positives']):,}",
        "{{FP}}": f"{int(aggregate['false_positives']):,}",
        "{{FN}}": f"{int(aggregate['false_negatives']):,}",
        "{{PRECISION}}": f"{float(aggregate['micro_precision']) * 100:.1f}%",
        "{{RECALL}}": f"{float(aggregate['micro_recall']) * 100:.1f}%",
        "{{F1}}": f"{float(aggregate['micro_f1']) * 100:.1f}%",
    }

    card = CARD_TEMPLATE_PATH.read_text(encoding="utf-8")
    for token, value in replacements.items():
        card = card.replace(token, value)

    unresolved = sorted(token for token in replacements if token in card)
    require(not unresolved, "dataset card has unresolved placeholders: " + ", ".join(unresolved))
    (output_dir / "README.md").write_text(card, encoding="utf-8")

    print(
        "Built Hugging Face dataset: "
        f"{len(rows)} rows, {len({item['ecosystem'] for item in projects})} ecosystems, "
        f"{total_inputs:,} inputs, {covered_inputs:,} covered, {coverage_pct:.2f}% coverage; "
        f"validation version {validation_version}, current source version {source_version}"
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
