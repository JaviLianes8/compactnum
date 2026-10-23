"""Hostile, huge and malformed input: typed errors only, bounded messages, linear time."""

from __future__ import annotations

import contextlib
import decimal
import functools
import random
import sys
import time
from collections.abc import Callable
from decimal import Decimal
from fractions import Fraction

import pytest

from compactnum import CompactError, format, parse, parse_decimal

ALPHABET = "0123456789.,+- \t\nkKmMbBgGtTiIqQaAsSxXpPoOnNeEzZyYrR\x00e_" + chr(0xA0) + chr(0x661)


def _hostile(rng: random.Random) -> str:
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 24)))


@pytest.mark.parametrize("seed", [10, 11, 12])
def test_random_text_raises_nothing_but_compact_error(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(20000):
        text = _hostile(rng)
        unit = rng.choice(["", "", "B", "k", " "])
        separator = rng.choice([".", ",", "_"])
        try:
            decimal_value = parse_decimal(text, unit=unit, decimal_sep=separator)
        except CompactError as error:
            assert len(str(error)) < 200
            with pytest.raises(CompactError):
                parse(text, unit=unit, decimal_sep=separator)
            continue
        assert decimal_value.is_finite()
        whole = decimal_value.as_tuple().exponent == 0
        expected = int(decimal_value) if whole else float(decimal_value)
        assert parse(text, unit=unit, decimal_sep=separator) == expected


@pytest.mark.parametrize("seed", [20, 21])
def test_random_format_arguments_raise_only_documented_errors(seed: int) -> None:
    rng = random.Random(seed)
    pool: list[object] = [0, -0.0, 1e308, -1e-308, 5e-324, 10**4299, Decimal("-0E+5"), 2**1000]
    pool += [Decimal("1e4299"), Decimal("9.99e4299"), Fraction(1, 3), Decimal("sNaN"), True]
    pool += [float("inf"), float("nan"), Decimal("Infinity"), "12", None, 10**4300, 1 + 1j]
    for _ in range(3000):
        value = rng.choice(pool)
        precision = rng.choice([0, 1, 5, 40, -1, 4300, 4301])
        style = rng.choice(["si", "long", "metric", "short", "SI", ""])
        base = rng.choice([1000, 1024, 1000.0, 2])
        try:
            text = format(value, precision=precision, style=style, base=base)  # type: ignore[arg-type]
        except (TypeError, ValueError) as error:
            assert not isinstance(error, CompactError)
            assert len(str(error)) < 200
        else:
            assert isinstance(text, str) and text


def _timed(call: Callable[[], object]) -> float:
    start = time.perf_counter()
    with contextlib.suppress(CompactError, ValueError):
        call()
    return time.perf_counter() - start


@pytest.mark.parametrize(
    "shape",
    [
        "9" * 4300,
        "1." + "9" * 4290 + "k",
        " " * 200_000 + "1k",
        "1" + " " * 200_000 + "k",
        "1." * 100_000,
        "9" * 200_000 + "k",
        "1k" + "B" * 200_000,
        "-" * 200_000,
        "1" + "k" * 200_000,
    ],
    ids=lambda shape: f"{shape[:6]!r}x{len(shape)}",
)
def test_huge_text_is_handled_quickly_with_short_messages(shape: str) -> None:
    for unit in ("", "B"):
        assert _timed(functools.partial(parse_decimal, shape, unit=unit)) < 2.0
    try:
        parse(shape)
    except CompactError as error:
        assert len(str(error)) < 200


def test_parse_time_grows_linearly() -> None:
    def cost(size: int) -> float:
        texts = [" " * size + "1" + " " * size + "x", "1" * size + "." + "1" * size]
        return min(
            sum(_timed(functools.partial(parse_decimal, t)) for t in texts) for _ in range(3)
        )

    small, large = cost(20_000), cost(320_000)
    assert large < small * 16 * 4 + 0.05


def test_huge_values_and_precision_format_quickly() -> None:
    assert _timed(lambda: format(10**4299 - 1, precision=4300)) < 2.0
    assert _timed(lambda: format(Decimal("1e-999999"), precision=4300)) < 2.0
    assert _timed(lambda: format(Decimal("7." + "3" * 200_000), precision=3)) < 2.0
    assert format(Decimal("1e-999999")) == "0"
    assert format(Decimal("-5E-1999999999999999997"), precision=4300) == "0"
    assert format(Decimal("1e-8601"), precision=4300) == "0"
    assert format(Decimal("6e-4301"), precision=4300, trim_zeros=False) == "0." + "0" * 4299 + "1"


def test_results_ignore_the_callers_decimal_context_and_digit_limit() -> None:
    cases: list[tuple[int | Decimal, int]] = [
        (10**30 + 5 * 10**28, 1),
        (Decimal("123456789.123456789"), 9),
        (999_950, 1),
    ]
    texts = ["1.23456789012345678901234567890Yi", "-0.5k", "9" * 100 + ".5M"]
    expected = [format(value, precision=p) for value, p in cases]
    parsed = [parse_decimal(text) for text in texts]
    floats = [parse(text) for text in texts]
    huge = parse("9" * 4300 + "Yi")
    limit = sys.get_int_max_str_digits()
    hostile = decimal.Context(prec=1, Emax=5, Emin=-5, rounding=decimal.ROUND_FLOOR)
    hostile.traps = dict.fromkeys(hostile.traps, True)
    try:
        sys.set_int_max_str_digits(640)
        with decimal.localcontext(hostile) as context:
            assert [format(value, precision=p) for value, p in cases] == expected
            assert [parse_decimal(text) for text in texts] == parsed
            assert [parse(text) for text in texts] == floats
            assert format(10**1000)[:4] == "1000"
            assert parse("9" * 4300 + "Yi") == huge
            assert not any(context.flags.values())
    finally:
        sys.set_int_max_str_digits(limit)
    assert huge == int("9" * 4300) * 2**80


def test_numeric_types_are_read_as_documented() -> None:
    assert format(Fraction(1, 3) * 3000) == "1k"
    assert format(Fraction(1, 8) * 10_000, precision=4) == "1.25k"

    class Index(int):
        pass

    assert format(Index(1234), precision=Index(2), base=Index(1024)) == "1.21Ki"
    assert format(1.05, precision=1) == "1.1"  # read as its shortest repr, 1.05
    assert format(2.675, precision=2) == "2.68"
    with pytest.raises(ValueError):
        format(Decimal("sNaN"))
    with pytest.raises(TypeError):
        format(1 + 0j)  # type: ignore[arg-type]
