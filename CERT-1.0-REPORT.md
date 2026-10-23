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
- [x] Independent reviewer (item 16): round 1 (at e061874) scored item 18 FAIL, fixed at
  556c6cf; round 2 (at 0fd443c) scored every item PASS
- [x] Five QA lenses (item 19): round 1 reported 17 findings, all fixed at 1a86ea1; round 2
  re-verified them and reported 9 new ones, all fixed at 7da7243; round 3 re-verified those
  and reported 9 new ones, all fixed at 0a74dcf; round 4 re-verified those and reported 6
  new ones (one found by two lenses), all fixed at ca77018; round 5 re-verified those and
  reported 3 new ones, all fixed at d56401b; round 6 re-verified those and reported 1 new
  one, fixed at 59e2a1c; round 7 re-verified it and reported 1 new one, fixed at 41a9cd2;
  round 8 re-verified it: all five lenses PASS
- [x] PR #3 from `release/1.0.0` opened (item 17); trace guard, merge and publish pending

## Scorecard (items 1 to 15 and 18)

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed | PASS: the four names of 0.2.0 kept with their signatures and defaults, pinned by `tests/test_contract.py`; every behaviour change in CHANGELOG 1.0.0 |
| 2 | `__all__` exact | PASS: `__all__` and `dir()` both give exactly `CompactError`, `format`, `parse`, `parse_decimal` |
| 3 | Docstrings with runnable examples | PASS: every public name and the package have `>>>` examples, run by `--doctest-modules`; README (10 outputs) and GUIDE (15 outputs) examples and the README command transcript run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests` clean, `py.typed` shipped, `typing.get_type_hints` resolves on every function |
| 5 | Typed, documented, safe errors | PASS: `CompactError` (a `ValueError`) for bad text, `TypeError` for wrong types, `ValueError` for bad options; messages quote at most 40 characters (CLI: 300); GUIDE error table |
| 6 | Contract of every public name | PASS: 322 tests and 5 doctests, the 2 opt-in wheel tests among them (327 in all at a823a59) |
| 7 | Real ground truth | PASS: five fetched documents with a hash manifest; 3,000 ICU 78.3 and 3,000 GNU numfmt 8.32 outputs captured and compared, plus live runs |
| 8 | Real e2e from the wheel | PASS: wheel installed in a fresh venv, used from an empty folder with `-I`, console script and `python -m` by subprocess; no PyPI release to upgrade from |
| 9 | Seeded fuzz | PASS: 51,000 seeded oracle cases and 66,000 hostile calls per run, timing linear |
| 10 | Supported Pythons | PASS: the sdist suite against the installed wheel on CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t on this PC (311 passed, 7 upstream skips each, at 3eb194d) and on 3.10.22, 3.11.17, 3.12.15, 3.13.17, 3.14.9 and 3.14.9t (319 passed, 3 skipped each, at 0fd443c) |
| 11 | README, `twine check` | PASS: `twine check --strict` PASSED for wheel and sdist; absolute links tested; certified badge |
| 12 | Dated CHANGELOG | PASS: `## [1.0.0] - 2026-10-22` |
| 13 | pyproject | PASS: 1.0.0, Production/Stable, Python 3.10 to 3.14 classifiers, MIT, Homepage/Source/Issues/Changelog, keywords, `dependencies = []` (tested) |
| 14 | sdist and wheel contents | PASS: listed and asserted by `tests/test_e2e_wheel.py` |
| 15 | Gates exit 0 alone | PASS: see Gates |
| 18 | Contracts bite | PASS: 46 author mutants at 556c6cf, 44 killed, 2 equivalent (proven by a differential run) |

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
reports unencodable output. QA round 1 changed three things: `value` is annotated
`SupportsFloat | SupportsIndex` (every documented value type passes `mypy --strict`), the
default style is named `"short"` (`"si"` stays as its 0.x name: it never wrote SI
prefixes), and `trim_zeros` must be a `bool`. QA round 2 made the runtime read every value
the annotation accepts (objects with only `__index__` or only `__float__`), named foreign
types by module in `TypeError` messages, and let the command read `-inf` and `-nan`.

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

