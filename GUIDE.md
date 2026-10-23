# compactnum guide

The behaviour of every public name in detail. Each Python block below runs as a test:
a comment line after a `print` holds what it prints.

## Formatting

`format(value, *, precision=1, style="short", base=1000, unit="", trim_zeros=True,
decimal_sep=".")` picks the largest scale not above the value, divides, rounds the
mantissa to `precision` decimals and writes the suffix.

- **Input.** An integer (`int`, a NumPy integer) and a `Decimal` are read exactly, a
  `float` as its shortest `repr` (so `1.05` rounds like the decimal 1.05, not like the
  binary value just below it), and any other real number (a `Fraction`, a NumPy float)
  through `float()`. `value` is annotated `SupportsFloat | SupportsIndex`, so a type
  checker accepts all of them.
  `bool`, strings, `None` and complex numbers raise `TypeError`. Infinities, NaNs and
  values with more than 4300 integer digits raise `ValueError`.
- **Rounding** is half-up: ties go away from zero. It works on the exact decimal value,
  so the result never depends on binary floating point or on the caller's `decimal`
  context.
- **Carry.** When rounding reaches the base, the next scale is used: `999_999` is
  `1M`, not `1000k`. Past the largest suffix the mantissa simply grows: `10**33` is
  `1000No`.
- **Zero** has no sign: `-0.04` is `0`, and so is `-0.0`.
- **Trimming.** Trailing fractional zeros are dropped, then a bare decimal point;
  `trim_zeros=False` keeps exactly `precision` decimals. `trim_zeros` must be a `bool`.
- `precision` is an integer from 0 to 4300 (any `__index__` integer, `bool` refused),
  `base` is 1000 or 1024, `unit` any string appended exactly as given, and
  `decimal_sep` a single character that is not a digit, a letter, a sign or whitespace.
  A `str` subclass, such as a string enum member, is read by its characters, never by
  its own `__str__`.

```python
from compactnum import format

print(format(1249), format(1250), format(-1250), format(1.05), format(-0.04))
# 1.2k 1.3k -1.3k 1.1 0
print(format(999_950), format(999_949), format(10**33))
# 1M 999.9k 1000No
print(format(2000, trim_zeros=False), format(2000, precision=0), format(1234.5, precision=0))
# 2.0k 2k 1k
```

### Styles and bases

| Scale | `"short"` | `"metric"` | `"long"` | `base=1024` | `base=1024`, `"long"` |
| --- | --- | --- | --- | --- | --- |
| 1 | `k` | `k` | `thousand` | `Ki` | `kibi` |
| 2 | `M` | `M` | `million` | `Mi` | `mebi` |
| 3 | `B` | `G` | `billion` | `Gi` | `gibi` |
| 4 | `T` | `T` | `trillion` | `Ti` | `tebi` |
| 5 | `Qa` | `P` | `quadrillion` | `Pi` | `pebi` |
| 6 | `Qi` | `E` | `quintillion` | `Ei` | `exbi` |
| 7 | `Sx` | `Z` | `sextillion` | `Zi` | `zebi` |
| 8 | `Sp` | `Y` | `septillion` | `Yi` | `yobi` |
| 9 | `Oc` | `R` | `octillion` | | |
| 10 | `No` | `Q` | `nonillion` | | |

`"short"` is the default. `"si"` is its 0.x name, still accepted; it writes the
short-scale letters, not the SI prefixes, which `"metric"` writes.

Scale *n* is 1000<sup>*n*</sup>, or 1024<sup>*n*</sup> with `base=1024`. Sources: the
SI prefixes are the BIPM list (with `ronna` and `quetta` from 2022), the binary prefixes
are IEC 80000-13 as listed by NIST and Wikipedia, and the words are the short-scale
names. The letters `Qa Qi Sx Sp Oc No` are a common convention with no standard behind
them. The 2025 IEC prefixes `robi` (`Ri`) and `quebi` (`Qi`) are left out on purpose:
`Qi` already reads as the short-scale quintillion. Unicode CLDR writes `K` for
thousands in English; compactnum writes the SI `k` and reads both.

```python
from compactnum import format

print(format(1_500_000_000), format(1_500_000_000, style="metric"))
# 1.5B 1.5G
print(format(10**30, style="metric"), format(7 * 10**27, style="long"))
# 1Q 7 octillion
print(format(5_368_709_120, base=1024, unit="B"), format(1024, base=1024, style="long"))
# 5GiB 1 kibi
print(format(1500, unit=" ms"), format(1500, decimal_sep=","))
# 1.5k ms 1,5k
```

## Parsing

`parse_decimal(text, *, unit="", decimal_sep=".")` reads an optional sign, ASCII digits
with an optional fraction (at most 8600 digits in all, which covers anything `format`
writes), optional whitespace and a suffix
from any style or base, and returns the exact `Decimal`. `parse` is the same reading
with an `int` result when the value is whole and the nearest `float` otherwise.

- Suffixes are matched without case: `1.2K`, `1.2k`, `3 MILLION` and `1mi` are all
  valid. So `m` is million (mega), never milli, and `e` is exa.
