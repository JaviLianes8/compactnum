# compactnum

Two-way compact number notation: format large numbers as `1.2k` or `3.5M` and
parse them back. Small, typed, and dependency-free.

## Install

```
pip install compactnum
```

## Usage

```python
import compactnum

compactnum.format(1200)  # "1.2k"
compactnum.format(3_500_000)  # "3.5M"
compactnum.format(2_000_000_000)  # "2B"
compactnum.format(-1200)  # "-1.2k"

compactnum.format(1234, precision=2)  # "1.23k"
compactnum.format(1200, style="long")  # "1.2 thousand"
compactnum.format(2000, trim_zeros=False)  # "2.0k"

compactnum.parse("1.2k")  # 1200
compactnum.parse("3.5M")  # 3500000
compactnum.parse("1.2 thousand")  # 1200
compactnum.parse("-2B")  # -2000000000
```

`parse` returns an `int` when the result is whole and a `float` otherwise.

## Guide

### Styles

`style="si"` (default), or its alias `style="short"`, uses the finance-flavoured
short scale `k M B T` and keeps growing to `Qa Qi Sx Sp`. `style="metric"` uses
true SI prefixes `k M G T P E Z Y`, and `style="long"` spells the words.

```python
compactnum.format(1_500_000_000, style="si")  # "1.5B"
compactnum.format(1_500_000_000, style="metric")  # "1.5G"
compactnum.format(1_500_000_000, style="long")  # "1.5 billion"
```

### Binary (IEC) mode and units

Pass `base=1024` for file sizes and memory. The prefixes become
`Ki Mi Gi Ti Pi Ei Zi Yi` (and `kibi` to `yobi` under `style="long"`). A `unit`
is glued to the suffix, and `parse` strips the same unit back off.

```python
compactnum.format(1536, base=1024, unit="B")  # "1.5KiB"
compactnum.parse("1.5KiB", unit="B")  # 1536
```

### Precision, rounding and trimming

Rounding is half-up and carries across scales, so `999999` becomes `"1M"`.
Trailing fractional zeros are dropped unless `trim_zeros=False`.

```python
compactnum.format(1250)  # "1.3k"
compactnum.format(999_999)  # "1M"
compactnum.format(2000, trim_zeros=False)  # "2.0k"
```

### Locale decimal separator

```python
compactnum.format(1500, decimal_sep=",")  # "1,5k"
compactnum.parse("1,5k", decimal_sep=",")  # 1500
```

### Exact values

`format` is lossy by design: `format(1234)` is `"1.2k"`, which reads back as
`1200`. Use `parse_decimal` for an exact `Decimal`, free of float rounding, which
is ideal for very large magnitudes or money.

```python
from decimal import Decimal
from compactnum import parse_decimal

parse_decimal("1.5KiB", unit="B")  # Decimal("1536")
parse_decimal("999999999999999999k")  # Decimal("999999999999999999000")
```

### Errors

Parsing is strict and raises `CompactError` (a `ValueError` subclass) on anything
that is not clean compact notation.

```python
from compactnum import CompactError, parse

try:
    parse("1.2x")
except CompactError:
    ...
```

## Command line

The package installs a `compactnum` console script.

```
compactnum format 1200                        # 1.2k
compactnum format 1536 --base 1024 --unit B   # 1.5KiB
compactnum format 3500000 --style long        # 3.5 million
compactnum parse 1.2k                          # 1200
compactnum parse 1.5KiB --unit B               # 1536
compactnum parse 1,5k --decimal-sep ,          # 1500
compactnum --version
```

Run `compactnum --help` for every option. Errors print to stderr and exit with
code `1`.

## Why

Existing options only go one way. `numerize`, `millify` and `humanize` format
numbers into compact strings but cannot read them back, while `numify` parses
compact strings but cannot produce them. `compactnum` does both directions with
one small, typed, zero-dependency package, with configurable precision and
rounding, short, metric, long and binary styles, units, locale separators, an
exact decimal parser, and a command-line tool.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