Each mutant applied alone to a fresh clone of 556c6cf on Elena's PC (CPython 3.14.2,
NumPy 2.5.4, the fetched documents present), `__pycache__` purged, the full suite run
with `-x` and a 300 s per-test limit; unmutated, the suite passes there (see the
independent review round 1 below). The first table was proven at b805b23; the code
later moved to `_value.py` and `PARSE_DIGITS`, so M06, M09, M10, M12, M20, M24, M25,
M31, M39 and M42 were ported to the code they now mutate and the whole table was run
again at the release code. The independent review at e061874 found two survivors, now
M45/M46 and M47, killed by the contracts added in 556c6cf. Earlier runs at baa71ef and
16dbfb9 left M29, M37 (the old stderr escaping, redundant with Python's own), M39 and a
redundant silencing call in `write` alive: contracts added and the redundant code
removed in 16dbfb9 and b805b23.

M07 and M12 are equivalent. A value exactly at a scale factor rounds to the base and
carries. An integer of exactly -10**4300 passes the mutated bound in `_integer`, but
`coerce` then checks the digit count and raises the same `ValueError` with the same
message (the reviewer's R04 is this mutant). 182,630 `format` outcomes (every power of
10 up to the 4300-digit limit and its neighbours, both signs, every scale factor of 1000
and 1024 and values just below it, integers given through `__index__` at both limits,
seven option sets) hash the same with and without each mutant, at 556c6cf on Elena's
PC: sha256 d4dafde2c385e5cb2637d1125795770741e8e71c051d63a8e52596c79184a1e1.

| Id | Mutation | File | Result | Caught by |
| --- | --- | --- | --- | --- |
| M01 | carry only above the base | `_format.py` | killed | `src/compactnum/_format.py::compactnum._format.format` |
| M02 | half-even rounding | `_format.py` | killed | `src/compactnum/__init__.py::compactnum` |
| M03 | minus sign on a rounded zero | `_format.py` | killed | `tests/test_contract.py::test_format_promise_in_one_place` |
| M04 | space after a bare number in long style | `_format.py` | killed | `tests/test_format.py::test_long_style_uses_words_with_a_space` |
| M05 | trim zeros of whole mantissas | `_format.py` | killed | `tests/test_format.py::test_value_limits_are_exact` |
| M06 | floats read as exact binary values | `_value.py` | killed | `tests/test_hostile.py::test_numeric_types_are_read_as_documented` |
| M07 | scale chosen only above its factor | `_format.py` | equivalent | |
| M08 | no upper bound on precision | `_format.py` | killed | `tests/test_format.py::test_integer_options_refuse_bool_and_bounds` |
| M09 | bool accepted as a value | `_value.py` | killed | `tests/test_contract.py::test_wrong_types_raise_type_error_not_compact_error` |
| M10 | no guard for tiny exponents | `_value.py` | killed | `tests/test_hostile.py::test_huge_values_and_precision_format_quickly` |
| M11 | bare decimal point left | `_format.py` | killed | `src/compactnum/_format.py::compactnum._format.format` |
| M12 | lower integer bound off by one | `_value.py` | equivalent | |
| M13 | separator ignored on output | `_format.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M14 | octillion letter swapped | `_scales.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M15 | giga written lower case | `_scales.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M16 | gibi misspelt | `_scales.py` | killed | `tests/test_ground_truth.py::test_binary_scales_are_the_iec_prefixes_up_to_yobi` |
| M17 | IEC prefixes parsed as decimal | `_scales.py` | killed | `src/compactnum/_parse.py::compactnum._parse.parse_decimal` |
| M18 | sign accepted as separator | `_scales.py` | killed | `tests/test_format.py::test_rejects_unsafe_decimal_separators` |
| M19 | bool accepted as an integer option | `_scales.py` | killed | `tests/test_format.py::test_integer_options_refuse_bool_and_bounds` |
| M20 | `si` alias mapped to metric | `_scales.py` | killed | `tests/test_format.py::test_short_is_the_default_style_and_si_its_older_name` |
| M21 | digit accepted as separator | `_scales.py` | killed | `tests/test_format.py::test_rejects_unsafe_decimal_separators` |
| M22 | non-ASCII digits accepted | `_parse.py` | killed | `tests/test_parse.py::test_explicit_plus_sign_and_ascii_digits_only` |
| M23 | plus sign refused | `_parse.py` | killed | `tests/test_oracle.py::test_parse_decimal_is_exact_and_normalized` |
| M24 | digit limit off by one | `_parse.py` | killed | `tests/test_limits.py::test_parser_digit_limit_is_exactly_8600` |
| M25 | space before the unit refused | `_parse.py` | killed | `tests/test_oracle.py::test_units_and_separators_round_trip` |
| M26 | point accepted with another separator | `_parse.py` | killed | `tests/test_parse.py::test_custom_decimal_separator` |
| M27 | whole values keep their exponent | `_parse.py` | killed | `src/compactnum/__init__.py::compactnum` |
| M28 | signed zero returned | `_parse.py` | killed | `tests/test_contract.py::test_parse_promise_in_one_place` |
| M29 | infinite float returned | `_parse.py` | killed | `tests/test_parse.py::test_parse_refuses_a_fraction_too_large_for_a_float` |
| M30 | suffixes case-sensitive | `_parse.py` | killed | `src/compactnum/_parse.py::compactnum._parse.parse` |
| M31 | unit case-sensitive | `_parse.py` | killed | `src/compactnum/_parse.py::compactnum._parse.parse_decimal` |
| M32 | longer excerpts | `_errors.py` | killed | `tests/test_hostile.py::test_huge_text_is_handled_quickly_with_short_messages` |
| M33 | excerpt boundary off by one | `_errors.py` | killed | `tests/test_parse.py::test_messages_quote_at_most_forty_characters` |
| M34 | data errors exit 2 | `_cli.py` | killed | `tests/test_cli.py::test_rejected_values_exit_one_with_a_short_message` |
| M35 | whole values printed as floats | `_cli.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M36 | unbounded messages | `_cli_io.py` | killed | `tests/test_cli.py::test_usage_errors_exit_two_with_a_bounded_message` |
| M37 | usage errors unbounded | `_cli_io.py` | killed | `tests/test_cli.py::test_usage_errors_exit_two_with_a_bounded_message` |
| M38 | one decimal too many | `_format.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M39 | unit type unchecked | `_format.py` | killed | `tests/test_format.py::test_text_options_must_be_strings` |
| M40 | `--no-trim` inverted | `_cli.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M42 | integers read through float | `_value.py` | killed | `tests/test_format.py::test_value_limits_are_exact` |
| M43 | surrounding whitespace refused | `_parse.py` | killed | `tests/test_contract.py::test_parse_promise_in_one_place` |
| M44 | yobi missing | `_scales.py` | killed | `tests/test_cli.py::test_prints_the_result_and_exits_zero` |
| M45 | message cut one character late (`> MESSAGE_LIMIT + 1`) | `_cli_io.py` | killed | `tests/test_limits.py::test_cli_messages_are_cut_at_exactly_300_characters` |
| M46 | `MESSAGE_LIMIT = 301` | `_cli_io.py` | killed | `tests/test_limits.py::test_cli_messages_are_cut_at_exactly_300_characters` |
| M47 | unit scan stops one character short | `_parse.py` | killed | `tests/test_parse.py::test_text_that_is_only_the_unit_has_no_number` |

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

Final run at a823a59 (the release code; later commits change only this report), from a
fresh clone of `release/1.0.0` on Elena's PC (CPython 3.14.2, NumPy 2.5.4, the fetched
documents present, every hash matching the manifest), each command alone:
`ruff format --check .` (37 files), `ruff check .`, `mypy --strict src` (9 files),
`mypy --strict src tests` (30 files) and `pytest` (324 passed, 3 skipped: the 2 opt-in
wheel tests and GNU numfmt) all exit 0. `python -m build` exits 0 and
`twine check --strict` PASSED for both files, byte for byte the files of the second
review (wheel sha256 c5a01a51d5cf795e7e125537814fbd8063904e770a6751fe774879d72e804ec2,
sdist sha256 24a881a582db5c27999fc3b0c630abf6bd063b4ba668280ee66267d5d7d2dfd5). The
wheel, installed in a throwaway venv, ran the sdist's suite with `src` removed and
`COMPACTNUM_E2E=1`: `compactnum` imported from the venv's `site-packages` at version
1.0.0, 321 passed, 1 skipped (GNU numfmt).

