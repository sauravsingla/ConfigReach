from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.run_external_holdout import select_projects, validate_manifest


MANIFEST = ROOT / "validation" / "external_holdout_projects.json"
BASELINE = ROOT / "validation" / "real_world_projects.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_holdout_is_frozen_disjoint_and_profiled() -> None:
    manifest = _load(MANIFEST)
    baseline = _load(BASELINE)

    summary = validate_manifest(manifest, baseline)

    assert summary["projects"] == 11
    assert summary["baseline_overlap"] == []
    assert summary["profiles"]["full"] == 11
    assert summary["profiles"]["smoke"] == 4

    smoke = select_projects(manifest, "smoke")
    assert [item["repo"] for item in smoke] == [
        "PrefectHQ/prefect",
        "vitejs/vite",
        "laravel/framework",
        "terraform-aws-modules/terraform-aws-vpc",
    ]


def test_manifest_rejects_baseline_overlap() -> None:
    manifest = _load(MANIFEST)
    baseline = _load(BASELINE)
    broken = copy.deepcopy(manifest)
    broken["projects"][0]["repo"] = baseline["projects"][0]["repo"]
    broken["projects"][0]["source_url"] = f"https://github.com/{baseline['projects'][0]['repo']}"

    with pytest.raises(ValueError, match="overlaps baseline"):
        validate_manifest(broken, baseline)


def test_manifest_rejects_abbreviated_commit_sha() -> None:
    manifest = _load(MANIFEST)
    broken = copy.deepcopy(manifest)
    broken["projects"][0]["commit"] = broken["projects"][0]["commit"][:12]

    with pytest.raises(ValueError, match="40-character Git SHA"):
        validate_manifest(broken)


def test_manifest_requires_every_project_in_full_profile() -> None:
    manifest = _load(MANIFEST)
    broken = copy.deepcopy(manifest)
    broken["projects"][0]["profiles"] = ["smoke"]

    with pytest.raises(ValueError, match="must include full"):
        validate_manifest(broken)


def test_repo_filter_cannot_escape_frozen_corpus() -> None:
    manifest = _load(MANIFEST)

    with pytest.raises(ValueError, match="not in the frozen holdout"):
        select_projects(manifest, "full", ["example/not-in-corpus"])
