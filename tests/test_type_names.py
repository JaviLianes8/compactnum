"""Type errors name the type: by module, by qualified name, cut after 80 characters."""

from __future__ import annotations

import pytest

from compactnum import format


class BadIndex:
    def __index__(self) -> int:
        raise TypeError("no")


class Outer:
    class Inner:
        pass


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
