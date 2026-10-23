"""An independent reference for the tests, written apart from the library.

The suffix tables are typed in by hand here (not imported from the library); the
ground-truth tests check them, and the library's own tables, against the fetched
BIPM, NIST, CLDR and Wikipedia documents. The reference works on exact fractions and
picks a scale by trying them from the smallest up, which is a different route from the
library's (largest scale not above the value, then carry).
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

SHORT = ["", "k", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No"]
METRIC = ["", "k", "M", "G", "T", "P", "E", "Z", "Y", "R", "Q"]
WORDS = [
    "",
    "thousand",
    "million",
    "billion",
    "trillion",
    "quadrillion",
    "quintillion",
    "sextillion",
    "septillion",
    "octillion",
    "nonillion",
]
IEC = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"]
IEC_WORDS = ["", "kibi", "mebi", "gibi", "tebi", "pebi", "exbi", "zebi", "yobi"]


def suffixes(style: str, base: int) -> list[str]:
    """The suffix of scale 0, 1, 2, ... for a style and base."""
    if base == 1024:
        return IEC_WORDS if style == "long" else IEC
    return {"si": SHORT, "short": SHORT, "metric": METRIC, "long": WORDS}[style]


def multipliers() -> dict[str, int]:
    """Every suffix the parser must accept, lower-cased, with its exact multiplier."""
    table: dict[str, int] = {}
    for column in (SHORT, METRIC, WORDS):
        for power, suffix in enumerate(column):
            table[suffix.lower()] = 1000**power
    for column in (IEC, IEC_WORDS):
        for power, suffix in enumerate(column):
            table[suffix.lower()] = 1024**power
    return table


def exact(value: object) -> Fraction:
    """The exact quantity the library promises to read: floats by their shortest repr."""
    if isinstance(value, float):
        return Fraction(repr(value))
    if isinstance(value, Decimal):
        return Fraction(value)
    if isinstance(value, int):
        return Fraction(value)
    return Fraction(repr(float(value)))  # type: ignore[arg-type]


def rounded(value: object, precision: int, base: int, count: int) -> tuple[Fraction, int]:
    """Return (signed shown quantity in units of the scale, scale index)."""
    x = exact(value)
    magnitude = abs(x)
    step = Fraction(1, 10**precision)
    for index in range(count):
        factor = base**index
        units = (magnitude / factor / step + Fraction(1, 2)).__floor__()
        mantissa = units * step
        if mantissa < base or index == count - 1:
            return (-mantissa if x < 0 else mantissa), index
    raise AssertionError("unreachable")


def render(
    value: object,
    *,
    precision: int = 1,
    style: str = "si",
    base: int = 1000,
    unit: str = "",
    trim_zeros: bool = True,
    decimal_sep: str = ".",
) -> str:
    """What ``compactnum.format`` must return, computed independently."""
    names = suffixes(style, base)
    mantissa, index = rounded(value, precision, base, len(names))
    units = abs(mantissa) * 10**precision
    assert units.denominator == 1
    whole, frac = divmod(int(units), 10**precision)
    text = str(whole)
    if precision:
        digits = str(frac).rjust(precision, "0")
        if trim_zeros:
            digits = digits.rstrip("0")
        if digits:
            text += decimal_sep + digits
    sign = "-" if mantissa < 0 else ""
    gap = " " if style == "long" and names[index] else ""
    return f"{sign}{text}{gap}{names[index]}{unit}"


def shown(value: object, *, precision: int = 1, style: str = "si", base: int = 1000) -> Fraction:
    """The exact quantity that ``format`` shows, suffix applied."""
    names = suffixes(style, base)
    mantissa, index = rounded(value, precision, base, len(names))
    return mantissa * Fraction(base) ** index
