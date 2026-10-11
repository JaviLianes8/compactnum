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


def test_metric_style_round_trips() -> None:
    assert parse(format(7_200_000, style="metric")) == 7_200_000


def test_binary_round_trips_with_a_unit() -> None:
    text = format(1536, base=1024, unit="B")
    assert text == "1.5KiB"
    assert parse(text, unit="B") == 1536


def test_comma_separator_round_trips() -> None:
    text = format(1500, decimal_sep=",")
    assert text == "1,5k"
    assert parse(text, decimal_sep=",") == 1500


def test_rounding_is_lossy_by_design() -> None:
    # 1234 rounds to "1.2k" at precision 1, which reads back as 1200, not 1234.
    assert format(1234) == "1.2k"
    assert parse(format(1234)) == 1200
    # Higher precision narrows the gap but the contract stays approximate.
    assert parse(format(1234, precision=2)) == 1230
