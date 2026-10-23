"""Fetch the reference documents listed in tests/upstream/MANIFEST.json.

The documents (the BIPM and NIST prefix tables, the Unicode CLDR English number data
and two pinned Wikipedia revisions) are not part of the repository. Their tests skip
until this script has fetched them; each download is checked against the size and
sha256 recorded in the manifest.

    python scripts/fetch_upstream.py            # fetch and verify
    python scripts/fetch_upstream.py --update   # fetch and record the new size and sha256

An entry with ``"form": "text"`` is an HTML page whose markup changes on every request
(session tokens, scripts): it is stored as its visible text, which is what is hashed.
"""

from __future__ import annotations

import datetime
import hashlib
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1] / "tests" / "upstream"
MANIFEST = FOLDER / "MANIFEST.json"


def visible_text(page: bytes) -> bytes:
    """Return an HTML page's visible text: scripts, styles and tags dropped, spaces collapsed."""
    text = page.decode("utf-8")
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip().encode("utf-8")


def main(argv: list[str]) -> int:
    update = "--update" in argv
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failed = 0
    for name, entry in manifest.items():
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "compactnum-tests"})
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
        if entry.get("form") == "text":
            body = visible_text(body)
        digest = hashlib.sha256(body).hexdigest()
        if len(body) != entry["size"] or digest != entry["sha256"]:
            if not update:
                print(f"{name}: got {len(body)} bytes, sha256 {digest}; manifest differs")
                failed += 1
                continue
            entry.update(size=len(body), sha256=digest, fetched=datetime.date.today().isoformat())
            print(f"{name}: updated")
        (FOLDER / name).write_bytes(body)
        print(f"{name}: ok")
    if update:
        text = json.dumps(manifest, indent=2) + "\n"
        MANIFEST.write_text(text, encoding="utf-8", newline="\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
