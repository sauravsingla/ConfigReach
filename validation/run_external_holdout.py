from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configreach import __version__
from validation.run_real_world import _project_result, _review_map, _source_revision


FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def _repo_names(document: dict) -> set[str]:
    projects = document.get("projects", [])
    if not isinstance(projects, list):
        raise ValueError("projects must be a list")
    return {item.get("repo", "") for item in projects if isinstance(item, dict) and item.get("repo")}


def validate_manifest(manifest: dict, baseline: dict | None = None) -> dict:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    suite = manifest.get("suite")
    if not isinstance(suite, dict):
        errors.append("suite must be an object")
        suite = {}

    if not suite.get("id"):
        errors.append("suite.id is required")
    if not suite.get("title"):
        errors.append("suite.title is required")
    if suite.get("selection_frozen_before_scan") is not True:
        errors.append("suite.selection_frozen_before_scan must be true")

    profile_doc = suite.get("profiles")
    if not isinstance(profile_doc, dict) or not profile_doc:
        errors.append("suite.profiles must be a non-empty object")
        profile_names: set[str] = set()
    else:
        profile_names = set(profile_doc)
        if "full" not in profile_names:
            errors.append("suite.profiles must define a full profile")

    projects = manifest.get("projects")
    if not isinstance(projects, list) or not projects:
        errors.append("projects must be a non-empty list")
        projects = []

    seen: set[str] = set()
    ecosystems: set[str] = set()
    profile_counts = {name: 0 for name in profile_names}

    for index, project in enumerate(projects):
        prefix = f"projects[{index}]"
        if not isinstance(project, dict):
            errors.append(f"{prefix} must be an object")
            continue

        repo = project.get("repo")
        if not isinstance(repo, str) or not REPO_RE.fullmatch(repo):
            errors.append(f"{prefix}.repo must be owner/name")
        elif repo in seen:
            errors.append(f"{prefix}.repo duplicates {repo}")
        else:
            seen.add(repo)

        commit = project.get("commit")
        if not isinstance(commit, str) or not FULL_SHA_RE.fullmatch(commit):
            errors.append(f"{prefix}.commit must be a lowercase 40-character Git SHA")

        ecosystem = project.get("ecosystem")
        if not isinstance(ecosystem, str) or not ecosystem.strip():
            errors.append(f"{prefix}.ecosystem is required")
        else:
            ecosystems.add(ecosystem)

        source_url = project.get("source_url")
        if not isinstance(source_url, str) or source_url != f"https://github.com/{repo}":
            errors.append(f"{prefix}.source_url must be https://github.com/<repo>")

        rationale = project.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"{prefix}.rationale is required")

        profiles = project.get("profiles")
        if not isinstance(profiles, list) or not profiles or any(not isinstance(name, str) for name in profiles):
            errors.append(f"{prefix}.profiles must be a non-empty list of profile names")
            continue
        if len(profiles) != len(set(profiles)):
            errors.append(f"{prefix}.profiles contains duplicates")
        unknown = sorted(set(profiles) - profile_names)
        if unknown:
            errors.append(f"{prefix}.profiles contains unknown profiles: {', '.join(unknown)}")
        if "full" not in profiles:
            errors.append(f"{prefix}.profiles must include full")
        for name in set(profiles) & profile_names:
            profile_counts[name] += 1

    if "smoke" in profile_names and profile_counts.get("smoke", 0) == 0:
        errors.append("smoke profile must contain at least one project")

    overlap: list[str] = []
    if baseline is not None:
        overlap = sorted(seen & _repo_names(baseline))
        if overlap:
            errors.append("holdout overlaps baseline repositories: " + ", ".join(overlap))

    if errors:
        raise ValueError("\n".join(errors))

    return {
        "projects": len(projects),
        "ecosystems": len(ecosystems),
        "profiles": dict(sorted(profile_counts.items())),
        "baseline_overlap": overlap,
    }


def select_projects(manifest: dict, profile: str, requested_repos: list[str] | None = None) -> list[dict]:
    profiles = manifest["suite"]["profiles"]
    if profile not in profiles:
        raise ValueError(f"unknown profile {profile!r}; choose from {', '.join(sorted(profiles))}")

    available = {item["repo"] for item in manifest["projects"]}
    requested = set(requested_repos or [])
    unknown = sorted(requested - available)
    if unknown:
        raise ValueError("requested repositories are not in the frozen holdout: " + ", ".join(unknown))

    selected = [
        item
        for item in manifest["projects"]
        if profile in item["profiles"] and (not requested or item["repo"] in requested)
    ]
    if not selected:
        raise ValueError("selection produced zero projects")
    return selected


def _summary(projects: list[dict]) -> dict:
    config_total = sum(item["configuration_inputs"] for item in projects)
    covered_total = sum(item["covered_inputs"] for item in projects)
    return {
        "projects_scanned": len(projects),
        "configuration_inputs": config_total,
        "covered_inputs": covered_total,
        "configuration_coverage": round(covered_total / config_total, 6) if config_total else 1.0,
        "runtime_seconds": round(sum(item["runtime_seconds"] for item in projects), 6),
        "projects_with_manual_review": sum(
            1 for item in projects if item["manual_review"]["scope"] != "not-yet-reviewed"
        ),
        "reviewed_false_positives": sum(
            item["manual_review"]["false_positive_count"] for item in projects
        ),
        "reviewed_false_negatives": sum(
            item["manual_review"]["false_negative_count"] for item in projects
        ),
    }


