# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/compactnum/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing.
- Run `python scripts/fetch_upstream.py` once to fetch the reference documents the
  ground-truth tests read (they skip without them), then `scripts/check.ps1` (format,
  lint, types, tests) and make sure it passes. `COMPACTNUM_E2E=1` adds the wheel tests.
- `python tests/programs.py` recaptures the ICU and GNU `numfmt` fixtures; it needs
  Node.js and `numfmt` on the PATH.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
