from __future__ import annotations

import io
import sys
import tarfile
from pathlib import Path

import pytest

from configreach._compat import safe_extract_tar
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
    assert (3, 8) <= sys.version_info[:2] <= (3, 14)


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
