from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from . import __version__
from ._compat import safe_extract_tar
from .baseline import baseline_path, write_baseline
from .config import load_settings
from .discover import scan
from .models import ConfigKey, ScanReport
from .reporters import markdown_report, render
from .tracer import summarize_trace, trace_python

FORMATS = ["text", "json", "markdown", "sarif", "html"]


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", nargs="?", default=".", help="repository path")
    parser.add_argument("--format", choices=FORMATS, default="text")
    parser.add_argument("--output", help="write output to a file")
    parser.add_argument("--no-cache", action="store_true", help="disable persistent scan cache")


def _emit(text: str, output: str | None) -> None:
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def _status(report: ScanReport, fail_under: float | None, fail_on: list[str] | None = None) -> int:
    settings = load_settings(Path(report.root))
    threshold = settings.fail_under if fail_under is None else fail_under
    if threshold is not None and report.coverage * 100 < threshold:
        return 2
    policies = set(settings.fail_on)
    policies.update(x.lower() for x in (fail_on or []))
    if not policies:
        return 0
    for finding in report.findings:
        tokens = {finding.rule_id.lower(), finding.severity.lower()}
        if finding.rule_id == "CR001": tokens.add("uncovered")
        if finding.rule_id == "CR002": tokens.add("undeclared")
        if finding.rule_id == "CR004": tokens.add("untested-values")
        if finding.rule_id == "CR005": tokens.add("unsafe-default")
        if finding.rule_id == "CR008": tokens.add("default-only")
        if finding.rule_id == "CR009": tokens.add("global-env-overwrite")
        if tokens & policies:
            return 2
    return 0


def _explain(item: ConfigKey) -> str:
    data = item.to_dict()
    lines = [
        f"{item.name}", "=" * len(item.name),
        f"Covered:   {'yes' if item.covered else 'no'}",
        f"Runtime:   {'observed' if item.runtime_observed else 'not observed'}",
        f"Used:      {'yes' if item.used else 'no'}",
        f"Declared:  {'yes' if item.declared else 'no'}",
        f"Baseline:  {'ignored' if item.baseline_ignored else 'active'}",
        f"Sensitive: {'yes' if data['sensitive'] else 'no'}",
        f"Blast radius: {item.blast_radius_files} files / {item.blast_radius_modules} modules",
        f"Categories: {', '.join(data['categories']) or '—'}",
        f"Languages:  {', '.join(data['languages']) or '—'}",
    ]
    for heading, field in [("Reads", item.reads), ("Branches", item.branches), ("Declarations", item.declarations), ("Tests", item.test_mentions)]:
        lines += ["", heading + ":"]
        lines += [f"  {loc.path}:{loc.line} ({loc.detail or loc.kind})" for loc in field] or ["  —"]
    if data["expected_values"]:
        lines += ["", "Expected values: " + ", ".join(data["expected_values"])]
        lines += ["Tested values:   " + (", ".join(data["tested_values"]) or "—")]
        lines += [f"Value coverage:  {(item.value_coverage or 0)*100:.1f}%"]
    if data["validators"]:
        lines += ["", "Validators: " + ", ".join(data["validators"])]
    return "\n".join(lines) + "\n"


def _matrix(report: ScanReport) -> str:
    lines = ["KEY\tCOVERED\tUSED\tDECLARED\tVALUE_COVERAGE\tBLAST_FILES\tCATEGORIES"]
    for name in sorted(report.keys):
        item = report.keys[name]
        value_cov = "" if item.value_coverage is None else f"{item.value_coverage*100:.1f}%"
        lines.append(
            f"{name}\t{'yes' if item.covered else 'no'}\t{'yes' if item.used else 'no'}\t"
            f"{'yes' if item.declared else 'no'}\t{value_cov}\t{item.blast_radius_files}\t{','.join(sorted(item.categories))}"
        )
    return "\n".join(lines) + "\n"


