"""Every value type the annotation of ``format`` accepts is read; type errors name the type."""

from __future__ import annotations

import importlib
import importlib.util
from decimal import Decimal
from fractions import Fraction

import pytest

from compactnum import format


class IndexOnly:
    """An integer that is only ``SupportsIndex``: no ``numbers`` registration, no ``__float__``."""

    def __init__(self, number: int) -> None:
        self.number = number

    def __index__(self) -> int:
        return self.number


class FloatOnly:
    """A number that is only ``SupportsFloat``."""

    def __init__(self, number: float) -> None:
        self.number = number

    def __float__(self) -> float:
        return self.number


class BadFloat:
    def __float__(self) -> float:
        raise TypeError("no")


def test_an_index_only_object_is_read_exactly() -> None:
    assert format(IndexOnly(1200)) == "1.2k"
    assert format(IndexOnly(-1536), base=1024) == "-1.5Ki"
    assert format(IndexOnly(10**30 + 1), precision=30) == "1.000000000000000000000000000001No"
    with pytest.raises(ValueError, match="more than 4300 integer digits"):
        format(IndexOnly(10**4300))


def test_a_float_only_object_is_read_through_float() -> None:
    assert format(FloatOnly(1500.0)) == "1.5k"
    assert format(FloatOnly(1.05)) == "1.1"  # the shortest repr, like a float
    with pytest.raises(ValueError, match="finite"):
        format(FloatOnly(float("inf")))
    with pytest.raises(TypeError, match="value must be a real number"):
        format(BadFloat())


def test_values_without_a_number_protocol_are_still_refused() -> None:
    for value in ("1200", b"1200", None, 1 + 0j, [1200], True, False):
        with pytest.raises(TypeError, match="value must be a real number"):
            format(value)  # type: ignore[arg-type]
    assert format(Fraction(3, 2)) == "1.5" and format(Decimal("1.5e3")) == "1.5k"


def test_numpy_values_follow_the_annotation() -> None:
    if importlib.util.find_spec("numpy") is None:
        pytest.skip("numpy is not installed")
    np = importlib.import_module("numpy")
    assert format(np.array(1500.0)) == "1.5k"  # a 0-d array has __float__
    assert format(np.int64(-1200)) == "-1.2k" and format(np.float32(1.5)) == "1.5"
    with pytest.raises(TypeError, match=r"value must be a real number, not numpy\.ndarray$"):
        format(np.array([1500.0, 2.0]))
    with pytest.raises(TypeError, match=r"value must be a real number, not numpy\.bool_?$"):
        format(np.bool_(True))
    with pytest.raises(TypeError, match=r"trim_zeros must be a bool, not numpy\.bool_?$"):
        format(2000, trim_zeros=np.bool_(True))


def test_type_errors_name_foreign_types_by_module() -> None:
    with pytest.raises(TypeError, match=r"not (tests\.)?test_value_types\.BadFloat$"):
        format(BadFloat())
    with pytest.raises(TypeError, match=r"trim_zeros must be a bool, not int$"):
        format(2000, trim_zeros=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"unit must be a str, not fractions\.Fraction$"):
        format(2000, unit=Fraction(1))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"precision must be an integer, not decimal\.Decimal$"):
        format(2000, precision=Decimal(1))  # type: ignore[arg-type]


def test_a_huge_type_name_is_cut_in_the_message() -> None:
    hostile = type("x" * 100_000, (), {})
    with pytest.raises(TypeError) as info:
        format(hostile())
    assert len(str(info.value)) < 200
    with pytest.raises(TypeError) as info:
        format(1, unit=hostile())
    assert len(str(info.value)) < 200
