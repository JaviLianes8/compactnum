"""Every value type the annotation of ``format`` accepts is read; type errors name the type."""

from __future__ import annotations

import importlib
import importlib.util
import numbers
from decimal import Decimal
from fractions import Fraction
from typing import Any

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


class BadIndex:
    def __index__(self) -> int:
        raise TypeError("no")


class HugeFloat:
    def __float__(self) -> float:
        raise OverflowError("too big")


class ComplexFloat:
    """A complex number that also has ``__float__``, like a NumPy complex scalar."""

    def __float__(self) -> float:
        return 1500.0


numbers.Complex.register(ComplexFloat)


class Outer:
    class Inner:
        pass


def _numpy() -> object:
    if importlib.util.find_spec("numpy") is None:
        pytest.skip("numpy is not installed")
    return importlib.import_module("numpy")


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
    np: Any = _numpy()
    assert format(np.array(1500.0)) == "1.5k"  # a 0-d array has __float__
    assert format(np.int64(-1200)) == "-1.2k" and format(np.float32(1.5)) == "1.5"
    assert format(np.uint64(1536), base=1024) == "1.5Ki"
    assert format(np.array(-1200)) == "-1.2k" and format(np.array(1200, np.uint16)) == "1.2k"
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


def test_a_value_too_large_for_a_float_is_a_value_error() -> None:
    for value in (Fraction(10**400), HugeFloat()):
        with pytest.raises(ValueError, match=r"^value is too large for a float$"):
            format(value)


def test_complex_numbers_with_float_are_refused() -> None:
    with pytest.raises(TypeError, match=r"^value must be a real number, not .*ComplexFloat$"):
        format(ComplexFloat())
    np: Any = _numpy()
    for value, name in (
        (np.complex64(1500), r"numpy\.complex64"),
        (np.complex128(1500 + 5j), r"numpy\.complex128"),
    ):
        with pytest.raises(TypeError, match=rf"^value must be a real number, not {name}$"):
            format(value)


def test_numpy_values_that_hold_no_real_number_are_refused() -> None:
    np: Any = _numpy()
    for value in (
        np.array(True),
        np.array(False),
        np.array(1500 + 0j),
        np.array("1200"),
        np.array(b"1200"),
        np.array(np.timedelta64(5, "s")),
        np.array(Decimal(5), dtype=object),
    ):
        with pytest.raises(TypeError, match=r"^value must be a real number, not numpy\.ndarray$"):
            format(value)
    for value, name in ((np.str_("1200"), "str_"), (np.timedelta64(5, "s"), "timedelta64")):
        with pytest.raises(TypeError, match=rf"^value must be a real number, not numpy\.{name}$"):
            format(value)


@pytest.mark.parametrize("name", ["bool", "bool_"])
def test_numpy_booleans_are_refused_under_either_name(name: str) -> None:
    # NumPy 2 names its boolean type bool, NumPy 1 bool_; both read as a number otherwise.
    stand_in = type(name, (), {"__module__": "numpy", "__index__": lambda self: 1})
    with pytest.raises(TypeError, match=rf"^value must be a real number, not numpy\.{name}$"):
        format(stand_in())


def test_a_refusing_index_names_the_type_by_module() -> None:
    with pytest.raises(TypeError, match=r"BadIndex$") as info:
        format(BadIndex())
    assert str(info.value).endswith(f"not {BadIndex.__module__}.BadIndex")


def test_a_nested_type_is_named_by_its_qualified_name() -> None:
    with pytest.raises(TypeError) as info:
        format(Outer.Inner())  # type: ignore[arg-type]
    assert str(info.value).endswith(f"not {Outer.__module__}.Outer.Inner")


@pytest.mark.parametrize(("length", "shown"), [(80, 80), (81, 80), (109, 80), (79, 79)])
def test_type_names_are_cut_after_80_characters(length: int, shown: int) -> None:
    full = "m." + "x" * (length - 2)
    kind = type("x" * (length - 2), (), {"__module__": "m"})
    cut = full[:shown] + ("..." if length > 80 else "")
    with pytest.raises(TypeError) as info:
        format(kind())
    assert str(info.value) == f"value must be a real number, not {cut}"
