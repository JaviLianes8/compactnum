from decimal import Decimal

import pytest

from compactnum import CompactError, parse, parse_decimal


def test_parses_each_scale() -> None:
    assert parse("1.2k") == 1200
    assert parse("3.5M") == 3_500_000
    assert parse("2B") == 2_000_000_000
    assert parse("1.5T") == 1_500_000_000_000


def test_parses_plain_numbers() -> None:
    assert parse("42") == 42
    assert parse("0") == 0
    assert parse("1200") == 1200


def test_integral_results_are_int_and_others_are_float() -> None:
    assert isinstance(parse("1.2k"), int)
    assert parse("1.2345k") == 1234.5
    assert isinstance(parse("1.2345k"), float)


def test_units_are_case_insensitive() -> None:
    assert parse("1.2K") == 1200
    assert parse("3.5m") == 3_500_000


def test_parses_metric_and_short_scale_letters() -> None:
    assert parse("1.5G") == 1_500_000_000
    assert parse("1.5B") == 1_500_000_000
    assert parse("2Qa") == 2_000_000_000_000_000


def test_parses_binary_prefixes() -> None:
    assert parse("1Ki") == 1024
    assert parse("1.5Ki") == 1536
    assert parse("1mi") == 1024 * 1024
    assert parse("1 gibi") == 1024**3


def test_parses_long_words_and_spacing() -> None:
    assert parse("1.2 thousand") == 1200
    assert parse("2 million") == 2_000_000
    assert parse("  3B  ") == 3_000_000_000


def test_parses_negatives_and_explicit_sign() -> None:
    assert parse("-1.2k") == -1200
    assert parse("+2M") == 2_000_000


def test_unit_is_stripped_before_parsing() -> None:
    assert parse("1.5KiB", unit="B") == 1536
    assert parse("2kB", unit="B") == 2000
    assert parse("900B", unit="B") == 900


def test_missing_expected_unit_is_an_error() -> None:
    with pytest.raises(CompactError):
        parse("1.5Ki", unit="B")


def test_text_that_is_only_the_unit_has_no_number() -> None:
    with pytest.raises(CompactError) as info:
        parse("B", unit="B")
    assert str(info.value) == "not compact notation: 'B'"
    with pytest.raises(CompactError) as info:
        parse_decimal(" kB ", unit="KB")
    assert str(info.value) == "not compact notation: ' kB '"


def test_custom_decimal_separator() -> None:
    assert parse("1,5k", decimal_sep=",") == 1500
    with pytest.raises(CompactError):
        parse("1.5k", decimal_sep=",")


def test_parse_decimal_is_exact() -> None:
    assert parse_decimal("1.2k") == Decimal("1200")
    assert parse_decimal("1.5KiB", unit="B") == Decimal("1536")
    big = parse_decimal("999999999999999999k")
    assert big == Decimal("999999999999999999000")
    assert isinstance(big, Decimal)


@pytest.mark.parametrize("bad", ["", "abc", "1.2x", "1.2.3", "1,200", "k", "1 2k"])
def test_rejects_invalid_notation(bad: str) -> None:
    with pytest.raises(CompactError):
        parse(bad)


def test_rejects_non_strings() -> None:
    with pytest.raises(TypeError):
        parse(1200)  # type: ignore[arg-type]


def test_rejects_bad_decimal_separator() -> None:
    with pytest.raises(ValueError):
        parse("1.2k", decimal_sep="99")


def test_messages_quote_at_most_forty_characters() -> None:
    with pytest.raises(CompactError) as info:
        parse("x" * 40)
    assert str(info.value) == f"not compact notation: {'x' * 40!r}"
    with pytest.raises(CompactError) as info:
        parse("x" * 41)
    assert str(info.value) == f"not compact notation: {'x' * 40!r}... (41 characters)"
    with pytest.raises(CompactError) as info:
        parse("1" + "q" * 500)
    assert str(info.value) == f"unknown suffix: {'q' * 40!r}... (500 characters)"
    with pytest.raises(CompactError) as info:
        parse("1k", unit="B" * 50)
    assert len(str(info.value)) < 120


def test_digit_limit_counts_digits_on_both_sides_of_the_point() -> None:
    whole, fraction = "9" * 4300, "9" * 4300
    assert parse_decimal(whole + "." + fraction) == Decimal(whole + "." + fraction)
    with pytest.raises(CompactError, match="more than 8600 digits"):
        parse_decimal(whole + "." + fraction + "9")


def test_explicit_plus_sign_and_ascii_digits_only() -> None:
    assert parse_decimal("+1.5k") == Decimal(1500)
    odd = [chr(0x661) + chr(0x662) + "k", chr(0xFF11) + "k", "1" + chr(0xB2) + "k"]
    for text in [*odd, "++1k", "+-1k"]:
        with pytest.raises(CompactError):
            parse(text)


def test_parse_refuses_a_fraction_too_large_for_a_float() -> None:
    with pytest.raises(CompactError, match="too large for a float"):
        parse("1" * 300 + ".3Yi")
    assert parse_decimal("1" * 300 + ".3Yi") > 10**320
    assert parse("1" * 300 + ".5Yi") == int("1" * 300) * 2**80 + 2**79
