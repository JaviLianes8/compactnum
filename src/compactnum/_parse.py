"""Parse compact notation such as ``1.2k`` back into a number."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from ._scales import SCALES


class CompactError(ValueError):
    """Raised when a string is not valid compact notation."""


_EXPONENTS: dict[str, int] = {"": 0}
for _exp, _si, _long in SCALES:
    _EXPONENTS[_si.lower()] = _exp
    _EXPONENTS[_long] = _exp

_PATTERN = re.compile(r"^([+-]?)(\d+(?:\.\d+)?)\s*([a-zA-Z]*)$")


def parse(text: str) -> int | float:
    """Parse ``text`` into a number, inverting :func:`format`.

    The unit is matched case-insensitively. An integral result is returned as
    ``int``, otherwise as ``float``. Anything that is not clean compact notation
    raises :class:`CompactError`.
    """
    if not isinstance(text, str):
        raise CompactError(f"expected a string, got {type(text).__name__}")

    match = _PATTERN.match(text.strip())
    if match is None:
        raise CompactError(f"not compact notation: {text!r}")

    sign, digits, unit = match.groups()
    exp = _EXPONENTS.get(unit.lower())
    if exp is None:
        raise CompactError(f"unknown unit: {unit!r}")

    try:
        value = Decimal(sign + digits) * Decimal(10) ** exp
    except InvalidOperation:  # pragma: no cover - the pattern already guards this
        raise CompactError(f"not a number: {text!r}") from None

    if value == value.to_integral_value():
        return int(value)
    return float(value)
