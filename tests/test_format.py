from decimal import Decimal

import pytest

from compactnum import format, parse


def test_formats_each_scale() -> None:
    assert format(1200) == "1.2k"
    assert format(3_500_000) == "3.5M"
    assert format(2_000_000_000) == "2B"
    assert format(1_500_000_000_000) == "1.5T"


def test_reaches_the_largest_short_scale_names() -> None:
    assert format(2_500_000_000_000_000) == "2.5Qa"
    assert format(3_000_000_000_000_000_000) == "3Qi"
    assert format(4_000_000_000_000_000_000_000) == "4Sx"
    assert format(5_000_000_000_000_000_000_000_000) == "5Sp"


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


def test_short_style_is_an_alias_of_si() -> None:
    assert format(2_000_000_000, style="short") == format(2_000_000_000, style="si")


def test_metric_style_uses_true_si_prefixes() -> None:
    assert format(1_500_000_000, style="metric") == "1.5G"
    assert format(1_500_000_000_000_000, style="metric") == "1.5P"
    assert format(2_000_000_000, style="si") == "2B"


def test_binary_base_uses_iec_prefixes() -> None:
    assert format(1536, base=1024) == "1.5Ki"
    assert format(5_368_709_120, base=1024) == "5Gi"
    assert format(1024, base=1024, style="long") == "1 kibi"


def test_unit_is_glued_to_the_suffix() -> None:
    assert format(1536, base=1024, unit="B") == "1.5KiB"
    assert format(2000, unit="B") == "2kB"
    assert format(900, unit="B") == "900B"


def test_trim_zeros_can_be_disabled() -> None:
    assert format(2000, trim_zeros=False) == "2.0k"
    assert format(500, precision=2, trim_zeros=False) == "500.00"


def test_decimal_separator_can_be_a_comma() -> None:
    assert format(1500, decimal_sep=",") == "1,5k"
    assert format(42, decimal_sep=",") == "42"


def test_rejects_negative_precision() -> None:
    with pytest.raises(ValueError):
        format(1000, precision=-1)


def test_rejects_unknown_style() -> None:
    with pytest.raises(ValueError):
        format(1000, style="fancy")


def test_rejects_unknown_base() -> None:
    with pytest.raises(ValueError):
        format(1000, base=2)


def test_rejects_bad_decimal_separator() -> None:
    with pytest.raises(ValueError):
        format(1000, decimal_sep=",,")
    with pytest.raises(ValueError):
        format(1000, decimal_sep="k")


@pytest.mark.parametrize("separator", ["+", "-", "k", "5", " ", "", ",,", chr(0x663)])
def test_rejects_unsafe_decimal_separators(separator: str) -> None:
    with pytest.raises(ValueError):
        format(1500, decimal_sep=separator)
    with pytest.raises(ValueError):
        parse("1.5k", decimal_sep=separator)


def test_integer_options_refuse_bool_and_bounds() -> None:
    with pytest.raises(TypeError):
        format(1200, precision=True)
    with pytest.raises(TypeError):
        format(1200, base=True)
    assert format(1200, precision=4300, trim_zeros=False) == "1.2" + "0" * 4299 + "k"
    with pytest.raises(ValueError, match="between 0 and 4300"):
        format(1200, precision=4301)


def test_value_limits_are_exact() -> None:
    assert format(10**4300 - 1, precision=0) == "1" + "0" * 4270 + "No"
    with pytest.raises(ValueError):
        format(10**4300)
    with pytest.raises(ValueError):
        format(Decimal("1e4300"))
    assert format(Decimal("9.99e4299"), precision=0) == "999" + "0" * 4267 + "No"
