import pytest

from compactnum import format, parse


@pytest.mark.parametrize(
    "value", [0, 42, 999, 1200, 3_500_000, 2_000_000_000, -1200, 1_500_000_000_000]
)
def test_parse_inverts_format(value: int) -> None:
    assert parse(format(value, precision=3)) == value


@pytest.mark.parametrize("text", ["1.2k", "3.5M", "-2B", "1.5T", "500"])
def test_format_inverts_parse(text: str) -> None:
    assert format(parse(text), precision=3) == text


def test_long_style_round_trips() -> None:
    assert parse(format(7_200_000, style="long")) == 7_200_000
