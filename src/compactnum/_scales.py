"""Canonical magnitude scales and argument checks shared by formatting and parsing.

Two tables drive the whole library. ``DECIMAL_SCALES`` covers base-1000
magnitudes with three suffix columns: short-scale letters (``k M B T``), SI
prefixes (``k M G T``) and the short-scale words. ``BINARY_SCALES`` covers
base-1024 magnitudes with the IEC prefixes (``Ki Mi Gi``) and their names.
Format reads the suffixes and parse reads the multipliers, so both directions
always agree.
"""

from __future__ import annotations

import operator
from decimal import Decimal

#: Most integer digits of a value to format, and the largest precision. It mirrors
#: CPython's default limit for converting between ``int`` and ``str``.
MAX_DIGITS = 4300

#: Most digits the parser reads. Twice MAX_DIGITS covers the longest number format
#: writes (8576 digits: 4276 integer digits over 2**80, then 4300 decimals), so
#: every result of format reads back.
PARSE_DIGITS = 2 * MAX_DIGITS

# Exponent of 10, short-scale letter, SI prefix, short-scale word.
DECIMAL_SCALES: tuple[tuple[int, str, str, str], ...] = (
    (3, "k", "k", "thousand"),
    (6, "M", "M", "million"),
    (9, "B", "G", "billion"),
    (12, "T", "T", "trillion"),
    (15, "Qa", "P", "quadrillion"),
    (18, "Qi", "E", "quintillion"),
    (21, "Sx", "Z", "sextillion"),
    (24, "Sp", "Y", "septillion"),
    (27, "Oc", "R", "octillion"),
    (30, "No", "Q", "nonillion"),
)

# Exponent of 2, IEC prefix, IEC name. The 2025 prefixes robi (Ri) and quebi (Qi)
# are left out on purpose: "Qi" already reads as the short-scale quintillion.
BINARY_SCALES: tuple[tuple[int, str, str], ...] = (
    (10, "Ki", "kibi"),
    (20, "Mi", "mebi"),
    (30, "Gi", "gibi"),
    (40, "Ti", "tebi"),
    (50, "Pi", "pebi"),
    (60, "Ei", "exbi"),
    (70, "Zi", "zebi"),
    (80, "Yi", "yobi"),
)

#: Accepted ``style`` values. ``"short"`` is the short-scale letters, ``"metric"``
#: the SI column and ``"long"`` the words. ``"si"`` is the 0.x name of ``"short"``,
#: kept so old code runs; it is not the SI column.
STYLES: tuple[str, ...] = ("short", "metric", "long", "si")

#: Accepted ``base`` values: decimal (1000) and binary (1024).
BASES: tuple[int, ...] = (1000, 1024)

_COLUMN = {"short": 1, "si": 1, "metric": 2, "long": 3}


def format_entries(base: int, style: str) -> tuple[tuple[Decimal, str], ...]:
    """Return ``(factor, suffix)`` pairs in ascending order for formatting."""
    if base == 1024:
        return tuple(
            (Decimal(2**exp), name if style == "long" else prefix)
            for exp, prefix, name in BINARY_SCALES
        )
    column = _COLUMN[style]
    return tuple((Decimal(10 ** row[0]), str(row[column])) for row in DECIMAL_SCALES)


def _build_multipliers() -> dict[str, Decimal]:
    table: dict[str, Decimal] = {"": Decimal(1)}
    for exp, short, metric, word in DECIMAL_SCALES:
        for key in (short, metric, word):
            table[key.lower()] = Decimal(10**exp)
    for exp, prefix, name in BINARY_SCALES:
        table[prefix.lower()] = Decimal(2**exp)
        table[name.lower()] = Decimal(2**exp)
    return table


#: Lower-cased suffix to multiplier, used by the parser. The empty string maps to
#: ``1`` so a bare number parses with no prefix.
MULTIPLIERS: dict[str, Decimal] = _build_multipliers()


def check_text(name: str, value: object) -> str:
    """Return ``value`` as a plain ``str`` if it is a ``str``, else raise :class:`TypeError`.

    A subclass (a string enum member, say) is read by its characters, never by its
    own ``__str__``, ``__eq__`` or ``__format__``.
    """
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str, not {type(value).__name__}")
    return str.__str__(value)


def check_bool(name: str, value: object) -> bool:
    """Return ``value`` if it is a ``bool``, else raise :class:`TypeError`."""
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a bool, not {type(value).__name__}")
    return value


def check_integer(name: str, value: object) -> int:
    """Return ``value`` as an ``int`` (any ``__index__`` integer but ``bool``)."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        return operator.index(value)  # type: ignore[arg-type]
    except TypeError:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}") from None


def validate_style(style: object) -> str:
    """Return ``style`` if it is a known style, else raise."""
    text = check_text("style", style)
    if text not in STYLES:
        shown = repr(text) if len(text) <= 40 else "that value"
        raise ValueError(f"unknown style: {shown}; choose from {', '.join(STYLES)}")
    return text


def validate_base(base: object) -> int:
    """Return ``base`` if it is ``1000`` or ``1024``, else raise."""
    number = check_integer("base", base)
    if number not in BASES:
        shown = number if abs(number) < 10**40 else "that value"
        raise ValueError(f"unknown base: {shown}; choose 1000 or 1024")
    return number


def validate_separator(decimal_sep: object) -> str:
    """Return ``decimal_sep`` if it is one safe character, else raise."""
    text = check_text("decimal_sep", decimal_sep)
    if len(text) != 1 or text.isdigit() or text.isspace():
        raise ValueError("decimal_sep must be a single non-digit, non-space character")
    if text.isalpha() or text in "+-":
        raise ValueError("decimal_sep must not be a letter or a sign character")
    return text
