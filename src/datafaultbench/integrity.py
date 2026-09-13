from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_receipt(paths: Iterable[str | Path], output: str | Path, metadata: dict) -> None:
    records = []
    for raw in sorted((Path(p) for p in paths), key=lambda p: str(p)):
        records.append({
            "path": str(raw.as_posix()),
            "size_bytes": raw.stat().st_size,
            "sha256": sha256_file(raw),
        })
    payload = {"metadata": metadata, "files": records}
    Path(output).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

