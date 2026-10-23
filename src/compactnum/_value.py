"""Read the value given to ``format`` as an exact, finite ``Decimal``."""

from __future__ import annotations

import numbers
import operator
from decimal import Decimal

from ._errors import type_name
from ._scales import MAX_DIGITS

_INT_LIMIT = 10**MAX_DIGITS


def coerce(value: object) -> Decimal:
    """Return ``value`` as a ``Decimal``, reading integers exactly and floats by ``repr``."""
    if isinstance(value, Decimal):
        number = value
    elif _is_boolean(value):
        raise TypeError(f"value must be a real number, not {type_name(value)}")
    elif isinstance(value, numbers.Integral):
        number = _integer(int(value))
    elif isinstance(value, numbers.Real):
        number = _float(value)
    elif hasattr(type(value), "__index__") or hasattr(type(value), "__float__"):
        number = _protocol(value)
    else:
        raise TypeError(f"value must be a real number, not {type_name(value)}")
    if not number.is_finite():
        raise ValueError("value must be finite")
    if number and number.adjusted() >= MAX_DIGITS:
        raise ValueError(f"value has more than {MAX_DIGITS} integer digits")
    if number.adjusted() < -2 * MAX_DIGITS:
        # Rounds to zero at every precision; an exponent this small could also be
        # outside the range decimal arithmetic accepts.
        return Decimal(0)
    return number


def _is_boolean(value: object) -> bool:
    # A NumPy boolean is no numbers.Real but has __float__; it is refused like bool.
    kind = type(value)
    return isinstance(value, bool) or (
        kind.__module__ == "numpy" and kind.__name__ in ("bool", "bool_")
    )


def _integer(integer: int) -> Decimal:
    if not -_INT_LIMIT < integer < _INT_LIMIT:
        raise ValueError(f"value has more than {MAX_DIGITS} integer digits")
    return Decimal(integer)


def _protocol(value: object) -> Decimal:
    """Read an object that is only ``SupportsIndex`` or ``SupportsFloat``, as annotated."""
    if hasattr(type(value), "__index__"):
        try:
            return _integer(operator.index(value))  # type: ignore[arg-type]
        except TypeError:
            # A NumPy float array has an __index__ that refuses; its __float__ may not.
            if not hasattr(type(value), "__float__"):
                raise TypeError(f"value must be a real number, not {type_name(value)}") from None
    return _float(value)


def _float(value: object) -> Decimal:
    try:
        number = float(value)  # type: ignore[arg-type]
    except OverflowError:
        raise ValueError("value is too large for a float") from None
    except TypeError:
        # An object whose __float__ refuses, such as a NumPy array of many elements.
        raise TypeError(f"value must be a real number, not {type_name(value)}") from None
    return Decimal(repr(number))