## QA lenses (item 19)

### Round 1 (reviewed at 4f53276, fixed at 1a86ea1)

Five lenses ran against 4f53276. Lens b (ground truth: 148 table checks, 58,576 ICU,
34,400 numfmt and 276,894 exact-reference comparisons) found only the round-trip limit
that lenses a and c also found; lens d (packaging: build, twine, wheel and sdist e2e on
six interpreters, upgrade from 0.2.0) found only the version-dependent negative values.
Every finding below was fixed; none is disputed.

| Lens | Id | Severity | Finding | Fix |
| --- | --- | --- | --- | --- |
| a | F1 | medium | `value: float \| Decimal` rejected `Fraction` and NumPy values for typed callers | annotated `SupportsFloat \| SupportsIndex`; `tests/test_typing.py` runs `mypy --strict` on a consumer (with NumPy when installed) and checks a `str` is still rejected |
| a | F2 | medium | the default style `"si"` wrote short-scale letters, not SI prefixes | default renamed `"short"`, `"si"` kept as its 0.x name; README, GUIDE, docstring, CLI and CHANGELOG |
| a, b, c | F3, F1, F2 | low | `format` could write up to 8576 digits, `parse_decimal` read at most 4300 | the parser reads 8600 digits; the round trip is tested at the extremes (precision 4300 on 4300-digit values, base 1024, long style, units and separators) against the independent reference |
| a | F4 | low | `parse` docstring said both parsers accept exactly the same text | reworded: same syntax, `parse` also refuses a non-whole value too large for a float |
| a | F5 | low | `trim_zeros` was read by truth value (`"False"` trimmed) | `TypeError` unless it is a `bool`; docstring, GUIDE error table, CHANGELOG |
| a | F6 | low | invalid `--precision` and `--decimal-sep` values exited 1 naming `decimal_sep`; README exit-code line incomplete | both are argparse type checks: exit 2 naming the option; README, GUIDE and help aligned |
| a | F7 | low | CHANGELOG said 0.2.0 raised `AttributeError` for `decimal_sep` | now "for `unit`" (re-checked against c44a14e) |
| a | F8 | low | unit matching failed when case folding changes the length (`SS` and `ß`) | characters are folded one by one from the end (linear, tested with 200,000-character units) |
| c | F1 | medium | `str` subclasses (string enums) were read through their own `__str__`: `KeyError`, wrong separator check, `1.5KiUnit.BYTE` | every text argument is read as `str.__str__(value)`, the plain characters |
| d | F1 | low | `format -1e3` and `parse -1.2k` were usage errors on 3.10 to 3.13 and worked on 3.14 | the 3.14 negative-number rule is set on every parser; in-process and subprocess tests |
| e | E1 to E8 | medium, low | no test bit on: the style and base message limits, the missing-unit excerpt, the parsers' separator check, unit whitespace, the CLI reading values exactly, lost `--help`/`--version` output, the quick refusal of a huge int | one contract test each in `tests/test_limits.py` and `tests/test_cli_options.py` |

Contract tests first: the new tests, run against 4f53276, failed 36 times (typing, string
enums, `trim_zeros`, case folding, the round trip, the digit limit, negative values,
option errors, the signature and the default style). The lens e tests passed there, as
expected: those were missing tests, not wrong behaviour.

Round-1 mutants, each applied alone to a clean clone of 1a86ea1 on Elena's PC (CPython
3.14.2, full suite with `-x`); the baseline passed:

| Id | Mutation | Caught by |
| --- | --- | --- |
| R01 | unknown-style message echoes the style | `tests/test_limits.py::test_an_unknown_style_message_never_echoes_a_long_style` |
| R02 | unknown-base message echoes the base | `tests/test_limits.py::test_an_unknown_base_message_never_echoes_a_huge_base` |
| R03 | missing-unit message echoes the unit | `tests/test_limits.py::test_a_missing_unit_message_cuts_a_huge_unit` |
| R04 | parsers skip the separator check | `tests/test_limits.py::test_parsers_validate_the_decimal_separator` |
| R05 | unit whitespace kept | `tests/test_limits.py::test_whitespace_around_the_unit_is_ignored` |
| R06 | CLI value read through `float` | `tests/test_cli_options.py::test_the_value_is_read_exactly` |
| R07 | lost help or version output exits 0 | `tests/test_cli_options.py::test_lost_output_exits_one` |
| R08 | no quick refusal of a huge int | `tests/test_limits.py::test_a_huge_integer_is_refused_at_once` |
| R09 | value annotation narrowed back | `tests/test_contract.py::test_signatures_are_pinned` (and `tests/test_typing.py`) |
| R10 | default style back to `"si"` | `tests/test_contract.py::test_signatures_are_pinned` |
| R11 | `trim_zeros` read by truth value | `tests/test_text_types.py::test_trim_zeros_must_be_a_bool` |
| R12 | unit folded by `lower()` | `tests/test_text_types.py::test_unit_matching_is_caseless_even_when_casefold_changes_length` |
| R13 | `str` subclasses kept as they are | `tests/test_text_types.py::test_string_enum_members_are_read_by_their_value` |
| R14 | parser digit limit back to 4300 | `tests/test_limits.py::test_parse_decimal_reads_back_everything_format_writes` |
| R15 | argparse negative-number rule left per version | survives on 3.14 (its own rule is the same, so equivalent there); killed on 3.11 and 3.13 by `tests/test_cli_options.py::test_negative_values_need_no_separator_on_any_python` |
| R16 | CLI precision range unchecked | `tests/test_cli_options.py::test_invalid_option_values_are_usage_errors_naming_the_flag` |
| R17 | CLI separator unchecked | `tests/test_cli_options.py::test_invalid_option_values_are_usage_errors_naming_the_flag` |

