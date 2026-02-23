from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def resolve_path(raw_path: str) -> Path:
    return Path(raw_path).expanduser().resolve()


def iter_files(root: Path, suffix: str) -> Iterable[Path]:
    if not root.exists():
        return iter(())
    return root.rglob(f"*{suffix}")


def read_json(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))
