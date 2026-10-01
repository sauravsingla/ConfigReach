from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings, load_settings
from .engine import scan
from .schemas import WORKSPACE_SCHEMA_VERSION


WORKSPACE_MARKERS = {
    "pyproject.toml",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}


@dataclass(frozen=True)
class WorkspaceResult:
    path: str
    files_scanned: int
    tests_scanned: int
    configuration_inputs: int
    covered_inputs: int
    coverage: float
    cache_hit: bool
    findings: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "files_scanned": self.files_scanned,
            "tests_scanned": self.tests_scanned,
            "configuration_inputs": self.configuration_inputs,
            "covered_inputs": self.covered_inputs,
            "coverage": round(self.coverage, 6),
            "cache_hit": self.cache_hit,
            "findings": self.findings,
        }


@dataclass
class WorkspaceReport:
    root: str
    workspaces: list[WorkspaceResult]

    @property
    def total_files(self) -> int:
        return sum(item.files_scanned for item in self.workspaces)

    @property
    def total_tests(self) -> int:
        return sum(item.tests_scanned for item in self.workspaces)

    @property
    def total_inputs(self) -> int:
        return sum(item.configuration_inputs for item in self.workspaces)

    @property
    def total_covered(self) -> int:
        return sum(item.covered_inputs for item in self.workspaces)

    @property
    def coverage(self) -> float:
        return 1.0 if self.total_inputs == 0 else self.total_covered / self.total_inputs

    @property
    def cache_hits(self) -> int:
        return sum(1 for item in self.workspaces if item.cache_hit)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": WORKSPACE_SCHEMA_VERSION,
            "root": self.root,
            "summary": {
                "workspaces": len(self.workspaces),
                "cache_hits": self.cache_hits,
                "files_scanned": self.total_files,
                "tests_scanned": self.total_tests,
                "configuration_inputs": self.total_inputs,
                "covered_inputs": self.total_covered,
                "coverage": round(self.coverage, 6),
            },
            "workspaces": [item.to_dict() for item in self.workspaces],
        }


def _is_marker(path: Path) -> bool:
    return path.name in WORKSPACE_MARKERS or path.suffix.lower() == ".csproj"


def detect_workspaces(root: str | Path) -> list[Path]:
    """Return deterministic package/workspace roots based only on local manifests."""
    root_path = Path(root).resolve()
    roots: set[Path] = set()
    for path in root_path.rglob("*"):
        if path.is_symlink() or not path.is_file() or not _is_marker(path):
            continue
        try:
            rel = path.relative_to(root_path).as_posix()
        except ValueError:
            continue
        if any(part in {".git", ".venv", "venv", "node_modules", "dist", "build", ".configreach"} for part in rel.split("/")):
            continue
        roots.add(path.parent.resolve())
    if not roots:
        roots.add(root_path)
    return sorted(roots, key=lambda path: path.relative_to(root_path).as_posix())


def _child_ignore_patterns(workspace: Path, all_roots: list[Path]) -> list[str]:
    patterns: list[str] = []
    for candidate in all_roots:
        if candidate == workspace:
            continue
        try:
            rel = candidate.relative_to(workspace).as_posix()
        except ValueError:
            continue
        if rel and rel != ".":
            patterns.append(f"{rel}/**")
    return sorted(set(patterns))


def _workspace_settings(workspace: Path, roots: list[Path]) -> Settings:
    settings = load_settings(workspace)
    settings.ignores.extend(_child_ignore_patterns(workspace, roots))
    return settings


def scan_workspaces(root: str | Path = ".", *, use_cache: bool = True) -> WorkspaceReport:
    """Scan manifest-defined workspaces with independent cache boundaries.

    Parent workspaces ignore nested workspaces, preventing double counting. Since each
    workspace invokes the normal ConfigReach engine from its own root, its persistent
    cache lives under that workspace and only that workspace invalidates when files change.
    """
    root_path = Path(root).resolve()
    roots = detect_workspaces(root_path)
    results: list[WorkspaceResult] = []
    for workspace in roots:
        settings = _workspace_settings(workspace, roots)
        report = scan(workspace, settings=settings, use_cache=use_cache)
        rel = workspace.relative_to(root_path).as_posix()
        display = "." if rel == "." else rel
        results.append(
            WorkspaceResult(
                path=display,
                files_scanned=report.files_scanned,
                tests_scanned=report.tests_scanned,
                configuration_inputs=report.effective_total,
                covered_inputs=report.covered,
                coverage=report.coverage,
                cache_hit=report.cache_hit,
                findings=len(report.findings),
            )
        )
    return WorkspaceReport(str(root_path), results)


def render_workspace(report: WorkspaceReport, format_name: str = "text") -> str:
    if format_name == "json":
        return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    if format_name == "markdown":
        lines = [
            "# ConfigReach workspace scan",
            "",
            f"- Workspaces: **{len(report.workspaces)}**",
            f"- Cache hits: **{report.cache_hits}**",
            f"- Configuration coverage: **{report.coverage * 100:.1f}%**",
            "",
            "| Workspace | Coverage | Inputs | Files | Tests | Cache | Findings |",
            "|---|---:|---:|---:|---:|---|---:|",
        ]
        for item in report.workspaces:
            lines.append(
                f"| `{item.path}` | {item.coverage * 100:.1f}% | {item.configuration_inputs} | "
                f"{item.files_scanned} | {item.tests_scanned} | {'hit' if item.cache_hit else 'miss'} | {item.findings} |"
            )
        return "\n".join(lines) + "\n"
    if format_name != "text":
        raise ValueError(f"unsupported workspace format: {format_name}")
    lines = [
        "ConfigReach workspace scan",
        f"Workspaces: {len(report.workspaces)}  Cache hits: {report.cache_hits}",
        f"Configuration coverage: {report.coverage * 100:.1f}%",
        "",
    ]
    for item in report.workspaces:
        lines.append(
            f"{item.path}: {item.coverage * 100:.1f}% ({item.covered_inputs}/{item.configuration_inputs}) "
            f"files={item.files_scanned} tests={item.tests_scanned} cache={'hit' if item.cache_hit else 'miss'}"
        )
    return "\n".join(lines) + "\n"
