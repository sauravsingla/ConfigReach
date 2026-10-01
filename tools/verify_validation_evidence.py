from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
from pathlib import Path
from typing import Any


_RUNTIME_CELL = re.compile(r"\|\s*[0-9]+(?:\.[0-9]+)?s\s*\|")
_TOTAL_RUNTIME = re.compile(r"^- Total scan wall time: \*\*[0-9]+(?:\.[0-9]+)?s\*\*$")


def _committed_text(path: Path) -> str:
    proc = subprocess.run(
        ["git", "show", f"HEAD:{path.as_posix()}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise SystemExit(f"cannot read committed evidence {path}: {proc.stderr.strip()}")
    return proc.stdout


def _load_json(text: str) -> dict[str, Any]:
    value = json.loads(text)
    if not isinstance(value, dict):
        raise SystemExit("validation evidence root must be a JSON object")
    return value


def _normalize_tool(data: dict[str, Any]) -> None:
    tool = data.get("tool")
    if isinstance(tool, dict):
        tool.pop("version", None)
        tool.pop("source_revision", None)


def _normalize_accuracy(data: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(data)
    _normalize_tool(out)
    return out


def _normalize_real_world(data: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(data)
    _normalize_tool(out)
    # Host/runtime provenance is deliberately recorded in generated evidence but
    # is not part of the scanner's semantic result and changes across CI runs.
    out.pop("environment", None)
    summary = out.get("summary")
    if isinstance(summary, dict):
        summary.pop("runtime_seconds", None)
    projects = out.get("projects")
    if isinstance(projects, list):
        for project in projects:
            if not isinstance(project, dict):
                continue
            project.pop("runtime_seconds", None)
            project.pop("engine_runtime_seconds", None)
            project.pop("clone_seconds", None)
    return out


def _normalize_accuracy_markdown(text: str) -> str:
    return "\n".join(
        line
        for line in text.splitlines()
        if not line.startswith("Tool: ConfigReach `")
    ).strip() + "\n"


def _normalize_real_world_markdown(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("Tool: ConfigReach `") or line.startswith("Runner: `"):
            continue
        if _TOTAL_RUNTIME.match(line):
            line = "- Total scan wall time: **<runtime>**"
        if line.startswith("|"):
            line = _RUNTIME_CELL.sub("| <runtime> |", line)
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def _assert_equal(label: str, committed: Any, generated: Any) -> None:
    if committed == generated:
        print(f"{label}: semantic evidence matches committed baseline")
        return
    if isinstance(committed, (dict, list)) and isinstance(generated, (dict, list)):
        before = json.dumps(committed, indent=2, sort_keys=True).splitlines()
        after = json.dumps(generated, indent=2, sort_keys=True).splitlines()
    else:
        before = str(committed).splitlines()
        after = str(generated).splitlines()
    import difflib

    diff = "\n".join(
        difflib.unified_diff(before, after, fromfile=f"committed/{label}", tofile=f"generated/{label}", lineterm="")
    )
    raise SystemExit(f"{label}: semantic evidence changed\n{diff}")


def verify_accuracy(json_path: Path, markdown_path: Path) -> None:
    committed_json = _load_json(_committed_text(json_path))
    generated_json = _load_json(json_path.read_text(encoding="utf-8"))
    _assert_equal("accuracy.json", _normalize_accuracy(committed_json), _normalize_accuracy(generated_json))

    committed_md = _committed_text(markdown_path)
    generated_md = markdown_path.read_text(encoding="utf-8")
    _assert_equal(
        "accuracy.md",
        _normalize_accuracy_markdown(committed_md),
        _normalize_accuracy_markdown(generated_md),
    )


def verify_real_world(json_path: Path, markdown_path: Path) -> None:
    committed_json = _load_json(_committed_text(json_path))
    generated_json = _load_json(json_path.read_text(encoding="utf-8"))
    _assert_equal(
        "real-world.json",
        _normalize_real_world(committed_json),
        _normalize_real_world(generated_json),
    )

    committed_md = _committed_text(markdown_path)
    generated_md = markdown_path.read_text(encoding="utf-8")
    _assert_equal(
        "real-world.md",
        _normalize_real_world_markdown(committed_md),
        _normalize_real_world_markdown(generated_md),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify generated validation evidence while ignoring volatile provenance/timing fields."
    )
    parser.add_argument("kind", choices=("accuracy", "real-world", "all"))
    args = parser.parse_args()

    if args.kind in {"accuracy", "all"}:
        verify_accuracy(
            Path("validation/results/accuracy.json"),
            Path("validation/results/accuracy.md"),
        )
    if args.kind in {"real-world", "all"}:
        verify_real_world(
            Path("validation/results/real-world.json"),
            Path("validation/results/real-world.md"),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
