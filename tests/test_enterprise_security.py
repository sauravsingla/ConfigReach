from __future__ import annotations

import ast
from pathlib import Path

import pytest

from configreach.engine import scan
from configreach.workspace import detect_workspaces


NETWORK_MODULE_PREFIXES = (
    "aiohttp",
    "http.client",
    "httpx",
    "requests",
    "socket",
    "urllib.request",
)


def _symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:  # pragma: no cover - platform policy
        pytest.skip(f"symlinks unavailable: {exc}")


def test_scan_never_reads_repository_file_symlinks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "safe.py").write_text("import os\nMODE = os.getenv('MODE', 'safe')\n", encoding="utf-8")

    outside_python = tmp_path / "outside.py"
    outside_python.write_text("import os\nKEY = 'OUTSIDE_PY'\nos.getenv(KEY)\n", encoding="utf-8")
    outside_typescript = tmp_path / "outside.ts"
    outside_typescript.write_text("console.log(process.env.OUTSIDE_TS)\n", encoding="utf-8")
    _symlink_or_skip(repository / "linked.py", outside_python)
    _symlink_or_skip(repository / "linked.ts", outside_typescript)

    original_read_text = Path.read_text

    def guarded_read_text(path: Path, *args, **kwargs):
        if path.is_symlink():
            raise AssertionError(f"ConfigReach attempted to read a repository-controlled symlink: {path}")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    report = scan(repository, use_cache=False)

    assert "MODE" in report.keys
    assert "OUTSIDE_PY" not in report.keys
    assert "OUTSIDE_TS" not in report.keys


def test_workspace_detection_ignores_symlinked_manifests(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    nested = repository / "nested"
    nested.mkdir(parents=True)
    external_manifest = tmp_path / "package.json"
    external_manifest.write_text('{"name": "outside"}\n', encoding="utf-8")
    _symlink_or_skip(nested / "package.json", external_manifest)

    assert detect_workspaces(repository) == [repository.resolve()]


def test_core_has_no_network_client_imports() -> None:
    source_root = Path(__file__).parents[1] / "src" / "configreach"
    violations: list[str] = []
    for path in sorted(source_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                if any(name == prefix or name.startswith(prefix + ".") for prefix in NETWORK_MODULE_PREFIXES):
                    violations.append(f"{path.name}:{getattr(node, 'lineno', 1)} imports {name}")
    assert not violations, "core network imports are not allowed: " + "; ".join(violations)


def test_core_never_uses_shell_true_or_os_system() -> None:
    source_root = Path(__file__).parents[1] / "src" / "configreach"
    violations: list[str] = []
    for path in sorted(source_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "os" and node.func.attr == "system":
                    violations.append(f"{path.name}:{getattr(node, 'lineno', 1)} uses os.system")
                if node.func.value.id == "subprocess":
                    for keyword in node.keywords:
                        if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                            violations.append(
                                f"{path.name}:{getattr(node, 'lineno', 1)} uses subprocess with shell=True"
                            )
    assert not violations, "shell execution is not allowed in the core: " + "; ".join(violations)
