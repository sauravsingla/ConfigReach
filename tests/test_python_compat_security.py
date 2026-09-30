from __future__ import annotations

import io
import sys
import tarfile
from pathlib import Path

import pytest

from configreach._compat import safe_extract_tar, validate_git_revision_range
from configreach.config import load_settings
from configreach.discover import scan


def _archive_with(member: tarfile.TarInfo, data: bytes = b"payload") -> tarfile.TarFile:
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w") as archive:
        if member.isfile():
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        else:
            archive.addfile(member)
    payload.seek(0)
    return tarfile.open(fileobj=payload, mode="r")


def test_supported_python_range() -> None:
    assert (3, 10) <= sys.version_info[:2] <= (3, 14)


def test_safe_extract_tar_extracts_regular_file(tmp_path: Path) -> None:
    member = tarfile.TarInfo("nested/file.txt")
    with _archive_with(member, b"ok") as archive:
        safe_extract_tar(archive, tmp_path)
    assert (tmp_path / "nested" / "file.txt").read_text(encoding="utf-8") == "ok"


@pytest.mark.parametrize("name", ["../escape.txt", "/absolute.txt", "..\\escape.txt", "C:/escape.txt"])
def test_safe_extract_tar_rejects_path_traversal(tmp_path: Path, name: str) -> None:
    member = tarfile.TarInfo(name)
    with _archive_with(member) as archive, pytest.raises(ValueError):
        safe_extract_tar(archive, tmp_path / "target")
    assert not (tmp_path / "escape.txt").exists()


def test_safe_extract_tar_rejects_links(tmp_path: Path) -> None:
    member = tarfile.TarInfo("link")
    member.type = tarfile.SYMTYPE
    member.linkname = "../escape.txt"
    with _archive_with(member) as archive, pytest.raises(ValueError):
        safe_extract_tar(archive, tmp_path / "target")


def test_scan_does_not_follow_file_symlinks_outside_repository(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text('import os\nLEAK = os.getenv("OUTSIDE_SECRET")\n', encoding="utf-8")
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text('import os\nMODE = os.getenv("SAFE_MODE")\n', encoding="utf-8")
    link = repository / "linked.py"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this platform")

    report = scan(repository, use_cache=False)
    assert "SAFE_MODE" in report.keys
    assert "OUTSIDE_SECRET" not in report.keys


def test_repository_config_cannot_escape_for_baseline_or_trace(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    (repository / "configreach.toml").write_text(
        "[configreach]\n"
        "baseline = '../outside.json'\n"
        f"trace_file = {str(outside)!r}\n",
        encoding="utf-8",
    )

    settings = load_settings(repository)
    assert settings.baseline == ".configreach/baseline.json"
    assert settings.trace_file == ".configreach/trace.jsonl"


@pytest.mark.parametrize("value", ["", "--ext-diff", "HEAD...--output=/tmp/out", "HEAD..-bad", "HEAD\x00main"])
def test_git_revision_validation_rejects_option_injection(value: str) -> None:
    with pytest.raises(ValueError):
        validate_git_revision_range(value)


def test_git_revision_validation_accepts_normal_ranges() -> None:
    assert validate_git_revision_range("origin/main...HEAD") == "origin/main...HEAD"
    assert validate_git_revision_range("HEAD~1..HEAD") == "HEAD~1..HEAD"