Gates at 1a86ea1 from a fresh clone of the pushed branch on this PC, with the fetched
documents, Node.js and GNU numfmt present: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, `mypy --strict src tests` and `pytest` (259 passed, 2 opt-in e2e
skipped) each exit 0. With `COMPACTNUM_E2E=1`: 261 passed, no skips, on CPython 3.10.19,
3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded.

### Round 2 (reviewed at 0848be4, fixed at 7da7243)

Lenses a, d and e re-ran every round-1 finding: all fixed (lens e replayed each as a
mutant, all killed). Lens a ran 37 Python probes and 14 CLI calls on 3.11 and 3.13, lens d
the sdist suite against the wheel on six interpreters (247 passed, 9 upstream skips each)
and 40 probes, lens e 40 new mutants. New findings, all fixed; none is disputed:

| Lens | Id | Severity | Finding | Fix |
| --- | --- | --- | --- | --- |
| a | N1 | medium | the annotation `SupportsFloat \| SupportsIndex` accepted objects with only `__index__` or only `__float__` (and NumPy arrays) that raised `TypeError` at run time | `format` reads such an object exactly through `operator.index`, or through `float()`; `bool` and NumPy booleans still refused, a refusing `__float__` is a `TypeError`; new module `_value.py`; `tests/test_value_types.py`, and `tests/test_typing.py` runs the typed consumer with those objects |
| a | N2 | low | `trim_zeros must be a bool, not bool` for a NumPy boolean | every `TypeError` names a type outside the builtins as `module.qualname` (`numpy.bool`), cut at 80 characters |
| d | F2 | low | `format -inf` (and `-Infinity`, `-nan`, `-sNaN`) was a usage error, against the "minus sign on every Python" promise | the negative-value rule also matches those whole words, so they exit 1 as not finite; any other dash and letter stays an option |
| e | E9 | low | no test of the `invalid integer value` wording for `--precision` | pinned |
| e | E10 | low | no test of the `--precision` range message | pinned for -1 and 4301 |
| e | E11 | low | no test of a separator whose `__ne__` lies | `Liar` separator in `tests/test_text_types.py` |
| e | E12 | low | no test that `parse` and `parse_decimal` read `text` by its characters and keep the message bounded | `Liar` text with lying `strip`, `replace` and `__repr__` |
| e | E13 | low | no test that a dash and a letter stays an option | `parse -k`, `format -nancy`, `--unit -B` and others must exit 2 |

Contract tests first: against 0848be4 the new tests failed 13 times (N1, N2 and F2); the
lens e tests passed there, as they pin existing behaviour. Each lens e mutant and six
more for the new code were applied alone to a copy of 7da7243 and run on CPython 3.13.2
with the affected test files; all killed:

| Id | Mutation | Caught by |
| --- | --- | --- |
| E9 | `_precision.__name__` not set | `tests/test_cli_options.py::test_precision_usage_errors_say_what_is_wrong` |
| E10 | `ValueError` for the precision range | `tests/test_cli_options.py::test_precision_usage_errors_say_what_is_wrong` |
| E11 | separator returned as the caller's object | `tests/test_text_types.py::test_a_separator_whose_comparisons_lie_is_read_by_its_characters` |
| E12 | checked text not assigned | `tests/test_text_types.py::test_text_whose_methods_lie_is_read_by_its_characters` |
| E13 | negative-value rule `-\.?\w` | `tests/test_cli_options.py::test_a_dash_and_text_that_is_no_number_stays_an_option` |
| R18 | negative-value rule back to `-\.?\d` | `tests/test_cli_options.py::test_negative_infinities_and_nans_are_values_rejected_as_not_finite` |
| R19 | protocol-only values refused | `tests/test_value_types.py::test_an_index_only_object_is_read_exactly` |
| R20 | `__index__` read through `float()` | `tests/test_value_types.py::test_an_index_only_object_is_read_exactly` |
| R21 | type names without their module | `tests/test_value_types.py::test_numpy_values_follow_the_annotation` |
| R22 | NumPy booleans accepted | `tests/test_value_types.py::test_numpy_values_follow_the_annotation` |
| R23 | huge type names not cut | `tests/test_value_types.py::test_a_huge_type_name_is_cut_in_the_message` |

Gates at 7da7243 on Elena's PC (CPython 3.14.2, NumPy 2.5.4, a clone of the branch):
`ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests`
and `pytest` with `COMPACTNUM_E2E=1` (279 passed, 8 skipped: the fetched documents and
GNU numfmt are not on that PC) each exit 0. The changed CLI, value and text test files
also pass on CPython 3.11.5 and 3.13.2 on this PC.

### Round 3 (reviewed at 6b8ad33, fixed at 0a74dcf)

Lenses a, d and e re-ran every round-2 finding: all fixed (lens e replayed each as a
mutant, all killed). Lens a ran 40 probes (30 in Python, 10 CLI arguments on 3.11 and
3.13), lens d the sdist suite against the wheel on six interpreters (275 passed, 7
upstream skips each) and 40 probes, lens e 38 new mutants, of which 11 survived. New
findings, all fixed; none is disputed:

