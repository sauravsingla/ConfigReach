"""Cross-version compatibility and security helpers."""

from __future__ import annotations

import shutil
import tarfile
from pathlib import Path, PurePosixPath


def validate_git_revision_range(value: str) -> str:
    """Reject Git revision arguments that can be reinterpreted as options."""
    if not value or "\x00" in value:
        raise ValueError("git revision range must be a non-empty revision expression")
    if "..." in value:
        parts = value.split("...", 1)
    elif ".." in value:
        parts = value.split("..", 1)
    else:
        parts = [value]
    if any(not part or part.startswith("-") for part in parts):
        raise ValueError(f"unsafe git revision range: {value!r}")
    return value


def _safe_tar_target(destination: Path, member_name: str) -> Path:
    """Resolve a tar member beneath *destination* or reject it.

    Tar headers use POSIX separators, but backslashes are normalized as well so
    Windows hosts cannot reinterpret a crafted name after validation.
    """
    normalized = member_name.replace("\\", "/")
    if not normalized or "\x00" in normalized:
        raise ValueError("unsafe tar member name")
    relative = PurePosixPath(normalized)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe tar member path: {member_name!r}")
    if relative.parts and len(relative.parts[0]) >= 2 and relative.parts[0][1] == ":":
        raise ValueError(f"unsafe tar member drive path: {member_name!r}")

    root = destination.resolve()
    target = root.joinpath(*relative.parts).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"tar member escapes destination: {member_name!r}") from exc
    return target


def safe_extract_tar(archive: tarfile.TarFile, destination: Path) -> None:
    """Extract only regular files and directories without path traversal.

    This deliberately avoids ``TarFile.extractall`` so Python 3.8-3.11 receive
    the same traversal/link protections as newer runtimes instead of falling
    back to the historical unrestricted extraction behavior.
    """
    destination.mkdir(parents=True, exist_ok=True)
    for member in archive.getmembers():
        target = _safe_tar_target(destination, member.name)
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if not member.isfile():
            raise ValueError(f"unsupported tar member type: {member.name!r}")
        target.parent.mkdir(parents=True, exist_ok=True)
        source = archive.extractfile(member)
        if source is None:
            raise ValueError(f"could not read tar member: {member.name!r}")
        with source, target.open("wb") as handle:
            shutil.copyfileobj(source, handle)
