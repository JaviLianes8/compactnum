"""Render a number as compact notation such as ``1.2k``, ``3.5M`` or ``1.5KiB``."""

from __future__ import annotations

from decimal import (
    MAX_EMAX,
    MIN_EMIN,
    ROUND_HALF_UP,
    Context,
    Decimal,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
)
from typing import SupportsFloat, SupportsIndex

from ._scales import (
    MAX_DIGITS,
    check_bool,
    check_integer,
    check_text,
    format_entries,
    validate_base,
    validate_separator,
    validate_style,
)
from ._value import coerce


def format(
    value: SupportsFloat | SupportsIndex,
    *,
    precision: int = 1,
    style: str = "short",
    base: int = 1000,
    unit: str = "",
    trim_zeros: bool = True,
    decimal_sep: str = ".",
) -> str:
    """Format ``value`` as compact notation.

    Args:
        value: The number to render: an ``int`` or other integer (a NumPy
            integer, say) and a :class:`~decimal.Decimal` are read exactly, a
            ``float`` as its shortest ``repr`` (so ``1.05`` rounds like the
            decimal ``1.05``), and any other real number (a
            :class:`~fractions.Fraction`, a NumPy float) through ``float()``.
            Any other object with ``__index__`` is read exactly through it,
            and one with only ``__float__`` through ``float()``, as the
            annotation promises. It must be finite and have at most 4300
            integer digits.
        precision: Decimals kept in the mantissa, from ``0`` to ``4300``.
        style: ``"short"`` for short-scale letters (``k M B T Qa Qi Sx Sp
            Oc No``), ``"metric"`` for SI prefixes (``k M G T P E Z Y R Q``),
            or ``"long"`` for words (``thousand`` to ``nonillion``). ``"si"``
            is the 0.x name of ``"short"``, kept so old code runs.
        base: ``1000`` for decimal magnitudes or ``1024`` for binary (IEC)
            magnitudes (``Ki`` to ``Yi``, and ``kibi`` to ``yobi`` under ``"long"``).
        unit: Text appended exactly as given after the suffix, for example
            ``"B"`` to produce ``"1.5KiB"``.
        trim_zeros: Drop trailing fractional zeros when ``True``.
        decimal_sep: Single character used as the decimal point in the output.

    Returns:
        The compact string. Rounding is half-up (ties away from zero) and
        carries across scales, so ``999_999`` becomes ``"1M"``. A value that
        rounds to zero has no minus sign. The result is lossy by design;
        :func:`compactnum.parse_decimal` reads back exactly the quantity shown,
        whatever the arguments.
        Values past the largest suffix keep that suffix with a bigger mantissa.

    Raises:
        TypeError: If ``value`` is not a real number (``bool`` and NumPy
            booleans included) or its ``__float__`` refuses, an
            integer argument is not an integer, ``trim_zeros`` is not a ``bool``,
            or a text argument is not a ``str``.
        ValueError: If ``value`` is not finite or too large, ``precision`` is
            out of range, or ``style``, ``base`` or ``decimal_sep`` is invalid.

    Examples:
        >>> format(1200)
        '1.2k'
        >>> format(1536, base=1024, unit="B")
        '1.5KiB'
        >>> format(2_000_000, style="long")
        '2 million'
        >>> format(-999_999, style="metric")
        '-1M'
    """
    number = coerce(value)
    digits = check_integer("precision", precision)
    if not 0 <= digits <= MAX_DIGITS:
        raise ValueError(f"precision must be between 0 and {MAX_DIGITS}")
    style = validate_style(style)
    base = validate_base(base)
    unit = check_text("unit", unit)
    trim = check_bool("trim_zeros", trim_zeros)
    decimal_sep = validate_separator(decimal_sep)

    magnitude = number.copy_abs()
    size = len(magnitude.as_tuple().digits) + max(magnitude.adjusted(), 0) + digits + 100
    exact = Context(
        prec=size,
        rounding=ROUND_HALF_UP,
        Emax=MAX_EMAX,
        Emin=MIN_EMIN,
        traps=[InvalidOperation, DivisionByZero, Overflow, Inexact],
    )
    rounding = exact.copy()
    rounding.traps[Inexact] = False
    quantum = Decimal((0, (1,), -digits))
    entries = format_entries(base, style)

    def scaled(factor: Decimal) -> Decimal:
        return exact.divide(magnitude, factor).quantize(quantum, context=rounding)

    factor, suffix = _choose(magnitude, entries)
    mantissa = scaled(factor)
    # Rounding can push the mantissa onto the next scale (999.95k becomes 1M).
    while mantissa >= base:
        nxt = _next(factor, entries)
        if nxt is None:
            break
        factor, suffix = nxt
        mantissa = scaled(factor)

    sign = "-" if number < 0 and mantissa != 0 else ""
    gap = " " if style == "long" and suffix else ""
    body = _render(mantissa, trim, decimal_sep)
    return f"{sign}{body}{gap}{suffix}{unit}"


def _choose(magnitude: Decimal, entries: tuple[tuple[Decimal, str], ...]) -> tuple[Decimal, str]:
    factor, suffix = Decimal(1), ""
    for scale_factor, scale_suffix in entries:
        if magnitude >= scale_factor:
            factor, suffix = scale_factor, scale_suffix
    return factor, suffix


def _next(factor: Decimal, entries: tuple[tuple[Decimal, str], ...]) -> tuple[Decimal, str] | None:
    for scale_factor, scale_suffix in entries:
        if scale_factor > factor:
            return scale_factor, scale_suffix
    return None


def _render(mantissa: Decimal, trim_zeros: bool, decimal_sep: str) -> str:
    text = f"{mantissa:f}"
    if trim_zeros and "." in text:
        text = text.rstrip("0").rstrip(".")
    if decimal_sep != "." and "." in text:
        text = text.replace(".", decimal_sep)
    return text
