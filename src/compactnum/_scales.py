"""Canonical magnitude scales shared by formatting and parsing.

Two tables drive the whole library. ``DECIMAL_SCALES`` covers base-1000
magnitudes with three suffix columns: short-scale letters (``k M B T``), true
metric prefixes (``k M G T``) and long words. ``BINARY_SCALES`` covers base-1024
magnitudes with IEC prefixes (``Ki Mi Gi``) and their long names. Keeping both
directions on these tables is what keeps :func:`compactnum.format` and
:func:`compactnum.parse` in sync: format reads the suffixes, parse reads the
multipliers.
"""

from __future__ import annotations

from decimal import Decimal

# Exponent of 10, short-scale letter, metric prefix, long word.
DECIMAL_SCALES: tuple[tuple[int, str, str, str], ...] = (
    (3, "k", "k", "thousand"),
    (6, "M", "M", "million"),
    (9, "B", "G", "billion"),
    (12, "T", "T", "trillion"),
    (15, "Qa", "P", "quadrillion"),
    (18, "Qi", "E", "quintillion"),
    (21, "Sx", "Z", "sextillion"),
    (24, "Sp", "Y", "septillion"),
)

# Exponent of 2, IEC prefix, long IEC word.
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

#: Accepted ``style`` values. ``"si"`` and ``"short"`` are the same short-scale
#: letters; ``"metric"`` is the true SI column; ``"long"`` is the words.
STYLES: tuple[str, ...] = ("si", "short", "metric", "long")

#: Accepted ``base`` values: decimal (1000) and binary (1024).
BASES: tuple[int, ...] = (1000, 1024)


def format_entries(base: int, style: str) -> tuple[tuple[Decimal, str], ...]:
    """Return ``(factor, suffix)`` pairs in ascending order for formatting."""
    if base == 1024:
        return tuple(
            (Decimal(2) ** exp, long if style == "long" else prefix)
            for exp, prefix, long in BINARY_SCALES
        )
    entries: list[tuple[Decimal, str]] = []
    for exp, short, metric, long in DECIMAL_SCALES:
        suffix = {"si": short, "short": short, "metric": metric, "long": long}[style]
        entries.append((Decimal(10) ** exp, suffix))
    return tuple(entries)


def _build_multipliers() -> dict[str, Decimal]:
    table: dict[str, Decimal] = {"": Decimal(1)}
    for exp, short, metric, long in DECIMAL_SCALES:
        factor = Decimal(10) ** exp
        for key in (short, metric, long):
            table[key.lower()] = factor
    for exp, prefix, long in BINARY_SCALES:
        factor = Decimal(2) ** exp
        table[prefix.lower()] = factor
        table[long.lower()] = factor
    return table


#: Lower-cased suffix to multiplier, used by the parser. The empty string maps to
#: ``1`` so a bare number parses with no prefix.
MULTIPLIERS: dict[str, Decimal] = _build_multipliers()


def validate_style(style: str) -> None:
    """Raise :class:`ValueError` if ``style`` is not a known style."""
    if style not in STYLES:
        raise ValueError(f"unknown style: {style!r}; choose from {', '.join(STYLES)}")


def validate_base(base: int) -> None:
    """Raise :class:`ValueError` if ``base`` is not ``1000`` or ``1024``."""
    if base not in BASES:
        raise ValueError(f"unknown base: {base!r}; choose 1000 or 1024")


def validate_separator(decimal_sep: str) -> None:
    """Raise :class:`ValueError` unless ``decimal_sep`` is one safe character."""
    if len(decimal_sep) != 1 or decimal_sep.isdigit() or decimal_sep.isspace():
        raise ValueError("decimal_sep must be a single non-digit, non-space character")
    if decimal_sep.isalpha() or decimal_sep in "+-":
        raise ValueError("decimal_sep must not be a letter or a sign character")
