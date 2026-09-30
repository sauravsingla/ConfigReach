from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
SHARDS = HERE / "data" / "shards"
DEFAULT_OUTPUT = HERE / "data" / "configreach_50k_scenarios.jsonl"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rebuild(output: Path = DEFAULT_OUTPUT) -> Path:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    compressed = bytearray()
    for entry in manifest["shards"]:
        path = SHARDS / entry["name"]
        raw = path.read_bytes()
        if len(raw) != entry["bytes"] or sha256(raw) != entry["sha256"]:
            raise SystemExit(f"shard integrity failure: {path}")
        compressed.extend(base64.b64decode(raw))
    compressed_bytes = bytes(compressed)
    if len(compressed_bytes) != manifest["xz_bytes"] or sha256(compressed_bytes) != manifest["xz_sha256"]:
        raise SystemExit("reconstructed XZ integrity failure")
    data = lzma.decompress(compressed_bytes)
    if len(data) != manifest["jsonl_bytes"] or sha256(data) != manifest["jsonl_sha256"]:
        raise SystemExit("reconstructed JSONL integrity failure")
    rows = data.count(b"\n")
    if rows != manifest["scenario_count"]:
        raise SystemExit(f"expected {manifest['scenario_count']} rows, found {rows}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(f"rebuilt {rows:,} rows -> {output}")
    print(f"sha256={sha256(data)}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rebuild(args.output)


if __name__ == "__main__":
    main()
