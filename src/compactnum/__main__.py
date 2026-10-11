"""Enable ``python -m compactnum`` to run the command-line interface."""

from __future__ import annotations

from ._cli import main

if __name__ == "__main__":
    raise SystemExit(main())
