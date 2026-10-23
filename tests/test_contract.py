"""The public contract: the names, signatures, types and errors that 1.0.0 promises to keep."""

from __future__ import annotations

import importlib.resources
import inspect
import pickle
import re
import typing
from decimal import Decimal
from pathlib import Path

import pytest

import compactnum
from compactnum import CompactError, format, parse, parse_decimal

ROOT = Path(__file__).resolve().parents[1]

# The public API. This list is the contract: the test below fails if it drifts.
PUBLIC_API = ["CompactError", "format", "parse", "parse_decimal"]

SIGNATURES = {
    "format": "(value: 'float | Decimal', *, precision: 'int' = 1, style: 'str' = 'si', "
    "base: 'int' = 1000, unit: 'str' = '', trim_zeros: 'bool' = True, "
    "decimal_sep: 'str' = '.') -> 'str'",
    "parse": "(text: 'str', *, unit: 'str' = '', decimal_sep: 'str' = '.') -> 'int | float'",
    "parse_decimal": "(text: 'str', *, unit: 'str' = '', decimal_sep: 'str' = '.') -> 'Decimal'",
}


def test_all_lists_exactly_the_public_api() -> None:
    assert compactnum.__all__ == PUBLIC_API


def test_no_other_public_attribute_exists() -> None:
    public = sorted(name for name in dir(compactnum) if not name.startswith("_"))
    assert public == sorted(PUBLIC_API)


def test_every_exported_name_resolves_and_reports_the_public_module() -> None:
    for name in compactnum.__all__:
        assert getattr(compactnum, name).__module__.startswith("compactnum")
    assert CompactError.__module__ == "compactnum"


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_signatures_are_pinned(name: str) -> None:
    assert str(inspect.signature(getattr(compactnum, name))) == SIGNATURES[name]


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_type_hints_resolve(name: str) -> None:
    hints = typing.get_type_hints(getattr(compactnum, name))
    assert "return" in hints


def test_version_is_a_three_part_string_matching_the_metadata() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", compactnum.__version__)
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.findall(r'^version = "(.*)"$', text, flags=re.MULTILINE) == ["1.0.0"]
    assert compactnum.__version__ == "1.0.0"
    assert re.findall(r"^dependencies = (.*)$", text, flags=re.MULTILINE) == ["[]"]


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("compactnum").joinpath("py.typed").is_file()


def test_compact_error_is_a_value_error_that_pickles() -> None:
    assert issubclass(CompactError, ValueError)
    error = pickle.loads(pickle.dumps(CompactError("bad")))
    assert type(error) is CompactError and str(error) == "bad"


def test_format_promise_in_one_place() -> None:
    assert format(1200) == "1.2k"
    assert format(999_999) == "1M"
    assert format(-1250) == "-1.3k"
    assert format(-0.04) == "0"
    assert format(1536, base=1024, unit="B") == "1.5KiB"
    assert format(2_000_000, style="long") == "2 million"
    assert format(1_500_000_000, style="metric") == "1.5G"
    assert format(2000, trim_zeros=False, decimal_sep=",") == "2,0k"
    assert format(Decimal("1234.5"), precision=0) == "1k"
    assert format(10**33) == "1000No"


def test_parse_promise_in_one_place() -> None:
    assert parse("1.2k") == 1200 and type(parse("1.2k")) is int
    assert parse("1.2345k") == 1234.5 and type(parse("1.2345k")) is float
    assert parse(" -1.5 KiB ", unit="b") == -1536
    assert parse("1,5 thousand", decimal_sep=",") == 1500
    assert parse_decimal("1.2345k") == Decimal("1234.5")
    assert parse_decimal("1.20k").as_tuple().exponent == 0
    assert str(parse_decimal("-0.0M")) == "0"


@pytest.mark.parametrize("bad", ["", "abc", "1.2x", "1.2.3", "1,200", "k", "1 2k", ".5k", "1.k"])
def test_bad_text_raises_compact_error_only(bad: str) -> None:
    with pytest.raises(CompactError):
        parse(bad)
    with pytest.raises(CompactError):
        parse_decimal(bad)


def test_wrong_types_raise_type_error_not_compact_error() -> None:
    for call in (
        lambda: parse(12),  # type: ignore[arg-type]
        lambda: parse_decimal(b"1k"),  # type: ignore[arg-type]
        lambda: parse("1k", unit=None),  # type: ignore[arg-type]
        lambda: format("12"),  # type: ignore[arg-type]
        lambda: format(True),
        lambda: format(12, precision=1.0),  # type: ignore[arg-type]
        lambda: format(12, style=None),  # type: ignore[arg-type]
    ):
        with pytest.raises(TypeError) as info:
            call()
        assert not isinstance(info.value, ValueError)
