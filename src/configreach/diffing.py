from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from ._compat import safe_extract_tar
from .config import load_settings
from .engine import SemanticScanReport, scan


def changed_paths(root: Path, rev_range: str) -> set[str]:
    proc = subprocess.run(["git", "diff", "--name-only", rev_range], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    return {line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()}


def changed_line_ranges(root: Path, rev_range: str) -> dict[str, list[tuple[int, int]]]:
    proc = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", rev_range, "--"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    ranges: dict[str, list[tuple[int, int]]] = {}
    current: str | None = None
    hunk = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for line in proc.stdout.splitlines():
        if line.startswith("+++ "):
            value = line[4:].strip()
            if value == "/dev/null":
                current = None
            else:
                current = value[2:] if value.startswith("b/") else value
                current = current.replace("\\", "/")
            continue
        if current and line.startswith("@@"):
            match = hunk.match(line)
            if not match:
                continue
            start = int(match.group(1))
            count = int(match.group(2) or "1")
            if count > 0:
                ranges.setdefault(current, []).append((start, start + count - 1))
    return ranges


def _resolve_base_revision(root: Path, rev_range: str) -> str:
    if "..." in rev_range:
        left, right = rev_range.split("...", 1)
        proc = subprocess.run(["git", "merge-base", left, right], cwd=root, capture_output=True, text=True, check=False)
        if proc.returncode:
            raise RuntimeError(proc.stderr.strip() or "git merge-base failed")
        return proc.stdout.strip()
    if ".." in rev_range:
        return rev_range.split("..", 1)[0]
    return rev_range


def _scan_revision(root: Path, revision: str) -> SemanticScanReport:
    with tempfile.TemporaryDirectory(prefix="configreach-base-") as temp_dir:
        temp = Path(temp_dir)
        archive = temp / "snapshot.tar"
        snapshot = temp / "repo"
        snapshot.mkdir()
        with archive.open("wb") as handle:
            proc = subprocess.run(
                ["git", "archive", "--format=tar", revision], cwd=root, stdout=handle, stderr=subprocess.PIPE, check=False
            )
        if proc.returncode:
            message = proc.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or f"git archive failed for {revision}")
        import tarfile
        with tarfile.open(archive, "r") as bundle:
            safe_extract_tar(bundle, snapshot)
        return scan(snapshot, use_cache=False)


def diff_report(root: Path, rev_range: str, *, use_cache: bool = True) -> str:
    head = scan(root, use_cache=use_cache)
    settings = load_settings(root)
    changed = changed_paths(root, rev_range)
    ranges = changed_line_ranges(root, rev_range)
    changed_tests = {p for p in changed if settings.is_test(p)}
    base_revision = _resolve_base_revision(root, rev_range)
    base = _scan_revision(root, base_revision)

    head_names, base_names = set(head.keys), set(base.keys)
    new_names = sorted(head_names - base_names)
    removed_names = sorted(base_names - head_names)
    shared = head_names & base_names
    changed_domain_names = sorted(
        name for name in shared
        if head.keys[name].expected_values != base.keys[name].expected_values
        or head.keys[name].branch_values != base.keys[name].branch_values
        or head.keys[name].defaults != base.keys[name].defaults
        or head.keys[name].validators != base.keys[name].validators
    )

    line_touched = {item.name for item in head.keys_for_line_ranges(ranges)}
    fallback_paths = changed - set(ranges)
    file_fallback = {item.name for item in head.keys_for_paths(fallback_paths)}
    touched = line_touched | file_fallback
    impacted_names = sorted(touched | set(new_names) | set(changed_domain_names))
    impacted = [head.keys[name] for name in impacted_names if name in head.keys]
    new_untested = [head.keys[name] for name in new_names if not head.keys[name].covered and not head.keys[name].baseline_ignored]

    new_value_gaps: list[tuple[str, list[str]]] = []
    for name in sorted(shared | set(new_names)):
        current = head.keys[name]
        previous_values = base.keys[name].expected_values if name in base.keys else set()
        introduced = current.expected_values - previous_values
        missing = sorted(introduced - current.tested_values)
        if missing:
            new_value_gaps.append((name, missing))

    lines = [
        f"# ConfigReach PR configuration diff: `{rev_range}`", "",
        f"- Base snapshot: `{base_revision[:12]}`",
        f"- Changed files: **{len(changed)}**",
        f"- Changed head-side line ranges: **{sum(len(v) for v in ranges.values())}**",
        f"- Line-scoped configuration inputs touched: **{len(line_touched)}**",
        f"- Changed test files: **{len(changed_tests)}**",
        f"- New configuration inputs: **{len(new_names)}**",
        f"- Removed configuration inputs: **{len(removed_names)}**",
        f"- Inputs with changed known/default/branch/validator domains: **{len(changed_domain_names)}**",
        f"- Newly introduced untested inputs: **{len(new_untested)}**",
        f"- Newly introduced untested values: **{sum(len(values) for _, values in new_value_gaps)}**", "",
    ]
    if not impacted:
        lines.append("No configuration inputs were added, changed, or detected on changed lines.")
    else:
        lines += ["| Key | Delta | Coverage | Values | Blast radius |", "|---|---|---|---|---:|"]
        for item in impacted:
            if item.name in new_names:
                delta = "NEW"
            elif item.name in changed_domain_names:
                delta = "domain changed"
            elif item.name in line_touched:
                delta = "changed line"
            else:
                delta = "touched file"
            gap = next((v for n, v in new_value_gaps if n == item.name), None)
            values = "untested new: " + ", ".join(gap) if gap else "—"
            lines.append(
                f"| `{item.name}` | {delta} | {'✅ covered' if item.covered else '❌ untested'} | "
                f"{values} | {item.blast_radius_files} files / {item.blast_radius_modules} modules |"
            )
    if removed_names:
        lines += ["", "Removed inputs: " + ", ".join(f"`{name}`" for name in removed_names)]
    if new_untested or new_value_gaps:
        lines += ["", "> ⚠️ This PR introduces configuration states without detected test-value evidence."]
    return "\n".join(lines) + "\n"
