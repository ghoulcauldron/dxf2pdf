from __future__ import annotations

from pathlib import Path


def is_dxf(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".dxf"


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)