- Whitespace is allowed around the text and between the number and the suffix.
- `unit` is stripped from the end first, without case (Unicode case folding, so `SS`
  matches `ß`) and ignoring whitespace around the unit itself; text without it raises
  `CompactError`. `"B"` reads `"1.5KiB"` as
  `1.5Ki`. Without `unit`, a trailing `B` is the short-scale billion.
- With a `decimal_sep` other than `.`, a `.` in the text is an error, so `1.5k` is not
  silently read as 15k.
- Not accepted: exponents (`1e3`), digit grouping (`1,200`), a bare or leading point
  (`1.`, `.5`), digits of other scripts, and anything after the suffix.
- `parse_decimal` returns whole values with exponent 0 (`Decimal('1200')`, never
  `Decimal('1.2E+3')`), other values without trailing zeros, and zero without a sign.
- `parse` raises `CompactError` when a value that is not whole is too large for a
  `float`; `parse_decimal` reads it.

```python
from compactnum import CompactError, parse, parse_decimal

print(parse("1.2K"), parse(" -3 MILLION "), parse("1.5 kibi"), parse("2B"))
# 1200 -3000000 1536 2000000000
print(parse("2B", unit="B"), parse("1.5 KiB", unit="b"), parse_decimal("1.20k"))
# 2 1536 1200
print(repr(parse_decimal("0.1234k")), parse("0.1234k"))
# Decimal('123.4') 123.4
for text in ["1e3", "1,200", ".5k", "1.5kk"]:
    try:
        parse(text)
    except CompactError as error:
        print(error)
# not compact notation: '1e3'
# not compact notation: '1,200'
# not compact notation: '.5k'
# unknown suffix: 'kk'
```

## Round trips

`format` is lossy by design: it shows a rounded quantity. `parse_decimal` reads back
exactly that quantity, with the same `unit` and `decimal_sep`, in every style and base,
for every argument `format` accepts: its longest output, 8576 digits (a 4300-digit value
over `Yi` at precision 4300), is within the 8600 digits the parser reads.

```python
from compactnum import format, parse_decimal

text = format(1234, precision=2, base=1024, unit="B")
print(text, parse_decimal(text, unit="B"))
# 1.21KiB 1239.04
```

## Errors

| Situation | Exception |
| --- | --- |
| Text that is not compact notation, lacks the unit, or has more than 8600 digits | `CompactError` |
| A value that is not whole and too large for a `float`, in `parse` | `CompactError` |
| An argument of the wrong type (`parse(12)`, `format("12")`, `format(True)`, `trim_zeros="no"`) | `TypeError` |
| An invalid `style`, `base`, `precision` or `decimal_sep`, a non-finite or too large value | `ValueError` |

`CompactError` subclasses `ValueError`, so `except ValueError` catches every value error.
Messages quote at most 40 characters of the input, so a huge or hostile string never
lands whole in a log.

## Command line

`compactnum format VALUE` takes the options of `format` (`--precision`, `--style`,
`--base`, `--unit`, `--decimal-sep`, `--no-trim`) and reads `VALUE` exactly as a
decimal (scientific notation allowed). `compactnum parse TEXT` takes `--unit`,
`--decimal-sep` and `--exact`; it prints whole values in full, other values as the
nearest float, or the exact decimal with `--exact`. A value may start with a minus sign
(`compactnum format -1e3`, `compactnum parse -1.2k`) on every supported Python; `--`
before it (`compactnum parse -- -1.2k`) works too.

Exit codes: 0 done; 1 the value was rejected, or the output could not be written (a
closed pipe, or a unit the output encoding cannot hold); 2 bad usage, including an
invalid `--precision` or `--decimal-sep` value, named by its option. Messages go to
stderr and are cut at 300 characters.

## Compared with other packages

Checked on 2026-10-23 with the versions shown, each installed from PyPI and run.

| Package | Formats | Parses | 999,999 | Notes |
| --- | --- | --- | --- | --- |
| `numerize` 0.12 | `1.2K` | no | `1000K` | short scale `K M B T` |
| `millify` 0.1.1 | `1.2k` | no | `1000k` | |
| `humanize` 4.16.0 | `1.2 thousand`, `1.5 KiB` | no | `1.0 million` | words, sizes and SI |
| `numify` 1.0.1 | no | `1.2k` to `1200` | | `k M B T` only, no sign |
| Babel 2.18.0 | `1.2K` (CLDR, many locales) | no compact parsing | | |
| `humanfriendly` 10.0 | `1.5 KiB` | `parse_size` | | byte sizes; `"1.5 billion"` reads as `1` |
| `prefixed` 0.9.0 | `1.2k`, `1.5Ki` | `Float("1.5Ki")` | `1.0M` | SI and IEC, float results |
| compactnum 1.0.0 | all of the styles above | exact | `1M` | short scale, SI, IEC, words |

## Upgrading from 0.2.0

0.2.0 was never published to PyPI. For anyone who installed it from the repository, the
behaviour changes are listed in the
[CHANGELOG](https://github.com/JaviLianes8/compactnum/blob/main/CHANGELOG.md).
