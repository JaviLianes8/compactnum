"""Parse compact notation such as ``1.2k`` or ``1.5KiB`` back into a number."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from ._scales import MULTIPLIERS, validate_separator


class CompactError(ValueError):
    """Raised when a string is not valid compact notation."""


_PATTERN = re.compile(r"^([+-]?)(\d+(?:\.\d+)?)\s*([a-zA-Z]*)$")


def parse_decimal(text: str, *, unit: str = "", decimal_sep: str = ".") -> Decimal:
    """Parse ``text`` into an exact :class:`~decimal.Decimal`.

    This is the exact counterpart of :func:`parse`: it never loses precision to
    binary floating point, so it is the right choice for very large magnitudes
    or for round-tripping money. The unit is matched case-insensitively.

    Args:
        text: The compact string, for example ``"1.2k"`` or ``"1.5 KiB"``.
        unit: A trailing unit to strip before parsing, mirroring
            :func:`compactnum.format`. ``"B"`` reads ``"1.5KiB"`` as ``1.5Ki``.
        decimal_sep: The single character used as the decimal point in ``text``.

    Returns:
        The exact numeric value as a ``Decimal``.

    Raises:
        CompactError: If ``text`` is not a string or not clean compact notation.
        ValueError: If ``decimal_sep`` is invalid.

    Examples:
        >>> parse_decimal("1.5KiB", unit="B")
        Decimal('1536')
        >>> parse_decimal("1,5k", decimal_sep=",")
        Decimal('1500')
    """
    if not isinstance(text, str):
        raise CompactError(f"expected a string, got {type(text).__name__}")
    validate_separator(decimal_sep)

    body = text.strip()
    if unit:
        if not body.lower().endswith(unit.lower()):
            raise CompactError(f"missing expected unit {unit!r}: {text!r}")
        body = body[: len(body) - len(unit)].strip()
    if decimal_sep != ".":
        if "." in body:
            raise CompactError(f"unexpected '.' for decimal_sep {decimal_sep!r}: {text!r}")
        body = body.replace(decimal_sep, ".")

    match = _PATTERN.match(body)
    if match is None:
        raise CompactError(f"not compact notation: {text!r}")

    sign, digits, suffix = match.groups()
    factor = MULTIPLIERS.get(suffix.lower())
    if factor is None:
        raise CompactError(f"unknown unit: {suffix!r}")

    try:
        return Decimal(sign + digits) * factor
    except InvalidOperation:  # pragma: no cover - the pattern already guards this
        raise CompactError(f"not a number: {text!r}") from None


def parse(text: str, *, unit: str = "", decimal_sep: str = ".") -> int | float:
    """Parse ``text`` into a number, inverting :func:`compactnum.format`.

    An integral result is returned as ``int``, otherwise as ``float``. For exact
    arithmetic without float rounding, use :func:`parse_decimal`.

    Args:
        text: The compact string, for example ``"1.2k"`` or ``"1.5 thousand"``.
        unit: A trailing unit to strip before parsing, mirroring
            :func:`compactnum.format`.
        decimal_sep: The single character used as the decimal point in ``text``.

    Returns:
        ``int`` when the value is whole, otherwise ``float``.

    Raises:
        CompactError: If ``text`` is not a string or not clean compact notation.
        ValueError: If ``decimal_sep`` is invalid.

    Examples:
        >>> parse("1.2k")
        1200
        >>> parse("3.5M")
        3500000
        >>> parse("1.2 thousand")
        1200
    """
    value = parse_decimal(text, unit=unit, decimal_sep=decimal_sep)
    if value == value.to_integral_value():
        return int(value)
    return float(value)
