# compactnum

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

Two-way compact number notation: format large numbers as `1.2k`, `3.5M` or `1.5KiB`
and parse them back, exactly.

## Install

```
pip install compactnum
```

## Usage

```python
import compactnum

print(compactnum.format(1200), compactnum.format(3_500_000), compactnum.format(-2_000_000_000))
# 1.2k 3.5M -2B

# Half-up rounding that carries to the next scale.
print(compactnum.format(1250), compactnum.format(999_999), compactnum.format(1234, precision=2))
# 1.3k 1M 1.23k

print(compactnum.parse("1.2k"), compactnum.parse("3.5 million"), compactnum.parse("1.2345k"))
# 1200 3500000 1234.5
```

`parse` returns an `int` when the value is whole and the nearest `float` otherwise;
`parse_decimal` returns the exact `Decimal`.

### Styles, bases and units

```python
from compactnum import format, parse

print(format(1_500_000_000), format(1_500_000_000, style="metric"))
# 1.5B 1.5G
print(format(1_500_000_000, style="long"))
# 1.5 billion

# base=1024 uses the IEC binary prefixes; a unit is appended and stripped back off.
print(format(1536, base=1024, unit="B"), parse("1.5KiB", unit="B"))
# 1.5KiB 1536
```

### Exact values, separators and errors

```python
from decimal import Decimal

from compactnum import CompactError, format, parse, parse_decimal

print(parse_decimal("999999999999999999.5k"))
# 999999999999999999500
print(format(Decimal("123456789012345678901234567890"), precision=3))
# 123.457Oc

print(format(1500, decimal_sep=","), parse("1,5k", decimal_sep=","))
# 1,5k 1500

try:
    parse("1.2x")
except CompactError as error:  # a ValueError subclass
    print(error)
# unknown suffix: 'x'
```

## API

| Name | What it does |
| --- | --- |
| `format(value, *, precision=1, style="si", base=1000, unit="", trim_zeros=True, decimal_sep=".")` | Compact text for an `int`, `float`, `Decimal` or other real number. |
| `parse(text, *, unit="", decimal_sep=".")` | The value as `int` (whole) or `float`. |
| `parse_decimal(text, *, unit="", decimal_sep=".")` | The exact value as a `Decimal`. |
| `CompactError` | `ValueError` subclass raised for text that is not compact notation. |

Styles: `"si"` (default) and its alias `"short"` write the short-scale letters
`k M B T Qa Qi Sx Sp Oc No`, `"metric"` the SI prefixes `k M G T P E Z Y R Q`, and
`"long"` the words `thousand` to `nonillion`. With `base=1024` they become `Ki` to `Yi`
(`kibi` to `yobi` under `"long"`). `parse` reads every one of them, in any case.

## Command line

```
$ compactnum format 1536 --base 1024 --unit B
1.5KiB
$ compactnum format 3500000 --style long
3.5 million
$ compactnum parse 1.2345k --exact
1234.5
$ compactnum parse -- -1.2k
-1200
```

`compactnum --help` lists every option. Exit codes: 0 done, 1 the value was rejected,
2 bad usage.

## Why

Python packages for compact numbers mostly go one way. `numerize` 0.12, `millify` 0.1.1
and `humanize` 4.16.0 format but have no parser, and the first two print `1000K` and
`1000k` for 999,999 where the rounding should carry to `1M`. `numify` 1.0.1 only parses
`k`, `M`, `B` and `T`, without a sign. Babel formats CLDR compact numbers but its parser
rejects `1.2K`. `prefixed` 0.9.0 works both ways for SI and binary prefixes but returns
floats, and `humanfriendly` 10.0 formats and parses byte sizes; neither reads the
short-scale `B` for billion or the words (`humanfriendly.parse_size("1.5 billion")`
returns `1`). `compactnum` covers the
short scale, SI and IEC prefixes and the words in both directions, with half-up
rounding that carries, an exact `Decimal` parser and a command-line tool, in one small,
typed, dependency-free package. It is tested against the BIPM, NIST and CLDR tables and
the output of ICU and GNU `numfmt`.

The [GUIDE](https://github.com/JaviLianes8/compactnum/blob/main/GUIDE.md) has every rule
in detail, and the [CHANGELOG](https://github.com/JaviLianes8/compactnum/blob/main/CHANGELOG.md)
what changed in each release.

## Development

`python scripts/fetch_upstream.py` downloads the reference documents listed in
`tests/upstream/MANIFEST.json` (they are not part of the repository; their tests skip
without them). `scripts/check.ps1` runs format, lint, types and tests. Set
`COMPACTNUM_E2E=1` to also build the wheel and test the installed package.

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/compactnum/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