| Lens | Id | Severity | Finding | Fix |
| --- | --- | --- | --- | --- |
| a | N3 | medium | NumPy complex scalars have `__float__`, so `format(np.complex128(1500 + 5j))` printed `1.5k`, dropping the imaginary part | a `numbers.Complex` that is not `numbers.Real` is refused before `float()` is tried |
| a | N4 | low | `format(np.array(True))` printed `1`: only the NumPy boolean scalar type was refused | any value whose `dtype.kind` is not an integer or float kind is refused, naming `numpy.ndarray`; the same check refuses 0-d string, bytes, timedelta and object arrays and `numpy.str_`, which also read as numbers, and `str` and `bytes` subclasses with `__float__` are refused too; docstring, GUIDE, CHANGELOG |
| d | F3 | low | GUIDE said `--unit -B` works after `--`; no placement of `--` does | GUIDE and `--help` say an option value that starts with a dash takes `=` (`--unit=-B`); subprocess test of `parse 1k-B --unit=-B`, `format 5 --unit=-B` and `parse --unit=-B -- -1k-B` |
| e | E16 | medium | no test of `format`'s `value is too large for a float` | `Fraction(10**400)` and a `__float__` raising `OverflowError` must raise that `ValueError`; GUIDE, docstring and CHANGELOG name the case |
| e | E14 | low | nothing pinned the NumPy 1 boolean name `bool_` | stand-in types named `numpy.bool` and `numpy.bool_` must be refused |
| e | E15 | low | nothing pinned the type name for a refusing `__index__` without `__float__` | `tests/test_type_names.py` asserts the module-qualified name |
| e | E17 | low | no nested type in the tests | `Outer.Inner` must be named by its qualified name |
| e | E18 | low | the 80-character cut was not pinned | exact messages for names of 79, 80, 81 and 109 characters |
| e | E19 | low | `-information` and `-nancy` were only tested with `format`, where a value also exits 2 | `parse` and `format` with `-information`, `-nancy`, `-infk`, `-nanB` and `-k` must exit 2 with `the following arguments are required` |

Contract tests first: against 6b8ad33 the new tests failed in
`test_complex_numbers_with_float_are_refused` and
`test_numpy_values_that_hold_no_real_number_are_refused` (N3 and N4); the lens e and F3
tests passed there, as they pin existing behaviour. Each surviving lens e mutant, adapted
to the new code, and eight more for it were applied alone to a clone of 0a74dcf on
Elena's PC (CPython 3.14.2, NumPy 2.5.4, full suite with `-x`); all killed:

| Id | Mutation | Caught by |
| --- | --- | --- |
| S02 | NumPy boolean names `("bool",)` only | `tests/test_value_types.py::test_numpy_booleans_are_refused_under_either_name[bool_]` |
| S11 | refusing `__index__` named by `__name__` | `tests/test_type_names.py::test_a_refusing_index_names_the_type_by_module` |
| S14 | `OverflowError` not caught | `tests/test_value_types.py::test_a_value_too_large_for_a_float_is_a_value_error` |
| S15 | `TypeError` for a float overflow | `tests/test_value_types.py::test_a_value_too_large_for_a_float_is_a_value_error` |
| S25 | type named by `__name__` | `tests/test_type_names.py::test_a_nested_type_is_named_by_its_qualified_name` |
| S26 | cut at 120 characters | `tests/test_type_names.py::test_type_names_are_cut_after_80_characters[81-80]` |
| S27 | cut at 80 characters or more | `tests/test_type_names.py::test_type_names_are_cut_after_80_characters[80-80]` |
| S28 | cut without `...` | `tests/test_type_names.py::test_type_names_are_cut_after_80_characters[81-80]` |
| S35 | negative-value rule without `$` | `tests/test_cli_options.py::test_a_dash_and_a_word_is_an_option_so_the_value_is_missing` |
| S37 | negative-value rule `inf\w*` | `tests/test_cli_options.py::test_a_dash_and_a_word_is_an_option_so_the_value_is_missing` |
| S38 | negative-value rule `s?nan\w*` | `tests/test_cli_options.py::test_a_dash_and_a_word_is_an_option_so_the_value_is_missing` |
| R24 | complex numbers not refused | `tests/test_value_types.py::test_complex_numbers_with_float_are_refused` |
| R25 | data type not checked | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |
| R26 | boolean data type allowed | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |
| R27 | object data type allowed | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |
| R28 | string data type allowed | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |
| R29 | `str` and `bytes` subclasses not refused | `tests/test_value_types.py::test_values_without_a_number_protocol_are_still_refused` |
| R30 | unsigned data type refused | `tests/test_value_types.py::test_numpy_values_follow_the_annotation` |

R29 survived the first pass (a `str` subclass with `__float__` had no test); the test was
added in 0a74dcf and the whole table above is the rerun.

Gates at 0a74dcf: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
`mypy --strict src tests` exit 0 on this PC (CPython 3.13.2, NumPy 2.5.4). On Elena's PC
(CPython 3.14.2, NumPy 2.5.4, a clone of the branch) `pytest` exits 0 (309 collected),
and so does `pytest` with `COMPACTNUM_E2E=1` (301 passed, 8 skipped: the fetched documents
and GNU numfmt are not on that PC).

### Round 4 (reviewed at b76bff8, fixed at ca77018)

Lenses a, d and e re-ran every round-3 finding: all fixed (lens e replayed each as a
mutant, 12 of 12 killed). Lens a ran 40 probes (30 in Python, 10 CLI arguments on 3.11.5
and 3.13.2), lens d the sdist suite against the wheel on six interpreters (297 passed, 7
upstream skips each) and 35 probes, lens e 24 new mutants, of which 7 survived. New
findings, all fixed; none is disputed:

| Lens | Id | Severity | Finding | Fix |
| --- | --- | --- | --- | --- |
| a, d | N5, F4 | low | on CPython 3.10 and 3.11, `--unit=--` (and `--precision=--`, `--base=--`, `--style=--`, `--decimal-sep=--`) crashed with a `TypeError` traceback, exit 1: argparse on 3.10, 3.11 before 3.11.8 and 3.12 before 3.12.2 drops `--` from an option's values and handed the option an empty list that skipped its checks | the parser reads an option value of exactly `--` as that text and runs the option's own type and choices check on it, as later versions do: `format 1500 --unit=--` prints `1.5k--`, the others exit 2 naming the option; GUIDE and CHANGELOG |
| e | E20 (N12, N13) | medium | no test of NumPy void values, so a denylist of data type kinds or an allowed `V` kind survived | `np.void(b"12")` and `np.array(np.void(b"12"))` must be refused, naming `numpy.void` and `numpy.ndarray` |
| e | E21 (N02, N03) | low | the `bytes` and `bytearray` entries of the refused types were never exercised | `tests/test_value_edges.py`: `bytes` and `bytearray` subclasses with `__float__` must be refused |
| e | E22 (N05) | low | nothing pinned that only NumPy's own boolean types are refused by name | stand-ins named `bool` and `bool_` from module `mylib` with `__index__` must format as `1.2k` |
| e | E23 (N23) | low | a `ValueError` from the value's own `__float__` could be turned into `value is too large for a float` | GUIDE states that such a `ValueError` (from `__float__` or `__index__`) reaches the caller unchanged; a test pins both |
| e | E24 (N24) | low | nothing pinned the `--help` sentence about `--unit=-B` | `test_version_and_help` asserts the whole sentence |

