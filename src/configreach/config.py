from __future__ import annotations

import fnmatch
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_IGNORES = [
    ".git/**", ".hg/**", ".svn/**", ".venv/**", "venv/**", "node_modules/**",
    "dist/**", "build/**", ".tox/**", ".pytest_cache/**", "__pycache__/**",
    ".configreach/**",
]


@dataclass
class Settings:
    ignores: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORES))
    test_patterns: list[str] = field(default_factory=lambda: [
        "tests/**", "test/**", "**/test_*.py", "**/*_test.py", "**/*.test.js",
        "**/*.test.ts", "**/*.spec.js", "**/*.spec.ts", "**/*_test.go", "**/*Test.java",
        "**/*Tests.cs", "**/*.Tests.cs", "**/spec/**", "**/__tests__/**",
    ])
    fail_under: float | None = None
    fail_on: set[str] = field(default_factory=set)
    baseline: str = ".configreach/baseline.json"
    trace_file: str = ".configreach/trace.jsonl"
    cache: bool = True
    plugins: bool = True
    max_file_size: int = 2_000_000

    def ignored(self, rel: str) -> bool:
        rel = rel.replace("\\", "/")
        return any(fnmatch.fnmatch(rel, pattern) for pattern in self.ignores)

    def is_test(self, rel: str) -> bool:
        rel = rel.replace("\\", "/")
        parts = rel.split("/")
        if "tests" in parts or "test" in parts or "__tests__" in parts or "spec" in parts:
            return True
        name = parts[-1] if parts else rel
        conventional = (
            (name.startswith("test_") and name.endswith(".py")),
            name.endswith("_test.py"),
            name.endswith("_test.go"),
            name.endswith("Test.java"),
            name.endswith("Tests.cs"),
            name.endswith(".test.js"), name.endswith(".test.ts"),
            name.endswith(".spec.js"), name.endswith(".spec.ts"),
        )
        if any(conventional):
            return True
        return any(fnmatch.fnmatch(rel, pattern) for pattern in self.test_patterns)


def _safe_repository_path(root: Path, configured: str) -> bool:
    """Return whether a repository-controlled path remains under *root*."""
    path = Path(configured)
    if path.is_absolute():
        return False
    try:
        (root / path).resolve().relative_to(root.resolve())
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def load_settings(root: Path) -> Settings:
    settings = Settings()
    path = root / "configreach.toml"
    if not path.exists():
        return settings
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return settings
    section = data.get("configreach", data)
    if isinstance(section.get("ignore"), list):
        settings.ignores.extend(str(x) for x in section["ignore"])
    if isinstance(section.get("test_patterns"), list):
        settings.test_patterns = [str(x) for x in section["test_patterns"]]
    if section.get("fail_under") is not None:
        try:
            settings.fail_under = float(section["fail_under"])
        except (TypeError, ValueError):
            pass
    if isinstance(section.get("fail_on"), list):
        settings.fail_on = {str(x).lower() for x in section["fail_on"]}
    if isinstance(section.get("baseline"), str) and _safe_repository_path(root, section["baseline"]):
        settings.baseline = section["baseline"]
    if isinstance(section.get("trace_file"), str) and _safe_repository_path(root, section["trace_file"]):
        settings.trace_file = section["trace_file"]
    if isinstance(section.get("cache"), bool):
        settings.cache = section["cache"]
    if isinstance(section.get("plugins"), bool):
        settings.plugins = section["plugins"]
    if isinstance(section.get("max_file_size"), int) and section["max_file_size"] > 0:
        settings.max_file_size = section["max_file_size"]
    return settings
