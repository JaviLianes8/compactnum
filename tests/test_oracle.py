"""Seeded property tests against the independent reference in ``reference.py``."""

from __future__ import annotations

import math
import random
from decimal import Decimal
from fractions import Fraction

import pytest
import reference

from compactnum import format, parse, parse_decimal

SEEDS = [1, 2, 3]
STYLES = ["si", "short", "metric", "long"]
ARABIC_SEPARATOR = chr(0x066B)
MICRO = chr(0x00B5)


def _value(rng: random.Random) -> int | float | Decimal:
    kind = rng.randrange(6)
    sign = -1 if rng.random() < 0.3 else 1
    if kind == 0:
        return sign * rng.randrange(10 ** rng.randint(1, 40))
    if kind == 1:  # just below a scale boundary, where rounding carries
        power = rng.randint(1, 12)
        return int(sign * (1000**power - rng.randint(1, 10 ** rng.randint(0, 3 * power))))
    if kind == 2:  # exact ties at the shown precision
        return Decimal(sign * (rng.randrange(10**6) * 10 + 5)).scaleb(rng.randint(-3, 30))
    if kind == 3:
        return sign * rng.uniform(0, 10 ** rng.randint(0, 30))
    if kind == 4:
        return Decimal(sign * rng.randrange(10 ** rng.randint(1, 30))).scaleb(rng.randint(-40, 40))
    return int(
        sign * 1024 ** rng.randint(0, 9) * rng.randrange(1, 2048) // rng.choice([1, 2, 4, 1024])
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_format_matches_the_reference(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(4000):
        value = _value(rng)
        options = {
            "precision": rng.randint(0, 6),
            "style": rng.choice(STYLES),
            "base": rng.choice([1000, 1024]),
            "unit": rng.choice(["", "B", "/s", " units"]),
            "trim_zeros": rng.random() < 0.5,
            "decimal_sep": rng.choice([".", ",", ARABIC_SEPARATOR]),
        }
        expected = reference.render(value, **options)  # type: ignore[arg-type]
        assert format(value, **options) == expected, (value, options)  # type: ignore[arg-type]


@pytest.mark.parametrize("seed", SEEDS)
def test_the_shown_quantity_reads_back_exactly(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(3000):
        value = _value(rng)
        precision = rng.randint(0, 4)
        style = rng.choice(STYLES)
        base = rng.choice([1000, 1024])
        text = format(value, precision=precision, style=style, base=base, unit="B")
        quantity = reference.shown(value, precision=precision, style=style, base=base)
        assert Fraction(parse_decimal(text, unit="B")) == quantity, (value, text)


def _text(rng: random.Random) -> tuple[str, Fraction]:
    table = reference.multipliers()
    suffix = rng.choice(sorted(table))
    cased = "".join(c.upper() if rng.random() < 0.5 else c for c in suffix)
    whole = str(rng.randrange(10 ** rng.randint(1, 25))).rjust(rng.randint(1, 3), "0")
    fraction = str(rng.randrange(10 ** rng.randint(1, 20))) if rng.random() < 0.6 else ""
    sign = rng.choice(["", "-", "+"])
    number = whole + ("." + fraction if fraction else "")
    gap = rng.choice(["", " ", "\t", "  "]) if suffix else ""
    value = Fraction(number) * table[suffix] * (-1 if sign == "-" else 1)
    return f"{rng.choice(['', ' '])}{sign}{number}{gap}{cased}{rng.choice(['', ' '])}", value


@pytest.mark.parametrize("seed", SEEDS)
def test_parse_decimal_is_exact_and_normalized(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(4000):
        text, expected = _text(rng)
        result = parse_decimal(text)
        assert Fraction(result) == expected, text
        exponent = result.as_tuple().exponent
        if expected.denominator == 1:
            assert exponent == 0, text
            assert result.is_signed() == (expected < 0), text
        else:
            assert isinstance(exponent, int) and exponent < 0
            assert result.as_tuple().digits[-1] != 0, text


@pytest.mark.parametrize("seed", SEEDS)
def test_parse_returns_int_or_the_nearest_float(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(4000):
        text, expected = _text(rng)
        result = parse(text)
        if expected.denominator == 1:
            assert type(result) is int and result == expected, text
        else:
            nearest = float(expected)  # Fraction to float is correctly rounded
            assert type(result) is float and result == nearest, text
            assert not math.isinf(result)


@pytest.mark.parametrize("seed", SEEDS)
def test_units_and_separators_round_trip(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(2000):
        text, expected = _text(rng)
        unit = rng.choice(["B", "bit", "/s", MICRO])
        separator = rng.choice([",", "'", ARABIC_SEPARATOR])
        dressed = text.rstrip() + rng.choice(["", " "]) + unit.upper()
        dressed = dressed.replace(".", separator)
        assert Fraction(parse_decimal(dressed, unit=unit, decimal_sep=separator)) == expected