Contract tests first: against b76bff8 the eight cases of
`tests/test_cli.py::test_an_option_value_of_two_dashes_is_read_as_text_on_every_python`
failed on CPython 3.11.5 and 3.10.19 and passed on 3.13.2 (N5 and F4); the lens e tests
passed there, as they pin existing behaviour. At ca77018 that test, `tests/test_cli.py`,
`tests/test_cli_options.py` and `tests/test_value_edges.py` pass on 3.10.19, 3.11.5,
3.12.12 and 3.13.2 on this PC. Each surviving lens e mutant and two for the new fix were
applied alone to a clone of ca77018 on Elena's PC (CPython 3.14.2, NumPy 2.5.4, full
suite with `-x`), and again to the four changed test files on 3.11.5 and 3.13.2 here:

| Id | Mutation | Caught by |
| --- | --- | --- |
| N12 | data type kinds as a denylist (`b c U S m O`) | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |
| N13 | `V` added to the allowed kinds | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |
| N02 | `bytes` not refused | `tests/test_value_edges.py::test_bytes_subclasses_with_float_are_refused[bytes]` |
| N03 | `bytearray` not refused | `tests/test_value_edges.py::test_bytes_subclasses_with_float_are_refused[bytearray]` |
| N05 | boolean names refused from any module | `tests/test_value_edges.py::test_only_numpy_booleans_are_refused_by_name[bool]` |
| N23 | `ValueError` from `__float__` read as an overflow | `tests/test_value_edges.py::test_a_value_error_from_the_values_own_protocol_reaches_the_caller_unchanged[float]` |
| N24 | `--help` sentence about `--unit=-B` removed | `tests/test_cli.py::test_version_and_help` |
| F4 | the `--` rule never applies | `tests/test_cli.py::test_an_option_value_of_two_dashes_is_read_as_text_on_every_python` on 3.11.5; equivalent on 3.12 and later, where argparse already passes `--` |
| F4b | the option's check skipped for `--` | `tests/test_cli.py::test_an_option_value_of_two_dashes_is_read_as_text_on_every_python` |

Gates at ca77018: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
`mypy --strict src tests` exit 0 on this PC (CPython 3.13.2, NumPy 2.3.5). On Elena's PC
(CPython 3.14.2, NumPy 2.5.4, a clone of the branch) `pytest` exits 0 (323 collected),
and so does `pytest` with `COMPACTNUM_E2E=1` (8 skipped: the fetched documents and GNU
numfmt are not on that PC).

### Round 5 (reviewed at 3eb194d, fixed at d56401b)

Lens a re-ran N5 on CPython 3.11.5 and 3.13.2 (fixed: `--unit=--` reads as the unit, the
other options exit 2 naming themselves, no traceback), ran 40 probes (34 CLI probes on
both interpreters and on stock `argparse.py` from twelve CPython tags, 6 on the GUIDE
claim about a `ValueError` from the value's own protocol), all as documented. Lens e ran
new mutants against the round-4 fixes; two survived. New findings, all fixed; none is
disputed:

| Lens | Id | Severity | Finding | Fix |
| --- | --- | --- | --- | --- |
| a | N6 | low | the CHANGELOG, the `_get_values` comment and a test comment said argparse dropped `--` from an option's values "before 3.12"; stock `argparse.py` does so on 3.10, on 3.11 before 3.11.8 and on 3.12 before 3.12.2 | CHANGELOG, `src/compactnum/_cli_io.py` and `tests/test_cli.py` name those versions |
| e | E25 (G13) | low | no test read a `--` given after the `--` separator, so dropping every `--` before delegating to argparse survived | `parse -- --` must exit 1 with `not compact notation: '--'` and `format -- --` exit 2 with `invalid number value: '--'` |
| e | E26 (V04, V05) | low | no test of NumPy `StringDType` arrays (kind `T`), so a denylist of kinds without `T`, or `T` added to the allowed kinds, survived | `np.array("1200", dtype=StringDType())` must be refused, naming `numpy.ndarray` (NumPy 2 and later; NumPy 1 has no such type) |

No behaviour changed in this round: the new tests pin what the code already did and pass
on the code at 3eb194d. Each surviving mutant was applied alone to a copy of the fixed
tree and `tests/test_cli.py` with `tests/test_value_types.py` run on CPython 3.11.5 and
NumPy 2.4.6:

| Id | Mutation | Caught by |
| --- | --- | --- |
| G13 | every `--` dropped before delegating to argparse | `tests/test_cli.py::test_an_option_value_of_two_dashes_is_read_as_text_on_every_python` (`format -- --`, `parse -- --`) |
| V05 | `T` added to the allowed data type kinds | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |
| V04 | data type kinds as a denylist (`b c U S m M O V`) | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |

The changed dash test passes on 3.10.19, 3.11.5 and 3.12.12 on this PC. Gates on this
PC: `ruff format --check .`, `ruff check .` and `mypy --strict src tests` exit 0.
On Elena's PC (CPython 3.14.2, NumPy 2.5.4, a clone of the branch) `pytest` exits 0,
and so does `pytest` with `COMPACTNUM_E2E=1` (8 skipped: the fetched documents and GNU
numfmt are not on that PC).

### Round 6 (reviewed at d56401b, fixed at 59e2a1c)

Lens e re-ran both round-5 findings: fixed. `parse -- --` exits 1 with
`not compact notation: '--'` and `format -- --` exits 2 with `invalid number value: '--'`;
`StringDType` arrays holding `1200` or `abc` are refused; G13, V04 and V05 are killed on
CPython 3.11.5 and 3.14.6. The only change to `src` since 3eb194d is a comment, so the lens
swept `Parser._get_values` and `_value._is_refused` with 10 new mutants: 6 killed, 1 killed
only on 3.11.5 (on 3.13 and 3.14 argparse already reads `--` as text), 2 equivalent (an
87-case CLI differential of exit code, stdout and stderr showed no difference on 3.11.5,
3.13.2 and 3.14.6, since every option has `nargs` None or 0) and 1 survivor. New finding,
fixed; none is disputed:

| Lens | Id | Severity | Finding | Fix |
| --- | --- | --- | --- | --- |
| e | E27 (S07) | low | no test used a NumPy complex array whose `float()` works, so `c` added to the allowed data type kinds survived: NumPy itself refuses `float()` of `np.array(1500 + 0j)`, but a `clongdouble` array converts with only a `ComplexWarning`, and the mutant formatted it as `1.5k` | `np.array(1500 + 0j, dtype=np.clongdouble)` must be refused, naming `numpy.ndarray` |

No behaviour changed in this round: the new case pins what the code already did. S07 was
applied alone to a copy of the tree and `tests/test_value_types.py` run on this PC: on
CPython 3.13.2 with NumPy 2.3.5 and on CPython 3.11.5 with NumPy 1.26.4 the test fails
under the mutant and passes on the unmutated code; without the new case it passed under
the mutant.

| Id | Mutation | Caught by |
| --- | --- | --- |
| S07 | `c` added to the allowed data type kinds | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |

Gates: `ruff format --check .`, `ruff check .` and `mypy --strict src tests` exit 0 on
this PC (CPython 3.13.2). On Elena's PC (CPython 3.14.2, NumPy 2.5.4, a clone of the
branch) `pytest` exits 0 (315 passed, 10 skipped).

