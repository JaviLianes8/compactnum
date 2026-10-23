"""Limits: every text format writes reads back, bounded messages, quick refusals."""

from __future__ import annotations

import time
from collections.abc import Callable
from decimal import Context, Decimal
from fractions import Fraction

import pytest
import reference

from compactnum import CompactError, format, parse, parse_decimal
from compactnum._cli import main
from compactnum._cli_io import bounded

BIG = 10**4300 - 1
EDGES: list[tuple[object, dict[str, object]]] = [
    (0.5, {"precision": 4300, "trim_zeros": False}),
    (1234, {"precision": 4300, "trim_zeros": False}),
    (Decimal("0." + "3" * 4400), {"precision": 4300}),
    (BIG, {"precision": 4300, "trim_zeros": False}),
    (BIG, {"precision": 4300, "base": 1024, "trim_zeros": False}),
    (-BIG, {"precision": 4300, "base": 1024, "style": "long", "trim_zeros": False}),
    (10**4299, {"precision": 40, "trim_zeros": False}),
]


@pytest.mark.parametrize(("value", "options"), EDGES, ids=[f"edge{i}" for i in range(len(EDGES))])
def test_parse_decimal_reads_back_everything_format_writes(
    value: object, options: dict[str, object]
) -> None:
    for unit, separator in (("", "."), ("B", ",")):
        text = format(value, unit=unit, decimal_sep=separator, **options)  # type: ignore[arg-type]
        back = parse_decimal(text, unit=unit, decimal_sep=separator)
        style = str(options.get("style", "short"))
        precision = int(str(options["precision"]))
        base = int(str(options.get("base", 1000)))
        assert Fraction(back) == reference.shown(value, precision=precision, style=style, base=base)


def test_the_longest_output_still_parses() -> None:
    text = format(BIG, base=1024, precision=4300, trim_zeros=False)
    digits = sum(character.isdigit() for character in text)
    assert digits == 8576
    assert parse_decimal(text) == Context(prec=9000).multiply(Decimal(text[:-2]), 2**80)


def test_parser_digit_limit_is_exactly_8600() -> None:
    assert parse_decimal("9" * 8600) == Decimal("9" * 8600)
    half = parse_decimal("9" * 4300 + "." + "5" * 4300 + "Yi")
    assert Fraction(half) == Fraction("9" * 4300 + "." + "5" * 4300) * 2**80
    with pytest.raises(CompactError, match="more than 8600 digits"):
        parse_decimal("9" * 8601)
    with pytest.raises(CompactError, match="more than 8600 digits"):
        parse_decimal("9" * 4300 + "." + "9" * 4301 + "k")


@pytest.mark.parametrize("size", [41, 100_000])
def test_an_unknown_style_message_never_echoes_a_long_style(size: int) -> None:
    with pytest.raises(ValueError) as info:
        format(1, style="y" * size)
    message = str(info.value)
    assert message.startswith("unknown style: that value;") and len(message) < 100
    with pytest.raises(ValueError, match="unknown style: 'yyyy"):
        format(1, style="y" * 40)


@pytest.mark.parametrize("base", [10**40, -(10**40), 10**4000], ids=["40", "-40", "4000"])
def test_an_unknown_base_message_never_echoes_a_huge_base(base: int) -> None:
    with pytest.raises(ValueError) as info:
        format(1, base=base)
    assert str(info.value) == "unknown base: that value; choose 1000 or 1024"
    with pytest.raises(ValueError, match="unknown base: 9999"):
        format(1, base=10**40 - 1)


def test_a_missing_unit_message_cuts_a_huge_unit() -> None:
    with pytest.raises(CompactError) as info:
        parse_decimal("1k", unit="U" * 100_000)
    message = str(info.value)
    assert len(message) < 150 and "(100000 characters)" in message


@pytest.mark.parametrize("call", [parse, parse_decimal])
def test_parsers_validate_the_decimal_separator(call: Callable[..., object]) -> None:
    for separator in ["ab", "", " ", "1", "-", "k"]:
        with pytest.raises(ValueError) as info:
            call("2k", decimal_sep=separator)
        assert type(info.value) is ValueError
    for wrong in [None, 5]:
        with pytest.raises(TypeError):
            call("2k", decimal_sep=wrong)


@pytest.mark.parametrize("unit", [" B", "B ", "\tB\n", " b "])
def test_whitespace_around_the_unit_is_ignored(unit: str) -> None:
    assert parse_decimal("1.5KiB", unit=unit) == Decimal(1536)
    assert parse("1.5 KiB ", unit=unit) == 1536


@pytest.mark.parametrize(
    "value", [10**1_000_000, -(10**1_000_000), 10**300_000], ids=["1e6", "-1e6", "3e5"]
)
def test_a_huge_integer_is_refused_at_once(value: int) -> None:
    start = time.perf_counter()
    with pytest.raises(ValueError, match="more than 4300 integer digits"):
        format(value)
    assert time.perf_counter() - start < 0.5


def _usage_message(capsys: pytest.CaptureFixture[str], style: str) -> str:
    assert main(["format", "1", "--style", style]) == 2
    return capsys.readouterr().err.splitlines()[-1].split(": error: ", 1)[1]


def test_cli_messages_are_cut_at_exactly_300_characters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert bounded("m" * 300) == "m" * 300
    assert bounded("m" * 301) == "m" * 300 + "..."
    extra = len(_usage_message(capsys, "x")) - 1
    whole = _usage_message(capsys, "x" * (300 - extra))
    assert len(whole) == 300 and whole.count("x" * (300 - extra)) == 1
    longer = whole.replace("x" * (300 - extra), "x" * (301 - extra))
    assert _usage_message(capsys, "x" * (301 - extra)) == longer[:300] + "..."
