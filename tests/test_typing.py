"""The annotations accept every value type the docs promise, as a typed caller sees them."""

from __future__ import annotations

import importlib
import importlib.util
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from compactnum import format

ROOT = Path(__file__).resolve().parents[1]

CONSUMER = """
from decimal import Decimal
from fractions import Fraction
from typing import SupportsFloat, SupportsIndex

from compactnum import format


def caller(index_like: SupportsIndex, float_like: SupportsFloat) -> list[str]:
    return [
        format(1200),
        format(1.5),
        format(Decimal("2.5e6")),
        format(Fraction(1, 3)),
        format(index_like),
        format(float_like),
        format(2000, trim_zeros=False, style="short", base=1024, unit="B", decimal_sep=","),
    ]
"""

NUMPY_CONSUMER = """
import numpy as np

from compactnum import format

texts = [format(np.int64(1200)), format(np.uint8(200)), format(np.float32(1.5))]
"""

REJECTED = """
from compactnum import format

text = format("1200")
"""


def _mypy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str) -> tuple[str, int]:
    api = pytest.importorskip("mypy.api")
    if (ROOT / "src" / "compactnum").is_dir():
        monkeypatch.setenv("MYPYPATH", str(ROOT / "src"))
    path = tmp_path / "consumer.py"
    path.write_text(source, encoding="utf-8")
    config = tmp_path / "mypy.ini"
    config.write_text("[mypy]\n", encoding="utf-8")
    cache = str(tmp_path / "cache")
    args = ["--strict", "--config-file", str(config), "--cache-dir", cache, str(path)]
    out, err, status = api.run(args)
    return out + err, status


def test_mypy_strict_accepts_every_documented_value_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = CONSUMER
    if importlib.util.find_spec("numpy") is not None:
        source += NUMPY_CONSUMER
    output, status = _mypy(tmp_path, monkeypatch, source)
    assert status == 0, output


def test_mypy_strict_still_rejects_a_string_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, status = _mypy(tmp_path, monkeypatch, REJECTED)
    assert status == 1 and "arg-type" in output, output


def test_the_same_values_format_at_run_time() -> None:
    class Count(int):
        pass

    assert format(Fraction(1, 3)) == "0.3"
    assert format(Count(1200)) == "1.2k"
    assert format(Decimal("2.5e6")) == "2.5M"
    if importlib.util.find_spec("numpy") is not None:
        np = importlib.import_module("numpy")
        assert format(np.int64(1200)) == "1.2k" and format(np.float32(1.5)) == "1.5"
