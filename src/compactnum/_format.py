"""Render a number as compact notation such as ``1.2k``, ``3.5M`` or ``1.5KiB``."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ._scales import format_entries, validate_base, validate_separator, validate_style


def format(
    value: float,
    *,
    precision: int = 1,
    style: str = "si",
    base: int = 1000,
    unit: str = "",
    trim_zeros: bool = True,
    decimal_sep: str = ".",
) -> str:
    """Format ``value`` as compact notation.

    Args:
        value: The number to render. Accepts ``int`` or ``float``.
        precision: Decimals kept in the mantissa. Must be ``>= 0``.
        style: ``"si"`` or its alias ``"short"`` for short-scale letters
            (``k M B T``), ``"metric"`` for true SI prefixes (``k M G T``), or
            ``"long"`` for words (``thousand``, ``million``).
        base: ``1000`` for decimal magnitudes or ``1024`` for binary (IEC)
            magnitudes (``Ki Mi Gi`` and the ``kibi`` words under ``"long"``).
        unit: Optional trailing unit glued to the suffix, for example ``"B"``
            to produce ``"1.5KiB"``.
        trim_zeros: Drop trailing fractional zeros when true.
        decimal_sep: Single character used as the decimal point in the output.

    Returns:
        The compact string. Rounding is half-up and carries across scales, so
        ``999_999`` becomes ``"1M"``. The result is lossy by design; use
        :func:`compactnum.parse` to read a value back approximately or
        :func:`compactnum.parse_decimal` for the exact rendered quantity.

    Raises:
        ValueError: If ``precision`` is negative, or ``style``, ``base`` or
            ``decimal_sep`` is invalid.

    Examples:
        >>> format(1200)
        '1.2k'
        >>> format(1536, base=1024, unit="B")
        '1.5KiB'
        >>> format(2_000_000, style="long")
        '2 million'
    """
    if precision < 0:
        raise ValueError("precision must be non-negative")
    validate_style(style)
    validate_base(base)
    validate_separator(decimal_sep)

    number = Decimal(str(value))
    magnitude = abs(number)
    quantum = Decimal(1).scaleb(-precision)
    entries = format_entries(base, style)

    factor, suffix = _choose(magnitude, entries)
    mantissa = _scaled(magnitude, factor, quantum)
    # Rounding can push the mantissa onto the next scale (999.95k becomes 1M).
    while mantissa >= base:
        nxt = _next(factor, entries)
        if nxt is None:
            break
        factor, suffix = nxt
        mantissa = _scaled(magnitude, factor, quantum)

    sign = "-" if number < 0 and mantissa != 0 else ""
    gap = " " if style == "long" and suffix else ""
    body = _render(mantissa, trim_zeros, decimal_sep)
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


def _scaled(magnitude: Decimal, factor: Decimal, quantum: Decimal) -> Decimal:
    return (magnitude / factor).quantize(quantum, rounding=ROUND_HALF_UP)


def _render(mantissa: Decimal, trim_zeros: bool, decimal_sep: str) -> str:
    text = f"{mantissa:f}"
    if trim_zeros and "." in text:
        text = text.rstrip("0").rstrip(".")
    if decimal_sep != "." and "." in text:
        text = text.replace(".", decimal_sep)
    return text
