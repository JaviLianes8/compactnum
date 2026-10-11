# compactnum

Two-way compact number notation: format large numbers as `1.2k` or `3.5M` and parse them back.

## Install

```
pip install compactnum
```

## Usage

```python
import compactnum

compactnum.format(1200)             # "1.2k"
compactnum.format(3_500_000)        # "3.5M"
compactnum.format(2_000_000_000)    # "2B"
compactnum.format(-1200)            # "-1.2k"

compactnum.format(1234, precision=2)        # "1.23k"
compactnum.format(1200, style="long")       # "1.2 thousand"
compactnum.format(2000, trim_zeros=False)   # "2.0k"

compactnum.parse("1.2k")            # 1200
compactnum.parse("3.5M")            # 3500000
compactnum.parse("1.2 thousand")    # 1200
compactnum.parse("-2B")             # -2000000000
```

Formatting rounds half up and carries across scales, so `999999` becomes `1M`.
Parsing is strict: it matches the unit case-insensitively (`k`, `M`, `B`, `T`, or
the long words) and raises `CompactError` on anything else.

```python
from compactnum import CompactError, parse

try:
    parse("1.2x")
except CompactError:
    ...
```

`parse` returns an `int` when the result is whole and a `float` otherwise, so
`format` and `parse` round-trip.

## Why

Existing options only go one way. `numerize`, `millify` and `humanize` format
numbers into compact strings but cannot read them back, while `numify` parses
compact strings but cannot produce them. `compactnum` does both directions with
one small, typed, zero-dependency package, with configurable precision, SI
letters or long words, correct rounding, and strict parse errors.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
