from __future__ import annotations

import json
import time
from dataclasses import fields
from pathlib import Path

from .baseline import apply_baseline, baseline_path
from .config import Settings, load_settings
from .discover import scan as core_scan
from .hardening import apply_hardening
from .lexical_hardening import apply_lexical_hardening
from .models import ConfigKey, Location, ScanReport
from .schemas import REPORT_SCHEMA_VERSION
from .semantic_adapters import (
    record_dotnet,
    record_go,
    record_java_frameworks,
    record_javascript_typescript,
    record_json_schema,
    record_terraform_domains,
)
from .validator_adapters import (
    record_extended_json_schema,
    record_java_bean_validation,
    record_terraform_validators,
    record_zod,
)

SEMANTIC_EXTENSIONS = {
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".java", ".kt", ".cs", ".json", ".tf",
}


class SemanticScanReport(ScanReport):
    """ScanReport with scoped deterministic semantics and line-range attribution."""

    @staticmethod
    def _dependency_scope(loc: Location) -> str:
        for language in ("python", "javascript", "go"):
            prefix = f"{language}:"
            if loc.detail.startswith(prefix) and loc.detail != f"{language}:module":
                return f"{loc.path}::{loc.detail.split(':', 1)[1]}"
        return loc.path

    def keys_for_line_ranges(self, ranges: dict[str, list[tuple[int, int]]]) -> list[ConfigKey]:
        out: list[ConfigKey] = []
        for item in self.keys.values():
            locations = item.reads + item.declarations + item.branches
            if any(
                start <= loc.line <= end
                for loc in locations
                for start, end in ranges.get(loc.path, [])
            ):
                out.append(item)
        return sorted(out, key=lambda x: x.name)

    def to_dict(self):
        data = super().to_dict()
        data["schema_version"] = REPORT_SCHEMA_VERSION
        data["summary"]["semantic_engine"] = "v0.9"
        return data


def _upgrade(report: ScanReport) -> SemanticScanReport:
    values = {field.name: getattr(report, field.name) for field in fields(ScanReport)}
    return SemanticScanReport(**values)


def _drop_generic_language_locations(report: ScanReport, rel: str, detail: str) -> None:
    for item in report.keys.values():
        item.reads = [loc for loc in item.reads if not (loc.path == rel and loc.detail == detail)]
        item.test_mentions = [loc for loc in item.test_mentions if not (loc.path == rel and loc.detail == detail)]


def _drop_schema_flattening(report: ScanReport, rel: str) -> None:
    to_delete: list[str] = []
    for name, item in report.keys.items():
        before = len(item.declarations)
        item.declarations = [
            loc for loc in item.declarations
            if not (loc.path == rel and loc.detail == "json")
        ]
        if before != len(item.declarations):
            item.defaults.clear() if not item.declarations and not item.reads else None
        if not (item.reads or item.declarations or item.test_mentions or item.branches or item.runtime_observed):
            to_delete.append(name)
    for name in to_delete:
        report.keys.pop(name, None)


def _add_symlink_ignores(root: Path, settings: Settings) -> None:
    """Prevent later passes from reading repository-controlled file symlinks."""
    known = set(settings.ignores)
    for path in root.rglob("*"):
        if not path.is_symlink():
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if rel not in known:
            settings.ignores.append(rel)
            known.add(rel)


def _semantic_files(root: Path, settings: Settings) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in SEMANTIC_EXTENSIONS:
            continue
        rel = path.relative_to(root).as_posix()
        if settings.ignored(rel):
            continue
        try:
            if path.stat().st_size > settings.max_file_size:
                continue
        except OSError:
            continue
        out.append(path)
    return sorted(out, key=lambda p: p.relative_to(root).as_posix())


def _dotnet_package_roots(root: Path) -> list[str]:
    roots: set[str] = set()
    for path in root.rglob("*.csproj"):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.parent.relative_to(root).as_posix()
        roots.add("." if rel == "." else rel)
    return sorted(roots)


def scan(root: str | Path = ".", settings: Settings | None = None, *, use_cache: bool | None = None) -> SemanticScanReport:
    started = time.perf_counter()
    root_path = Path(root).resolve()
    settings = settings or load_settings(root_path)
    _add_symlink_ignores(root_path, settings)
    base = core_scan(root_path, settings=settings, use_cache=use_cache)
    report = _upgrade(base)

    base_paths: set[str] = set()
    for item in report.keys.values():
        base_paths.update(loc.path for loc in item.reads + item.declarations + item.test_mentions + item.branches)

    for path in _semantic_files(root_path, settings):
        rel = path.relative_to(root_path).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            report.warnings.append(f"Could not read {rel} during semantic pass: {exc}")
            continue
        is_test = settings.is_test(rel)
        suffix = path.suffix.lower()

        if suffix in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}:
            _drop_generic_language_locations(report, rel, "javascript")
            record_javascript_typescript(text, rel, is_test, report.keys)
            record_zod(text, rel, report.keys)
        elif suffix == ".go":
            _drop_generic_language_locations(report, rel, "go")
            record_go(text, rel, is_test, report.keys)
        elif suffix in {".java", ".kt"}:
            record_java_frameworks(text, rel, is_test, report.keys)
            record_java_bean_validation(text, rel, report.keys)
        elif suffix == ".cs":
            record_dotnet(text, rel, is_test, report.keys)
            if rel not in base_paths:
                report.files_scanned += 1
                report.tests_scanned += int(is_test)
        elif suffix == ".json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and isinstance(data.get("properties"), dict):
                _drop_schema_flattening(report, rel)
                record_json_schema(data, rel, report.keys)
                record_extended_json_schema(data, rel, report.keys)
        elif suffix == ".tf":
            record_terraform_domains(text, rel, report.keys)
            record_terraform_validators(text, rel, report.keys)

    apply_hardening(root_path, settings, report)
    apply_lexical_hardening(root_path, settings, report)

    # Re-apply boolean inference after semantic/validator adapters add finite domains/flags.
    for item in report.keys.values():
        lower = {x.lower() for x in item.expected_values | item.defaults}
        if lower & {"true", "false"} or "feature-flag" in item.categories:
            item.expected_values.update({"true", "false"})
        item.baseline_ignored = False

    report.package_roots = sorted(set(report.package_roots) | set(_dotnet_package_roots(root_path)))
    apply_baseline(report, baseline_path(root_path, settings.baseline))
    report.scan_seconds = time.perf_counter() - started
    return report
