from __future__ import annotations

import re
from pathlib import Path


USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)")
SHA_REF = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    violations: list[str] = []
    workflow_dir = Path(".github/workflows")
    for path in sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")]):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = USES.match(line)
            if not match:
                continue
            target = match.group(1).strip("'\"")
            if target.startswith("./"):
                continue
            if "@" not in target:
                violations.append(f"{path}:{line_number}: action reference has no immutable ref: {target}")
                continue
            action, ref = target.rsplit("@", 1)
            if not SHA_REF.fullmatch(ref):
                violations.append(
                    f"{path}:{line_number}: external action must be pinned to a 40-character commit SHA: {action}@{ref}"
                )

    if violations:
        print("Mutable GitHub Action references detected:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("All external GitHub Actions are pinned to immutable commit SHAs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
