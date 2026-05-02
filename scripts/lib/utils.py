from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def slugify(value: str, max_length: int = 80) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:max_length].strip("-") or "paper"


def stable_paper_id(title: str, year: int | None = None, first_author: str | None = None) -> str:
    parts = []
    if first_author:
        parts.append(slugify(first_author.split()[-1], 24))
    if year:
        parts.append(str(year))
    parts.append(slugify(title, 48))
    return "-".join(part for part in parts if part)


def read_json(path: str | Path, default: Any = None) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return default
    return json.loads(file_path.read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> Path:
    file_path = Path(path)
    ensure_dir(file_path.parent)
    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def write_text(path: str | Path, content: str) -> Path:
    file_path = Path(path)
    ensure_dir(file_path.parent)
    file_path.write_text(content, encoding="utf-8")
    return file_path
