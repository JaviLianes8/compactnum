import pytest

from compactnum import format


def test_formats_each_scale() -> None:
    assert format(1200) == "1.2k"
    assert format(3_500_000) == "3.5M"
    assert format(2_000_000_000) == "2B"
    assert format(1_500_000_000_000) == "1.5T"


def test_small_numbers_keep_their_value() -> None:
    assert format(0) == "0"
    assert format(42) == "42"
    assert format(999) == "999"


def test_precision_controls_the_mantissa() -> None:
    assert format(1234, precision=0) == "1k"
    assert format(1234, precision=2) == "1.23k"
    assert format(1250, precision=3) == "1.25k"


def test_rounds_half_up() -> None:
    assert format(1250) == "1.3k"
    assert format(1849) == "1.8k"


def test_rounding_carries_to_the_next_scale() -> None:
    assert format(999_999) == "1M"
    assert format(999_999_999) == "1B"


def test_negatives_keep_their_sign() -> None:
    assert format(-1200) == "-1.2k"
    assert format(-3_500_000, precision=2) == "-3.5M"


def test_tiny_negative_does_not_render_minus_zero() -> None:
    assert format(-10) == "-10"
    assert format(-4, precision=0) == "-4"


def test_long_style_uses_words_with_a_space() -> None:
    assert format(1200, style="long") == "1.2 thousand"
    assert format(2_000_000, style="long") == "2 million"
    assert format(500, style="long") == "500"


def test_trim_zeros_can_be_disabled() -> None:
    assert format(2000, trim_zeros=False) == "2.0k"
    assert format(500, precision=2, trim_zeros=False) == "500.00"


def test_rejects_negative_precision() -> None:
    with pytest.raises(ValueError):
        format(1000, precision=-1)


def test_rejects_unknown_style() -> None:
    with pytest.raises(ValueError):
        format(1000, style="fancy")