def _markdown(data: dict) -> str:
    suite = data["suite"]
    selection = data["selection"]
    summary = data["summary"]
    rows = [
        f"# {suite['title']}",
        "",
        "Predetermined external holdout scans of immutable upstream commits.",
        "Target projects are never executed and their dependencies are not installed.",
        "Observed configuration coverage is ConfigReach output, not independently labelled ground truth.",
        "",
        f"- Suite: `{suite['id']}`",
        f"- Captured: `{data['captured_at']}`",
        f"- Source: {suite['source']}",
        f"- Profile: `{selection['profile']}`",
        f"- Baseline overlap: **{selection['baseline_overlap_count']}**",
        f"- Selection frozen before scan: **{str(suite['selection_frozen_before_scan']).lower()}**",
        "",
        "## Selection policy",
        "",
        suite["selection_policy"],
        "",
        "## Results",
        "",
        "| Project | Ecosystem | Configs | Covered | Coverage | Runtime |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for item in data["projects"]:
        rows.append(
            f"| {item['repo']} | {item['ecosystem']} | {item['configuration_inputs']} | "
            f"{item['covered_inputs']} | {item['configuration_coverage'] * 100:.1f}% | "
            f"{item['runtime_seconds']:.3f}s |"
        )

    rows += [
        "",
        "## Aggregate",
        "",
        f"- Projects scanned: **{summary['projects_scanned']}**",
        f"- Configuration inputs discovered: **{summary['configuration_inputs']}**",
        f"- Inputs with detected test/runtime evidence: **{summary['covered_inputs']}**",
        f"- Aggregate observed key coverage: **{summary['configuration_coverage'] * 100:.1f}%**",
        f"- Total scan wall time: **{summary['runtime_seconds']:.3f}s**",
        "",
        "## Claim boundary",
        "",
        "This holdout measures behavior on previously unscanned external repositories. "
        "It does not turn repository-level coverage into precision/recall. "
        "Precision, recall and F1 remain properties of the separately hand-labelled accuracy corpus.",
        "",
        "## Reproduction",
        "",
        "```bash",
        data["reproduction"],
        "```",
        "",
        f"Runner: `{data['environment']['platform']}` / Python `{data['environment']['python']}`.",
    ]
    if data["failures"]:
        rows += ["", "## Failures", ""]
        for failure in data["failures"]:
            rows.append(f"- `{failure['repo']}` at `{failure['commit']}`: {failure['error']}")
    return "\n".join(rows) + "\n"


def _reproduction(args: argparse.Namespace) -> str:
    parts = [
        "python validation/run_external_holdout.py",
        f"--manifest {args.manifest}",
        f"--baseline-manifest {args.baseline_manifest}",
        f"--profile {args.profile}",
        f"--json {args.json}",
        f"--markdown {args.markdown}",
    ]
    if args.reviews is not None:
        parts.append(f"--reviews {args.reviews}")
    for repo in args.repo:
        parts.append(f"--repo {repo}")
    return " ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run ConfigReach against a frozen, baseline-disjoint external holdout corpus"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("validation/external_holdout_projects.json"),
    )
    parser.add_argument(
        "--baseline-manifest",
        type=Path,
        default=Path("validation/real_world_projects.json"),
    )
    parser.add_argument(
        "--reviews",
        type=Path,
        default=Path("validation/external_holdout_reviews.json"),
    )
    parser.add_argument("--profile", default="full")
    parser.add_argument("--repo", action="append", default=[], help="Run only a named frozen holdout repo")
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("validation/results/external-holdout.json"),
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=Path("validation/results/external-holdout.md"),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate corpus integrity and profile selection without network access",
    )
    args = parser.parse_args()

    manifest = _read_json(args.manifest)
    baseline = _read_json(args.baseline_manifest)
    validation = validate_manifest(manifest, baseline)
    selected = select_projects(manifest, args.profile, args.repo)
    if args.validate_only:
        print(
            json.dumps(
                {
                    **validation,
                    "profile": args.profile,
                    "selected_projects": [item["repo"] for item in selected],
                },
                sort_keys=True,
            )
        )
        return 0

    reviews = _review_map(args.reviews)
    projects: list[dict] = []
    failures: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="configreach-external-holdout-") as tmp:
        work = Path(tmp)
        for project in selected:
            try:
                result = _project_result(project, work, reviews.get(project["repo"]))
                result["source_url"] = project["source_url"]
                result["rationale"] = project["rationale"]
                result["profiles"] = list(project["profiles"])
                projects.append(result)
            except Exception as exc:
                failures.append(
                    {
                        "repo": project["repo"],
                        "commit": project["commit"],
                        "error": str(exc),
                    }
                )
            finally:
                target = work / project["repo"].replace("/", "__")
                shutil.rmtree(target, ignore_errors=True)

    output = {
        "schema_version": 1,
        "captured_at": manifest["captured_at"],
        "suite": manifest["suite"],
        "selection": {
            "profile": args.profile,
            "requested_repositories": list(args.repo),
            "projects_requested": len(selected),
            "baseline_manifest": str(args.baseline_manifest),
            "baseline_overlap_count": len(validation["baseline_overlap"]),
        },
        "tool": {
            "name": "ConfigReach",
            "version": __version__,
            "source_revision": _source_revision(),
        },
        "methodology": {
            "static_only": True,
            "target_code_executed": False,
            "dependencies_installed": False,
            "pinned_commits": True,
            "holdout_frozen_before_scan": True,
            "baseline_disjoint": True,
            "manual_review_is_exhaustive": False,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "summary": {
            "projects_requested": len(selected),
            **_summary(projects),
        },
        "projects": projects,
        "failures": failures,
        "reproduction": _reproduction(args),
    }

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(_markdown(output), encoding="utf-8")
    print(json.dumps(output["summary"], sort_keys=True))

    if failures:
        for failure in failures:
            print(f"FAILED {failure['repo']}: {failure['error']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
