from __future__ import annotations

import json
from pathlib import Path

from configreach.capabilities import builtin_capability_document
from configreach.engine import scan
from configreach.fixture_exporters import render_fixture
from configreach.planner import PlanCase, TestPlan as ConfigTestPlan
from configreach.reproducibility import ReproResult, ReproRun
from configreach.schemas import SCHEMAS, schema_registry_document, validate_document


FIXTURES = Path(__file__).parent / "fixtures" / "schemas"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_schema_registry_versions_are_explicit() -> None:
    registry = schema_registry_document()
    assert registry["schema_version"] == 1
    assert registry["schemas"]["report"]["current_version"] == 5
    assert registry["schemas"]["report"]["min_supported_version"] == 3
    assert set(registry["schemas"]) == {
        "report", "workspace", "plan", "reproducibility", "capabilities"
    }


def test_golden_schema_fixtures_are_compatible() -> None:
    fixtures = {
        "report": "report-v5.json",
        "workspace": "workspace-v1.json",
        "plan": "plan-v1.json",
        "reproducibility": "reproducibility-v1.json",
        "capabilities": "capabilities-v1.json",
    }
    for kind, filename in fixtures.items():
        result = validate_document(kind, _load(filename))
        assert result.compatible is True
        assert result.status == "current"
        assert result.schema_version == SCHEMAS[kind].current_version


def test_legacy_report_is_accepted_but_future_report_is_rejected() -> None:
    legacy = validate_document("report", _load("report-v3-legacy.json"))
    assert legacy.compatible is True
    assert legacy.status == "compatible-legacy"
    assert legacy.warnings

    future = _load("report-v5.json")
    future["schema_version"] = SCHEMAS["report"].current_version + 1
    result = validate_document("report", future)
    assert result.compatible is False
    assert result.status == "invalid"
    assert any("newer than supported" in error for error in result.errors)


def test_schema_validation_detects_structural_breakage() -> None:
    broken = _load("workspace-v1.json")
    broken.pop("workspaces")
    result = validate_document("workspace", broken)
    assert result.compatible is False
    assert "missing required field: workspaces" in result.errors


def test_current_scan_matches_registered_report_schema(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        'import os\nMODE = os.getenv("MODE", "sandbox")\n', encoding="utf-8"
    )
    report = scan(tmp_path, use_cache=False)
    data = report.to_dict()
    assert data["summary"]["semantic_engine"] == "v0.9"
    validation = validate_document("report", data)
    assert validation.compatible is True
    assert validation.status == "current"


def _sample_plan() -> ConfigTestPlan:
    return ConfigTestPlan(
        strength=2,
        cases=[
            PlanCase(
                "CRP001",
                "app.py::handle",
                (("PAYMENT_MODE", "live"), ("REGION", "eu")),
                ("PAYMENT_MODE=live & REGION=eu",),
            )
        ],
        missing_values={"PAYMENT_MODE": ["live"]},
        interactions_total=4,
        interactions_already_covered=2,
        interactions_planned=1,
        interactions_remaining=1,
        scopes_considered=1,
        warnings=[],
    )


def test_junit_and_xunit_exporters_are_deterministic_and_assertion_free() -> None:
    plan = _sample_plan()
    junit = render_fixture(plan, "junit")
    xunit = render_fixture(plan, "xunit")

    assert "Stream<Arguments>" in junit
    assert 'Map.entry("PAYMENT_MODE", "live")' in junit
    assert "assert" not in junit.lower()
    assert "IEnumerable<object[]>" in xunit
    assert '["PAYMENT_MODE"] = "live"' in xunit
    assert "Environment.SetEnvironmentVariable" in xunit
    assert "assert" not in xunit.lower()
    assert render_fixture(plan, "junit") == junit
    assert render_fixture(plan, "xunit") == xunit


def test_current_plan_repro_and_capability_documents_match_registry() -> None:
    plan = _sample_plan().to_dict()
    repro = ReproResult([ReproRun(1, "a" * 64), ReproRun(2, "a" * 64)], True).to_dict()
    capabilities = builtin_capability_document()

    assert validate_document("plan", plan).compatible is True
    assert validate_document("reproducibility", repro).compatible is True
    assert validate_document("capabilities", capabilities).compatible is True