def _changed_paths(root: Path, rev_range: str) -> set[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", rev_range], cwd=root, capture_output=True, text=True, check=False
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    return {line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()}


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


def _scan_revision(root: Path, revision: str) -> ScanReport:
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
        with tarfile.open(archive, "r") as bundle:
            safe_extract_tar(bundle, snapshot)
        return scan(snapshot, use_cache=False)


def _diff_report(root: Path, rev_range: str, *, use_cache: bool = True) -> str:
    head = scan(root, use_cache=use_cache)
    settings = load_settings(root)
    changed = _changed_paths(root, rev_range)
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
    )
    touched = {item.name for item in head.keys_for_paths(changed)}
    impacted_names = sorted(touched | set(new_names) | set(changed_domain_names))
    impacted = [head.keys[name] for name in impacted_names if name in head.keys]
    untested = [item for item in impacted if not item.covered and not item.baseline_ignored]
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
        f"- Changed test files: **{len(changed_tests)}**",
        f"- New configuration inputs: **{len(new_names)}**",
        f"- Removed configuration inputs: **{len(removed_names)}**",
        f"- Inputs with changed known/default/branch domains: **{len(changed_domain_names)}**",
        f"- Newly introduced untested inputs: **{len(new_untested)}**",
        f"- Newly introduced untested values: **{sum(len(values) for _, values in new_value_gaps)}**", "",
    ]
    if not impacted:
        lines.append("No configuration inputs were added, changed, or detected in changed files.")
    else:
        lines += ["| Key | Delta | Coverage | Values | Blast radius |", "|---|---|---|---|---:|"]
        for item in impacted:
            if item.name in new_names:
                delta = "NEW"
            elif item.name in changed_domain_names:
                delta = "domain changed"
            else:
                delta = "touched"
            values = "—"
            gap = next((v for n, v in new_value_gaps if n == item.name), None)
            if gap:
                values = "untested new: " + ", ".join(gap)
            lines.append(
                f"| `{item.name}` | {delta} | {'✅ covered' if item.covered else '❌ untested'} | "
                f"{values} | {item.blast_radius_files} files / {item.blast_radius_modules} modules |"
            )
    if removed_names:
        lines += ["", "Removed inputs: " + ", ".join(f"`{name}`" for name in removed_names)]
    if new_untested or new_value_gaps:
        lines += ["", "> ⚠️ This PR introduces configuration states without detected test-value evidence."]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="configreach", description="Configuration coverage for your test suite")
    parser.add_argument("--version", action="version", version=f"ConfigReach {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("scan", "coverage", "export"):
        p = sub.add_parser(name)
        _add_common(p)
        p.add_argument("--fail-under", type=float, help="exit non-zero below this key coverage percentage")
        p.add_argument("--fail-on", action="append", default=[], help="fail on policy: uncovered, undeclared, untested-values, unsafe-default, warning, error, or CRxxx")

    p = sub.add_parser("explain")
    p.add_argument("key")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--no-cache", action="store_true")

    p = sub.add_parser("matrix")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--no-cache", action="store_true")

    p = sub.add_parser("diff")
    p.add_argument("revision_range", help="for example origin/main...HEAD")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--output")
    p.add_argument("--no-cache", action="store_true")

    p = sub.add_parser("pr-comment", help="generate a GitHub-ready Markdown PR comment")
    p.add_argument("revision_range", help="for example origin/main...HEAD")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--output")

    p = sub.add_parser("doctor")
    p.add_argument("path", nargs="?", default=".")

    p = sub.add_parser("init")
    p.add_argument("path", nargs="?", default=".")

    p = sub.add_parser("baseline", help="create or inspect the legacy finding baseline")
    baseline_sub = p.add_subparsers(dest="baseline_command", required=True)
    b = baseline_sub.add_parser("create")
    b.add_argument("path", nargs="?", default=".")
    b.add_argument("--all", action="store_true", help="baseline all discovered keys, not just uncovered keys")

    p = sub.add_parser("cache", help="manage the persistent scan cache")
    cache_sub = p.add_subparsers(dest="cache_command", required=True)
    c = cache_sub.add_parser("clear")
    c.add_argument("path", nargs="?", default=".")

    p = sub.add_parser("trace", help="trace Python environment reads while running a command")
    p.add_argument("--path", default=".")
    p.add_argument("--output", default=".configreach/trace.jsonl")
    p.add_argument("remainder", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command in {"scan", "coverage", "export"}:
        report = scan(args.path, use_cache=not args.no_cache)
        _emit(render(report, args.format), args.output)
        return _status(report, args.fail_under, args.fail_on)

    if args.command == "explain":
        report = scan(args.path, use_cache=not args.no_cache)
        item = report.key(args.key)
        if item is None:
            sys.stderr.write(f"ConfigReach: unknown configuration key: {args.key}\n")
            return 1
        sys.stdout.write(_explain(item))
        return 0

    if args.command == "matrix":
        sys.stdout.write(_matrix(scan(args.path, use_cache=not args.no_cache)))
        return 0

    if args.command in {"diff", "pr-comment"}:
        root = Path(args.path).resolve()
        try:
            text = _diff_report(root, args.revision_range, use_cache=not getattr(args, "no_cache", False))
            _emit(text, getattr(args, "output", None))
            return 0
        except RuntimeError as exc:
            sys.stderr.write(f"ConfigReach: {exc}\n")
            return 2

    if args.command == "doctor":
        root = Path(args.path).resolve()
        report = scan(root)
        settings = load_settings(root)
        checks = [
            (root.exists(), "repository path exists"),
            ((root / ".git").exists(), "git metadata present (optional outside diff mode)"),
            (report.files_scanned > 0, "supported source/config files found"),
            (report.tests_scanned > 0, "test files found"),
        ]
        for ok, message in checks:
            print(f"{'✓' if ok else '!'} {message}")
        print(f"✓ deterministic engine; no network/API/model required")
        print(f"✓ cache {'enabled' if settings.cache else 'disabled'}")
        print(f"✓ plugin entry points {'enabled' if settings.plugins else 'disabled'}")
        if report.package_roots:
            print(f"✓ monorepo/package roots detected: {', '.join(report.package_roots)}")
        return 0 if checks[0][0] and checks[2][0] else 1

    if args.command == "init":
        root = Path(args.path).resolve()
        target = root / "configreach.toml"
        if target.exists():
            sys.stderr.write("ConfigReach: configreach.toml already exists\n")
            return 1
        target.write_text(
            "[configreach]\nfail_under = 60\nfail_on = [\"error\"]\n"
            "ignore = [\"vendor/**\", \"generated/**\"]\n"
            "test_patterns = [\"tests/**\", \"**/test_*.py\", \"**/*.spec.ts\"]\n"
            "baseline = \".configreach/baseline.json\"\ntrace_file = \".configreach/trace.jsonl\"\n"
            "cache = true\nplugins = true\n",
            encoding="utf-8",
        )
        print(f"Created {target}")
        return 0

    if args.command == "baseline":
        root = Path(args.path).resolve()
        settings = load_settings(root)
        original = settings.baseline
        settings.baseline = ".configreach/nonexistent-baseline.json"
        report = scan(root, settings=settings, use_cache=False)
        target = baseline_path(root, original)
        write_baseline(report, target, uncovered_only=not args.all)
        print(f"Created {target} with {sum(1 for x in report.keys.values() if (args.all or not x.covered))} keys")
        return 0

    if args.command == "cache":
        root = Path(args.path).resolve()
        target = root / ".configreach" / "cache"
        if target.exists():
            shutil.rmtree(target)
        print(f"Cleared {target}")
        return 0

    if args.command == "trace":
        command = list(args.remainder)
        if command and command[0] == "--":
            command = command[1:]
        root = Path(args.path).resolve()
        output = (root / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
        try:
            code = trace_python(command, root, output)
        except ValueError as exc:
            sys.stderr.write(f"ConfigReach: {exc}\n")
            return 2
        keys, pairs = summarize_trace(output)
        print(f"Trace: {keys} configuration keys, {pairs} distinct value fingerprints")
        print(f"Trace file: {output}")
        return code
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
