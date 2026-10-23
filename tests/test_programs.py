"""compactnum against the real output of ICU (Node.js Intl) and GNU numfmt."""

from __future__ import annotations

import json
import re
from decimal import Decimal

import programs
import pytest

from compactnum import format, parse

ICU = json.loads((programs.FIXTURES / "icu-compact-en.json").read_text(encoding="utf-8"))
NUMFMT = json.loads((programs.FIXTURES / "numfmt-iec.json").read_text(encoding="utf-8"))
STYLE = {"short": "si", "long": "long"}


def _check_icu(cases: list[list[object]], outputs: list[str]) -> int:
    checked = 0
    for (value, precision, display), output in zip(cases, outputs, strict=True):
        ours = format(Decimal(str(value)), precision=int(str(precision)), style=STYLE[str(display)])
        assert ours == programs.from_icu(output, str(display)), (value, precision, display)
        checked += 1
    return checked


def test_icu_capture_agrees_case_by_case() -> None:
    assert ICU["program"] == {"node": "24.18.0", "icu": "78.3", "cldr": "48.0"}
    cases = [case[:3] for case in ICU["cases"]]
    assert _check_icu(cases, [case[3] for case in ICU["cases"]]) == 3000
    assert any(re.fullmatch(r"-\d+(\.\d+)?K", case[3]) for case in ICU["cases"])


@pytest.mark.skipif(programs.NODE is None, reason="Node.js is not installed")
def test_icu_live_agrees_on_fresh_cases() -> None:
    cases = programs.icu_cases(77, 4000)
    _, outputs = programs.run_icu(cases)
    assert _check_icu(cases, outputs) == 4000


def _check_numfmt(cases: list[list[int]], outputs: list[str]) -> int:
    checked = 0
    for (value, precision), output in zip(cases, outputs, strict=True):
        assert format(value, base=1024, precision=precision, trim_zeros=False) == output
        checked += 1
    return checked


def test_numfmt_capture_agrees_case_by_case() -> None:
    assert NUMFMT["program"] == "numfmt (GNU coreutils) 8.32"
    cases = [case[:2] for case in NUMFMT["format"]]
    assert _check_numfmt(cases, [case[2] for case in NUMFMT["format"]]) == 2000
    for text, output in NUMFMT["parse"]:
        assert parse(text) == int(output), text
    assert len(NUMFMT["parse"]) == 1000


@pytest.mark.skipif(programs.NUMFMT is None, reason="GNU numfmt is not installed")
def test_numfmt_live_agrees_on_fresh_cases() -> None:
    cases = programs.numfmt_format_cases(78, 3000)
    assert _check_numfmt(cases, programs.run_numfmt_format(cases)) == 3000
    texts = programs.numfmt_parse_cases(78, 1500)
    for text, output in zip(texts, programs.run_numfmt_parse(texts), strict=True):
        assert parse(text) == int(output), text