### Round 7 (reviewed at 59e2a1c, fixed at 41a9cd2)

Lens e re-ran the round-6 finding: fixed. S07 is killed by
`tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` on
CPython 3.11.5, 3.13.2 and 3.14.2. The lens swept `_value._is_refused` and
`_get_values` with 9 new mutants: 8 killed (dropping the complex check, allowing the
kinds `b`, `O`, `V`, `U` or `S`, dropping the `bool_` name, `_get_values` returning
`[value]`) and 1 survivor. New finding, fixed; none is disputed:

| Lens | Id | Severity | Finding | Fix |
| --- | --- | --- | --- | --- |
| e | E28 (R07) | low | no test used a NumPy `datetime64` value, so `M` added to the allowed data type kinds survived: NumPy refuses `float()` of coarse units such as `s` and `D`, but a fine unit such as `ns` converts, and the mutant formatted `np.datetime64(1500, "ns")` as `1.5k` | `np.datetime64(1500, "ns")` must be refused naming `numpy.datetime64`, and `np.array(np.datetime64(1500, "ns"))` naming `numpy.ndarray` |

No behaviour changed in this round: the new cases pin what the code already did (GUIDE.md
promises a `TypeError` for NumPy values whose data type is not an integer or float type).
R07 was applied alone to a copy of the tree and `tests/test_value_types.py` run: the test
fails under the mutant and passes on the unmutated code on CPython 3.13.2 with NumPy 2.3.5
and on CPython 3.11.5 with NumPy 1.26.4 (this PC), and fails under the mutant on CPython
3.14.2 with NumPy 2.5.4 (Elena's PC).

| Id | Mutation | Caught by |
| --- | --- | --- |
| R07 | `M` added to the allowed data type kinds | `tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` |

Gates: `ruff format --check .`, `ruff check .` and `mypy --strict src tests` exit 0 on
this PC (CPython 3.13.2). On Elena's PC (CPython 3.14.2, NumPy 2.5.4, a clone of 41a9cd2)
`pytest` exits 0 (315 passed, 10 skipped).

### Independent review round 1 (reviewed at e061874, fixed at 556c6cf)

The independent reviewer (item 16) scored every item PASS except item 18, and so item 16,
after its own mutation round of 30 mutants at e061874: 27 killed, R04 equivalent (the
author's M12), R18 and R28 alive. It also found the author table stale: proven at
b805b23, ten of its mutants no longer matched the code. Findings, all fixed; none is
disputed:

| Id | Severity | Finding | Fix |
| --- | --- | --- | --- |
| F18 | medium | no test pinned the 300-character cut on command-line messages: `> MESSAGE_LIMIT + 1`, `MESSAGE_LIMIT = 301` and even `1000` passed the suite, as did stopping the unit scan one character short in `_without_unit` (`parse("B", unit="B")` then reported the missing unit instead of text that is not compact notation); the item-18 table was proven at b805b23 | `test_cli_messages_are_cut_at_exactly_300_characters`: `bounded` keeps 300 characters whole and cuts 301 to the first 300 plus `...`, and a real usage error of exactly 300 and of 301 characters goes through `main` to stderr the same way; `test_text_that_is_only_the_unit_has_no_number` pins `not compact notation: 'B'` for `parse("B", unit="B")` and for `parse_decimal(" kB ", unit="KB")`; the author table was run again at 556c6cf with the ten stale mutants ported and the survivors added as M45 to M47 (see the item-18 section) |
| F16 | low | item 16 stays open until a re-review scores every item PASS | re-review pending |

No behaviour changed in this round: the new tests pin what the code already did. GUIDE.md
now says a message longer than 300 characters is cut to its first 300, followed by
`...`. Both new tests were run under each survivor in a copy of the tree and fail under
R28, `MESSAGE_LIMIT = 301`, `1000` and `299`, and R18; their checks also pass on CPython
3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t on this PC (the argparse message
differs between versions, so the test measures it first).

Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
`mypy --strict src tests` exit 0 on this PC (CPython 3.13.2). On Elena's PC (CPython
3.14.2, NumPy 2.5.4, a clone of 556c6cf with the fetched documents) `pytest` exits 0,
and so does `pytest` with `COMPACTNUM_E2E=1` (326 passed, 1 skipped: GNU numfmt is not
on that PC).

### Round 8 (re-verification, every lens PASS)

Lens e re-ran the round-7 finding at e061874: fixed. Under R07 `np.datetime64(1500, "ns")`
formats as `1.5k` (8 of 48 values differ on CPython 3.11.5 with NumPy 2.4.6 and on 3.13.2
with NumPy 2.5.4), and the mutant is killed by
`tests/test_value_types.py::test_numpy_values_that_hold_no_real_number_are_refused` on
both, and by the full suite on the laptop (CPython 3.14.6, NumPy 2.5.4; unmutated, 313
passed and 12 skipped). Its sweep of 10 new mutants on `_value._is_refused` and
`Parser._get_values`: 9 killed; dropping the argparse `--` handling survives the suite on
3.14.6 and is equivalent there and on 3.13.2, whose argparse already reads `--` as text (0
of 11 CLI calls differ), and is killed on 3.11.5 by `tests/test_cli.py`. No new finding.

Lenses b and c re-verified their round-1 findings at 0848be4 and swept the changed code:
lens b ran 39 probes on CPython 3.11.5 and 3.13.2 (the three round-trip repros of 4301 to
4356 digits, the longest output of 8576 digits in every style, the 8600 and 8601 digit
limits, the case-folded units, string enums, the default style and the command line),
0 failing; lens c ran 40 probes on CPython 3.9.25 to 3.14.2 (case folding that changes
length, a lone surrogate, 30,000 seeded round trips with hostile units and 0 mismatches,
linear scaling from 100,000 to 1,600,000 characters, the 8600-digit limit under a caller
context with `int_max_str_digits=640`, bounded messages, no traceback and no hang), all
passing. Lens a (round 6, at d56401b) checked the argparse `--` versions against stock
`argparse.py` from 59 CPython tags and ran 10 probes, and lens d (round 5, at 3eb194d)
ran the sdist suite against the installed wheel on CPython 3.10.19, 3.11.5, 3.12.12,
3.13.2, 3.14.2 and 3.14.2t (311 passed, 7 upstream skips each), the sdist install, a
`mypy --strict` consumer and the PyPI check (404, not published); neither found anything.

### Final QA verdicts (item 19)

Each lens worked from the 1.0.0 bar, ran things rather than reading them, and posted
nothing to GitHub. The reports are kept in the local certification folder, outside the repository.

| Lens | Scope | Rounds | Final verdict | Report | Commit of the final round |
| --- | --- | --- | --- | --- | --- |
| a | API and docs | 6 | PASS | `lens-a-r6/REPORT.md` | d56401b |
| b | Correctness and ground truth | 2 | PASS | `lens-b-r2/probes-3.11.log`, `lens-b-r2/probes-3.13.log` | 0848be4 |
| c | Adversarial and robustness | 2 | PASS | `lens-c-r2/sweep-output.txt`, `lens-c-r2/cli-output.txt` | 0848be4 |
| d | Packaging and real e2e | 5 | PASS | `lens-d-r5/matrix.log` | 3eb194d |
| e | Contract strength | 8 | PASS | `lens-e-r8/sweep-portatil.log` | e061874 |

After 3eb194d the only change to `src` is one comment, so lenses a, d and e saw the
release code. The code changes after 0848be4, where lenses b and c ended, are the fixes of
rounds 2 to 4 (values with only `__index__` or `__float__`, type names, negative
infinities, the NumPy and complex refusals, the `--` handling), each re-verified by the
lens that found it and swept again by lenses a, d and e.

### Independent review round 2 (reviewed at 0fd443c, every item PASS)

The reviewer audited 0fd443c against every item of the 1.0.0 bar. Gates on this PC:
`ruff format --check .` (37 files), `ruff check .`, `mypy --strict src` (9 files) and
`mypy --strict src tests` (30 files) each exit 0. On Elena's PC (a clone of 0fd443c,
CPython 3.14.2, NumPy 2.5.4): `pytest` exits 0 without and with the fetched documents (all
five hashes match the manifest), the `COMPACTNUM_E2E=1` wheel tests pass, `python -m build`
and `twine check --strict` pass for both files. The wheel, installed in a fresh venv on
CPython 3.10.22, 3.11.17, 3.12.15, 3.13.17, 3.14.9 and 3.14.9t, runs the sdist suite with
319 passed and 3 skipped each (GNU numfmt, and the two typing tests where mypy is not
installed); 3.9.25 refuses the install, as `requires-python` says. The reviewer's own 33
mutants: 32 killed, R04 equivalent (the author's M12); the 9 mutants of the round-1 fixes
(the 300-character cut and the unit scan) are all killed. README links answer 200, except
`GUIDE.md` on `main` (it lands with the merge; 200 on `release/1.0.0`) and LinkedIn, which
refuses automated requests.

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS |
| 2 | `__all__` lists exactly the public names | PASS |
| 3 | Docstrings with runnable examples, doctests pass | PASS |
| 4 | Typed end to end | PASS |
| 5 | Typed, documented, safe errors | PASS |
| 6 | Contract test of every public name | PASS |
| 7 | Real ground truth | PASS |
| 8 | Real e2e from the wheel | PASS |
| 9 | Seeded fuzz and property tests | PASS |
| 10 | Supported Pythons | PASS |
| 11 | README and `twine check` | PASS |
| 12 | Dated CHANGELOG | PASS |
| 13 | pyproject | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates exit 0 alone | PASS |
| 16 | Independent reviewer | PASS |
| 17 | PR from `release/1.0.0` | PASS (PR #3; trace guard, merge and publish follow) |
| 18 | Contracts bite | PASS |
| 19 | Five independent QA lenses | PASS |

### Disputed findings

None in rounds 1 to 8 or in independent review rounds 1 and 2.
