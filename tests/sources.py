"""Access to the fetched reference documents (see scripts/fetch_upstream.py)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

UPSTREAM = Path(__file__).resolve().parent / "upstream"


def upstream_text(name: str) -> str:
    """Return a fetched document, checked against its manifest entry.

    The documents are not committed: ``python scripts/fetch_upstream.py`` fetches them.
    Their tests skip while a document is absent and fail if it differs from the manifest.
    """
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    entry = json.loads((UPSTREAM / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == entry["sha256"], f"{name} differs from MANIFEST"
    return body.decode("utf-8")
