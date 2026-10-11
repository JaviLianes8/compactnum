"""Render a number as compact notation such as ``1.2k`` or ``3.5M``."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ._scales import SCALES

_STYLE_INDEX = {"si": 0, "long": 1}


def format(
    value: float,
    *,
    precision: int = 1,
    style: str = "si",
    trim_zeros: bool = True,
) -> str:
    """Format ``value`` as compact notation.

    ``precision`` is the number of decimals in the mantissa. ``style`` is
    ``"si"`` for letters (k, M, B, T) or ``"long"`` for words. Trailing zeros
    are dropped unless ``trim_zeros`` is false.
    """
    if precision < 0:
        raise ValueError("precision must be non-negative")
    if style not in _STYLE_INDEX:
        raise ValueError(f"unknown style: {style!r}")

    number = Decimal(str(value))
    magnitude = abs(number)
    quantum = Decimal(1).scaleb(-precision)

    exp, suffix = _choose(magnitude, _STYLE_INDEX[style])
    mantissa = _scaled(magnitude, exp, quantum)
    # Rounding can push the mantissa to the next scale (999.95k becomes 1M).
    while mantissa >= 1000:
        nxt = _next(exp, _STYLE_INDEX[style])
        if nxt is None:
            break
        exp, suffix = nxt
        mantissa = _scaled(magnitude, exp, quantum)

    sign = "-" if number < 0 and mantissa != 0 else ""
    separator = " " if style == "long" and suffix else ""
    return f"{sign}{_render(mantissa, trim_zeros)}{separator}{suffix}"


def _choose(magnitude: Decimal, index: int) -> tuple[int, str]:
    exp, suffix = 0, ""
    for scale_exp, si, long in SCALES:
        if magnitude >= Decimal(10) ** scale_exp:
            exp, suffix = scale_exp, (si, long)[index]
    return exp, suffix


def _next(exp: int, index: int) -> tuple[int, str] | None:
    for scale_exp, si, long in SCALES:
        if scale_exp > exp:
            return scale_exp, (si, long)[index]
    return None


def _scaled(magnitude: Decimal, exp: int, quantum: Decimal) -> Decimal:
    return (magnitude / Decimal(10) ** exp).quantize(quantum, rounding=ROUND_HALF_UP)


def _render(mantissa: Decimal, trim_zeros: bool) -> str:
    text = f"{mantissa:f}"
    if trim_zeros and "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
