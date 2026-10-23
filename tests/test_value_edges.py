"""Edge cases of the value check: text-like subclasses, foreign names, errors passed on."""

from __future__ import annotations

import pytest

from compactnum import format


class FloatBytes(bytes):
    """Bytes that also have ``__float__``."""

    def __float__(self) -> float:
        return 1500.0


class FloatByteArray(bytearray):
    """A bytearray that also has ``__float__``."""

    def __float__(self) -> float:
        return 1500.0


class RefusingFloat:
    """An object whose own ``__float__`` raises a ValueError of its own."""

    def __float__(self) -> float:
        raise ValueError("no reading yet")


class RefusingIndex:
    """An object whose own ``__index__`` raises a ValueError of its own."""

    def __index__(self) -> int:
        raise ValueError("no reading yet")


@pytest.mark.parametrize(
    "value", [FloatBytes(b"x"), FloatByteArray(b"x")], ids=["bytes", "bytearray"]
)
def test_bytes_subclasses_with_float_are_refused(value: object) -> None:
    name = type(value).__name__
    with pytest.raises(TypeError, match=rf"^value must be a real number, not .*\.{name}$"):
        format(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("name", ["bool", "bool_"])
def test_only_numpy_booleans_are_refused_by_name(name: str) -> None:
    stand_in = type(name, (), {"__module__": "mylib", "__index__": lambda self: 1200})
    assert format(stand_in()) == "1.2k"


@pytest.mark.parametrize("value", [RefusingFloat(), RefusingIndex()], ids=["float", "index"])
def test_a_value_error_from_the_values_own_protocol_reaches_the_caller_unchanged(
    value: object,
) -> None:
    with pytest.raises(ValueError, match=r"^no reading yet$"):
        format(value)  # type: ignore[arg-type]
