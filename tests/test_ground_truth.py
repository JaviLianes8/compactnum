"""The suffix tables against the fetched documents that define them.

Sources (URL, revision, fetch date and sha256 in tests/upstream/MANIFEST.json):
BIPM SI prefixes, NIST prefixes for binary multiples, Wikipedia "Binary prefix" (for
zebi, yobi and the 2025 robi and quebi), Wikipedia "Names of large numbers" (short-scale
words) and Unicode CLDR 48 English compact formats. The short-scale letters beyond
``T`` (``Qa Qi Sx Sp Oc No``) are a common convention with no standard behind them;
they are hand-written and only checked for consistency.
"""

from __future__ import annotations

import json
import re

import reference
from sources import upstream_text

from compactnum import format, parse
from compactnum._scales import BINARY_SCALES, DECIMAL_SCALES


def _bipm() -> dict[int, tuple[str, str]]:
    text = upstream_text("bipm-si-prefixes.txt")
    table = text.split("Name Symbol Multiplying factor", 1)[1].split("hecto", 1)[0]
    rows = re.findall(r"([a-z]+) ([A-Za-z]) 10 (\d+)", table)
    return {int(power): (name, symbol) for name, symbol, power in rows}


def test_bipm_lists_the_ten_prefixes_from_kilo_to_quetta() -> None:
    prefixes = _bipm()
    assert sorted(prefixes) == list(range(3, 31, 3))
    assert prefixes[3] == ("kilo", "k") and prefixes[30] == ("quetta", "Q")


def test_metric_style_uses_exactly_the_bipm_symbols() -> None:
    prefixes = _bipm()
    assert {power: metric for power, _, metric, _ in DECIMAL_SCALES} == {
        power: symbol for power, (_, symbol) in prefixes.items()
    }
    assert reference.METRIC[1:] == [prefixes[power][1] for power in sorted(prefixes)]
    for power, (_, symbol) in prefixes.items():
        assert format(10**power, style="metric") == f"1{symbol}"
        assert format(-25 * 10**power // 10, style="metric", unit="m") == f"-2.5{symbol}m"
        assert parse(f"1{symbol}") == 10**power


def _iec_rows() -> dict[int, tuple[str, str]]:
    wiki = upstream_text("wikipedia-binary-prefix.wiki")
    rows = re.findall(r"\|-[^\n]*\n\| ([a-z]+)\n\| ([A-Z]i)\n\| 2<sup>(\d+)</sup>", wiki)
    return {int(power): (name, symbol) for name, symbol, power in rows}


def test_nist_and_wikipedia_agree_on_the_binary_prefixes() -> None:
    nist = upstream_text("nist-binary-prefixes.txt")
    rows = re.findall(r"2 (\d+) ([a-z]+bi) ([A-Z]i) ", nist)
    from_nist = {int(power): (name, symbol) for power, name, symbol in rows}
    assert sorted(from_nist) == [10, 20, 30, 40, 50, 60]
    wiki = _iec_rows()
    assert sorted(wiki) == list(range(10, 101, 10))
    assert all(wiki[power] == pair for power, pair in from_nist.items())


def test_binary_scales_are_the_iec_prefixes_up_to_yobi() -> None:
    wiki = _iec_rows()
    assert {power: (name, prefix) for power, prefix, name in BINARY_SCALES} == {
        power: pair for power, pair in wiki.items() if power <= 80
    }
    assert reference.IEC[1:] == [wiki[power][1] for power in range(10, 81, 10)]
    assert reference.IEC_WORDS[1:] == [wiki[power][0] for power in range(10, 81, 10)]
    for power, (name, symbol) in wiki.items():
        if power > 80:
            continue
        assert format(2**power, base=1024) == f"1{symbol}"
        assert format(3 * 2**power, base=1024, style="long") == f"3 {name}"
        assert parse(f"1.5{symbol}B", unit="B") == 3 * 2 ** (power - 1)
        assert parse(f"2 {name}") == 2 ** (power + 1)


def test_robi_and_quebi_are_left_out_because_qi_is_taken() -> None:
    wiki = _iec_rows()
    assert wiki[90] == ("robi", "Ri") and wiki[100] == ("quebi", "Qi")
    assert parse("1Qi") == 10**18  # the short-scale quintillion, not 2**100
    assert format(2**100, base=1024) == "1048576Yi"


def _short_scale_words() -> dict[int, str]:
    wiki = upstream_text("wikipedia-names-of-large-numbers.wiki")
    pattern = r"\| (\d+) \|\| (?:\[\[)?([a-z]+illion)(?:\]\])?\n\| 10<sup>(\d+)</sup> \|\|"
    rows = re.findall(pattern, wiki)
    return {int(short): name for _, name, short in rows}


def test_words_follow_the_short_scale_names() -> None:
    words = _short_scale_words()
    assert words[6] == "million" and words[30] == "nonillion"
    library = {power: word for power, _, _, word in DECIMAL_SCALES}
    assert library.pop(3) == "thousand"  # 10**3 is not an -illion; hand-written
    assert library == {power: words[power] for power in range(6, 31, 3)}
    for power, word in library.items():
        assert format(7 * 10**power, style="long") == f"7 {word}"
        assert parse(f"7.5 {word.upper()}") == 75 * 10 ** (power - 1)


def _cldr_compact(width: str) -> dict[int, str]:
    data = json.loads(upstream_text("cldr-48-en-numbers.json"))
    formats = data["main"]["en"]["numbers"]["decimalFormats-numberSystem-latn"]
    patterns = formats[width]["decimalFormat"]
    found: dict[int, str] = {}
    for key, pattern in patterns.items():
        magnitude, count = key.split("-count-")
        if count == "other" and pattern.startswith("0") and not pattern.startswith("00"):
            found[len(magnitude) - 1] = pattern.lstrip("0").strip()
    return found


def test_cldr_english_compact_suffixes_match_the_short_scale() -> None:
    short, long = _cldr_compact("short"), _cldr_compact("long")
    assert short == {3: "K", 6: "M", 9: "B", 12: "T"}
    assert long == {3: "thousand", 6: "million", 9: "billion", 12: "trillion"}
    for power, letter in short.items():
        # CLDR writes K; compactnum writes the SI lower-case k and reads both.
        assert format(10**power).lower() == f"1{letter}".lower()
        assert parse(f"1.5{letter}") == 15 * 10 ** (power - 1)
        assert format(10**power, style="long") == f"1 {long[power]}"
