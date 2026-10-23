# compactnum 1.0.0 certification report

The 1.0.0 certification bar applied to compactnum. Nothing was ever published to PyPI
(`https://pypi.org/pypi/compactnum/json` answered 404 on 2026-10-23, and so did the
names `compact-num`, `compact_num` and `compact.num`), so there is no upgrade path to
test; every behaviour change is listed against the 0.2.0 code on `main` (c44a14e).

Progress:
- [x] Branch `release/1.0.0` created from `main` (c44a14e, 0.2.0)
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: BIPM, NIST, CLDR and Wikipedia fetched; ICU and GNU numfmt output (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, wheel e2e, every Python on this PC (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [ ] Independent reviewer (item 16)
- [ ] Five QA lenses (item 19)
- [ ] PR, trace guard, merge and publish (item 17)

## Scorecard (items 1 to 15 and 18)

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed | PASS: the four names of 0.2.0 kept with their signatures and defaults, pinned by `tests/test_contract.py`; every behaviour change in CHANGELOG 1.0.0 |
| 2 | `__all__` exact | PASS: `__all__` and `dir()` both give exactly `CompactError`, `format`, `parse`, `parse_decimal` |
| 3 | Docstrings with runnable examples | PASS: every public name and the package have `>>>` examples, run by `--doctest-modules`; README (10 outputs) and GUIDE (15 outputs) examples and the README command transcript run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests` clean, `py.typed` shipped, `typing.get_type_hints` resolves on every function |
| 5 | Typed, documented, safe errors | PASS: `CompactError` (a `ValueError`) for bad text, `TypeError` for wrong types, `ValueError` for bad options; messages quote at most 40 characters (CLI: 300); GUIDE error table |
| 6 | Contract of every public name | PASS: 189 tests and 5 doctests, plus the 2 opt-in wheel tests (196 in all) |
| 7 | Real ground truth | PASS: five fetched documents with a hash manifest; 3,000 ICU 78.3 and 3,000 GNU numfmt 8.32 outputs captured and compared, plus live runs |
| 8 | Real e2e from the wheel | PASS: wheel installed in a fresh venv, used from an empty folder with `-I`, console script and `python -m` by subprocess; no PyPI release to upgrade from |
| 9 | Seeded fuzz | PASS: 51,000 seeded oracle cases and 66,000 hostile calls per run, timing linear |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t, the sdist suite against the installed wheel, 191 passed each |
| 11 | README, `twine check` | PASS: `twine check --strict` PASSED for wheel and sdist; absolute links tested; certified badge |
| 12 | Dated CHANGELOG | PASS: `## [1.0.0] - 2026-10-22` |
| 13 | pyproject | PASS: 1.0.0, Production/Stable, Python 3.10 to 3.14 classifiers, MIT, Homepage/Source/Issues/Changelog, keywords, `dependencies = []` (tested) |
| 14 | sdist and wheel contents | PASS: listed and asserted by `tests/test_e2e_wheel.py` |
| 15 | Gates exit 0 alone | PASS: see Gates |
| 18 | Contracts bite | PASS: 43 author mutants, 41 killed, 2 equivalent (proven by a differential run) |

## Defects found in 0.2.0

Each reproduced against the 0.2.0 sources: `format` used the caller's `decimal` context,
so 34-digit values lost digits (`123456789.012Sp` for a 33-digit integer) and a context
with `prec=3` raised `InvalidOperation`; `format("1200")` was accepted, `format(True)`,
NaN and infinities raised `decimal.InvalidOperation`, `unit=5` was glued as text;
`parse` read Arabic-Indic digits, accepted any length, returned a wrong `int` for a huge
value that is not whole, and raised `AttributeError` for a non-string unit;
`parse_decimal("1.2k")` was `Decimal('1200.0')` and `"-0k"` gave `Decimal('-0')`;
messages echoed the whole input; values from 10^27 had no suffix (`1000Sp`). Found during
the round: a `Decimal` with an exponent near the arithmetic limit raised
`decimal.Inexact`, now read as zero (93c3bc8).

## API review (item 1)

Kept: `format(value, *, precision=1, style="si", base=1000, unit="", trim_zeros=True,
decimal_sep=".")`, `parse` and `parse_decimal(text, *, unit="", decimal_sep=".")`,
`CompactError`. Changed (CHANGELOG 1.0.0): exact arithmetic independent of the caller's
context; type checks (`TypeError`) and bounds (4300 digits, precision 0 to 4300); ASCII
digits only; normalized `Decimal` results; scales 9 and 10 (`Oc No`, SI `R Q`, the
words); bounded messages; `CompactError` reports the public module; the command reads
values exactly, exits 2 on usage errors with bounded messages, survives a closed pipe and
reports unencodable output. `value` stays typed `float | Decimal`; other real numbers are
accepted at run time through `float()`, as documented.

## Ground truth (item 7)

Fetched on 2026-10-23 by `scripts/fetch_upstream.py` into the ignored `tests/upstream`
folder; `tests/upstream/MANIFEST.json` records URL, revision, size, sha256 and licence,
and the tests check the hash first. The BIPM and NIST pages change their markup on every
request, so their visible text is what is stored and hashed (identical on two machines).

- BIPM SI prefixes: the ten symbols from kilo to quetta are exactly the `metric` column.
- NIST prefixes for binary multiples (kibi to exbi) and Wikipedia "Binary prefix"
  (oldid 1379766883, kibi to quebi): the IEC table up to yobi; robi and quebi are present
  in the source and left out on purpose (`Qi` is the short-scale quintillion).
- Wikipedia "Names of large numbers" (oldid 1378239340): million to nonillion at their
  short-scale powers; `thousand` is hand-written.
- Unicode CLDR 48 English compact formats (cldr-json tag 48.0.0): `K M B T` and the
  words thousand to trillion.
- ICU through Node.js 24.18.0 (ICU 78.3, CLDR 48.0, `Intl.NumberFormat` compact,
  `roundingMode: "halfExpand"`): 3,000 seeded cases captured in
  `tests/fixtures/icu-compact-en.json` and 4,000 fresh cases live, all identical once
  CLDR's `K` is written `k` and ICU's `-0` unsigned.
- GNU coreutils numfmt 8.32 (`--to=iec-i --round=nearest`, `--from=iec-i`): 2,000
  formatted and 1,000 parsed values captured in `tests/fixtures/numfmt-iec.json`, 3,000
  and 1,500 more live, all identical.
- The short-scale letters `Qa Qi Sx Sp Oc No` have no standard; they are labelled as a
  convention in the code, GUIDE and tests.
- An independent reference written in the tests (`tests/reference.py`, exact fractions,
  scales tried from the smallest up) agrees on 12,000 formatted and 9,000 read-back values.

## Fuzz and hostile input (item 9)

`tests/test_oracle.py`: three seeds of 4,000 `format` cases over every option (ties,
values just below a scale, floats, Decimals with exponents from -40 to 40), 3,000
read-backs, 4,000 generated texts through `parse_decimal` and `parse`, 2,000 with units and
separators. `tests/test_hostile.py`: 60,000 random texts raise only `CompactError` with
short messages; 6,000 random `format` argument sets raise only `TypeError`/`ValueError`;
nine 200,000-character shapes under 2 s; parsing linear from 20,000 to 320,000
characters; 4300-digit values at precision 4300; results identical under a caller context
with `prec=1` and every trap set, and with `sys.set_int_max_str_digits(640)`.

## Author mutation round (item 18)

Each mutant applied alone to a fresh clone of b805b23 on Elena's PC (CPython 3.14.2, the
fetched documents present), `__pycache__` purged, the full suite run with `-x` and a 300 s
per-test limit. Baseline: 194 passed, 2 skipped (the opt-in e2e tests). The first runs at
baa71ef and 16dbfb9 left M29, M37 (the old stderr escaping, redundant with Python's own),
M39 and a redundant silencing call in `write` alive: contracts added and the redundant
code removed in 16dbfb9 and b805b23. M07 and M12 are equivalent: a value exactly at a
scale factor rounds to the base and carries, and the integer bound is checked again by
the digit test; 361,059 `format` outputs over every power of 10, 1000 and 1024, their
neighbours and the 4300-digit limits are byte-identical with and without each mutant.

| Id | Mutation | File | Result | Caught by |
| --- | --- | --- | --- | --- |
| M01 | carry only above the base | `_format.py` | killed | `src/compactnum/_format.py::compactnum._format.format` |
| M02 | half-even rounding | `_format.py` | killed | `src/compactnum/__init__.py::compactnum` |
| M03 | minus sign on a rounded zero | `_format.py` | killed | `tests/test_contract.py::test_format_promise_in_one_place` |
| M04 | space after a bare number in long style | `_format.py` | killed | `tests/test_format.py::test_long_style_uses_words_with_a_space` |
| M05 | trim zeros of whole mantissas | `_format.py` | killed | `tests/test_format.py::test_value_limits_are_exact` |
| M06 | floats read as exact binary values | `_format.py` | killed | `tests/test_hostile.py::test_numeric_types_are_read_as_documented` |
| M07 | scale chosen only above its factor | `_format.py` | equivalent | |
| M08 | no upper bound on precision | `_format.py` | killed | `tests/test_format.py::test_integer_options_refuse_bool_and_bounds` |
| M09 | bool accepted as a value | `_format.py` | killed | `tests/test_contract.py::test_wrong_types_raise_type_error_not_compact_error` |
| M10 | no guard for tiny exponents | `_format.py` | killed | `tests/test_hostile.py::test_huge_values_and_precision_format_quickly` |
| M11 | bare decimal point left | `_format.py` | killed | `src/compactnum/_format.py::compactnum._format.format` |
| M12 | lower integer bound off by one | `_format.py` | equivalent | |
| M13 | separator ignored on output | `_format.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M14 | octillion letter swapped | `_scales.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M15 | giga written lower case | `_scales.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M16 | gibi misspelt | `_scales.py` | killed | `tests/test_ground_truth.py::test_binary_scales_are_the_iec_prefixes_up_to_yobi` |
| M17 | IEC prefixes parsed as decimal | `_scales.py` | killed | `src/compactnum/_parse.py::compactnum._parse.parse_decimal` |
| M18 | sign accepted as separator | `_scales.py` | killed | `tests/test_format.py::test_rejects_unsafe_decimal_separators` |
| M19 | bool accepted as an integer option | `_scales.py` | killed | `tests/test_format.py::test_integer_options_refuse_bool_and_bounds` |
| M20 | short alias mapped to metric | `_scales.py` | killed | `tests/test_format.py::test_short_style_is_an_alias_of_si` |
| M21 | digit accepted as separator | `_scales.py` | killed | `tests/test_format.py::test_rejects_unsafe_decimal_separators` |
| M22 | non-ASCII digits accepted | `_parse.py` | killed | `tests/test_parse.py::test_explicit_plus_sign_and_ascii_digits_only` |
| M23 | plus sign refused | `_parse.py` | killed | `tests/test_oracle.py::test_parse_decimal_is_exact_and_normalized` |
| M24 | digit limit off by one | `_parse.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M25 | space before the unit refused | `_parse.py` | killed | `tests/test_oracle.py::test_units_and_separators_round_trip` |
| M26 | point accepted with another separator | `_parse.py` | killed | `tests/test_parse.py::test_custom_decimal_separator` |
| M27 | whole values keep their exponent | `_parse.py` | killed | `src/compactnum/__init__.py::compactnum` |
| M28 | signed zero returned | `_parse.py` | killed | `tests/test_contract.py::test_parse_promise_in_one_place` |
| M29 | infinite float returned | `_parse.py` | killed | `tests/test_parse.py::test_parse_refuses_a_fraction_too_large_for_a_float` |
| M30 | suffixes case-sensitive | `_parse.py` | killed | `src/compactnum/_parse.py::compactnum._parse.parse` |
| M31 | unit case-sensitive | `_parse.py` | killed | `tests/test_contract.py::test_parse_promise_in_one_place` |
| M32 | longer excerpts | `_errors.py` | killed | `tests/test_hostile.py::test_huge_text_is_handled_quickly_with_short_messages` |
| M33 | excerpt boundary off by one | `_errors.py` | killed | `tests/test_parse.py::test_messages_quote_at_most_forty_characters` |
| M34 | data errors exit 2 | `_cli.py` | killed | `tests/test_cli.py::test_rejected_values_exit_one_with_a_short_message` |
| M35 | whole values printed as floats | `_cli.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M36 | unbounded messages | `_cli_io.py` | killed | `tests/test_cli.py::test_usage_errors_exit_two_with_a_bounded_message` |
| M37 | usage errors unbounded | `_cli_io.py` | killed | `tests/test_cli.py::test_usage_errors_exit_two_with_a_bounded_message` |
| M38 | one decimal too many | `_format.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M39 | unit type unchecked | `_format.py` | killed | `tests/test_format.py::test_text_options_must_be_strings` |
| M40 | `--no-trim` inverted | `_cli.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M42 | integers read through float | `_format.py` | killed | `tests/test_format.py::test_value_limits_are_exact` |
| M43 | surrounding whitespace refused | `_parse.py` | killed | `tests/test_contract.py::test_parse_promise_in_one_place` |
| M44 | yobi missing | `_scales.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

From a fresh clone on this PC (first at 3fc76f8, final run in the last section):
`python -m build`, `twine check
--strict` PASSED for both files. Wheel: the eight modules, `py.typed`, LICENSE, metadata
with Production/Stable, `Requires-Python: >=3.10` and only `dev` extras. Sdist: sources,
tests with both fixtures and the manifest, README, GUIDE, CHANGELOG, CONTRIBUTING,
scripts; no fetched documents, process notes or caches. Every interpreter here from
`requires-python` up got a fresh venv with the built wheel, and the sdist's suite ran with
`src` removed, `COMPACTNUM_E2E=1` (wheel contents, install in another venv, eight CLI
cases through the console script and `python -m`): CPython 3.10.19, 3.11.5, 3.12.12,
3.13.2, 3.14.2 and 3.14.2 free-threaded, 191 passed each at c9342bb (176 at 3fc76f8).
3.8 and 3.9 are below `requires-python`.

## Gates (item 15)

At c9342bb (the code of b805b23) from a fresh clone on this PC, with the fetched documents,
Node.js and GNU numfmt present, each command alone: `ruff format --check .`,
`ruff check .`, `mypy --strict src`, `mypy --strict src tests` and `pytest` with
`COMPACTNUM_E2E=1` (196 passed, no skips) all exit 0; `twine check --strict` PASSED for
the wheel and the sdist built from that clone.
