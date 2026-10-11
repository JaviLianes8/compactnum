import pytest

from compactnum import CompactError, parse


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


def test_parses_long_words_and_spacing() -> None:
    assert parse("1.2 thousand") == 1200
    assert parse("2 million") == 2_000_000
    assert parse("  3B  ") == 3_000_000_000


def test_parses_negatives_and_explicit_sign() -> None:
    assert parse("-1.2k") == -1200
    assert parse("+2M") == 2_000_000


@pytest.mark.parametrize("bad", ["", "abc", "1.2x", "1.2.3", "1,200", "k", "1 2k"])
def test_rejects_invalid_notation(bad: str) -> None:
    with pytest.raises(CompactError):
        parse(bad)


def test_rejects_non_strings() -> None:
    with pytest.raises(CompactError):
        parse(1200)  # type: ignore[arg-type]
