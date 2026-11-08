"""Stable, readable output-file tags for sweep scripts (FINDINGS §41 User decisions).

Overrides are encoded as sorted ``key=value`` pairs; when that is too long the tag falls back to the first
8 hex chars of a sha1 of the canonical JSON. ``guard_overwrite`` refuses to replace an existing file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Mapping, Optional

MAX_READABLE = 48


def overrides_tag(overrides: Optional[Mapping[str, Any]], max_len: int = MAX_READABLE) -> str:
    """'' for no overrides; else e.g. ``push_low_gap=9,push_top_gap=3`` or ``h-1a2b3c4d`` if too long."""
    if not overrides:
        return ""
    readable = ",".join(f"{k}={overrides[k]}" for k in sorted(overrides))
    readable = re.sub(r"[^A-Za-z0-9_.=,+-]", "-", readable)
    if len(readable) <= max_len:
        return readable
    canon = json.dumps(dict(overrides), sort_keys=True, separators=(",", ":"), default=str)
    return "h-" + hashlib.sha1(canon.encode()).hexdigest()[:8]


def scope_tag(scope: str) -> str:
    return "_nonref" if scope == "non_reference" else ""


class OutputExistsError(FileExistsError):
    pass


def guard_overwrite(path: str, overwrite: bool) -> None:
    if os.path.exists(path) and not overwrite:
        raise OutputExistsError(f"refusing to overwrite existing {path} (pass --overwrite)")
