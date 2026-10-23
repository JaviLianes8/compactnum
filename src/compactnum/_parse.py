"""Parse compact notation such as ``1.2k`` or ``1.5KiB`` back into a number."""

from __future__ import annotations

import math
import re
from decimal import (
    MAX_EMAX,
    MIN_EMIN,
    Context,
    Decimal,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
)

from ._errors import CompactError, excerpt
from ._scales import MAX_DIGITS, MULTIPLIERS, check_text, validate_separator

# ASCII digits only: a sign, digits with an optional fraction, optional
# whitespace, then letters for the suffix.
_PATTERN = re.compile(r"([+-]?)([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)")

# Wide enough for MAX_DIGITS digits times the largest multiplier (2**80, 25 digits),
# so every product is exact; Inexact is trapped to prove it.
_EXACT = Context(
    prec=MAX_DIGITS + 64,
    Emax=MAX_EMAX,
    Emin=MIN_EMIN,
    traps=[InvalidOperation, DivisionByZero, Overflow, Inexact],
)
_ONE = Decimal(1)


def parse_decimal(text: str, *, unit: str = "", decimal_sep: str = ".") -> Decimal:
    """Parse ``text`` into an exact :class:`~decimal.Decimal`.

    This is the exact counterpart of :func:`parse`: it never loses precision to
    binary floating point, so it is the right choice for very large magnitudes
    or for money. Suffixes and the unit are matched case-insensitively, and
    whitespace is allowed around the text and before the suffix.

    Args:
        text: The compact string, for example ``"1.2k"`` or ``"1.5 KiB"``: an
            optional sign, ASCII digits with an optional fraction (at most 4300
            digits in all), and an optional suffix from any style.
        unit: A trailing unit to strip before parsing, mirroring
            :func:`compactnum.format`. ``"B"`` reads ``"1.5KiB"`` as ``1.5Ki``.
            Surrounding whitespace in ``unit`` is ignored.
        decimal_sep: The single character used as the decimal point in ``text``.

    Returns:
        The exact value. A whole value has exponent ``0`` (``Decimal('1536')``),
        any other value has no trailing zeros, and zero is unsigned.

    Raises:
        CompactError: If ``text`` is not compact notation, lacks ``unit``, or
            has more than 4300 digits.
        TypeError: If ``text``, ``unit`` or ``decimal_sep`` is not a ``str``.
        ValueError: If ``decimal_sep`` is not one safe character.

    Examples:
        >>> parse_decimal("1.5KiB", unit="B")
        Decimal('1536')
        >>> parse_decimal("1,5k", decimal_sep=",")
        Decimal('1500')
        >>> parse_decimal("1.2345k")
        Decimal('1234.5')
    """
    check_text("text", text)
    wanted = check_text("unit", unit).strip()
    decimal_sep = validate_separator(decimal_sep)

    body = text.strip()
    if wanted:
        cut = len(body) - len(wanted)
        if cut < 0 or body[cut:].casefold() != wanted.casefold():
            raise CompactError(f"missing the unit {excerpt(wanted)}: {excerpt(text)}")
        body = body[:cut].rstrip()
    if decimal_sep != ".":
        if "." in body:
            raise CompactError(f"unexpected '.' for decimal_sep {decimal_sep!r}: {excerpt(text)}")
        body = body.replace(decimal_sep, ".")

    match = _PATTERN.fullmatch(body)
    if match is None:
        raise CompactError(f"not compact notation: {excerpt(text)}")
    sign, digits, suffix = match.groups()
    if len(digits) - digits.count(".") > MAX_DIGITS:
        raise CompactError(f"more than {MAX_DIGITS} digits: {excerpt(text)}")
    factor = MULTIPLIERS.get(suffix.lower())
    if factor is None:
        raise CompactError(f"unknown suffix: {excerpt(suffix)}")

    value = _EXACT.multiply(Decimal(sign + digits), factor)
    if not value:
        return Decimal(0)
    if value == value.to_integral_value(context=_EXACT):
        return value.quantize(_ONE, context=_EXACT)
    return value.normalize(context=_EXACT)


def parse(text: str, *, unit: str = "", decimal_sep: str = ".") -> int | float:
    """Parse ``text`` into a number, inverting :func:`compactnum.format`.

    A whole result is returned as ``int``, otherwise as the nearest ``float``.
    For exact arithmetic without float rounding, use :func:`parse_decimal`; the
    two accept exactly the same text.

    Args:
        text: The compact string, for example ``"1.2k"`` or ``"1.5 thousand"``.
        unit: A trailing unit to strip before parsing, mirroring
            :func:`compactnum.format`.
        decimal_sep: The single character used as the decimal point in ``text``.

    Returns:
        ``int`` when the value is whole, otherwise ``float``.

    Raises:
        CompactError: If :func:`parse_decimal` rejects ``text``, or a value
            that is not whole is too large for a ``float``.
        TypeError: If ``text``, ``unit`` or ``decimal_sep`` is not a ``str``.
        ValueError: If ``decimal_sep`` is not one safe character.

    Examples:
        >>> parse("1.2k")
        1200
        >>> parse("3.5M")
        3500000
        >>> parse("1.2 thousand")
        1200
        >>> parse("1.2345k")
        1234.5
    """
    value = parse_decimal(text, unit=unit, decimal_sep=decimal_sep)
    if value.as_tuple().exponent == 0:
        return int(value)
    result = float(value)
    if math.isinf(result):
        raise CompactError(f"too large for a float, use parse_decimal: {excerpt(text)}")
    return result
