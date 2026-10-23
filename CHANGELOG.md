# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-22

The public API is now stable: `format`, `parse`, `parse_decimal` and `CompactError`,
their signatures, defaults and error types follow Semantic Versioning from this release
on. This is the first release published to PyPI; 0.1.0 and 0.2.0 exist only in the
repository, and the changes below are measured against 0.2.0.

### Stable

- `format` renders an `int`, `float`, `Decimal` or other real number as compact text
  with half-up rounding that carries across scales, in the short-scale, SI, word and
  IEC binary styles, with a unit and a decimal separator.
- `parse_decimal` reads compact text back as an exact `Decimal`, and `parse` as an `int`
  or the nearest `float`, accepting every suffix of every style without case.
- `CompactError` (a `ValueError`) for text that is not compact notation; `TypeError` for
  arguments of the wrong type; `ValueError` for invalid options.
- The `compactnum` command and `python -m compactnum`.

### Added

- Scales 9 and 10: `Oc` and `No` (octillion, nonillion) in the short scale, the 2022 SI
  prefixes `R` and `Q` under `style="metric"`. In 0.2.0, `format(10**27)` was `1000Sp`
  and `format(10**30, style="metric")` was `1000000Y`.

### Changed

- The default style is named `"short"`. `"si"`, its 0.x name, is still accepted and
  means the same short-scale letters (`1.5B`); the SI prefixes (`1.5G`) are
  `style="metric"`, as before. The command's `--style` default is `short` too.
- `format`'s `value` is annotated `SupportsFloat | SupportsIndex` (it was `float`), so
  type checkers accept the `Decimal`, `Fraction` and NumPy values it reads, and it reads
  every value the annotation accepts: an object with only `__index__` exactly, one with
  only `__float__` (a 0-d NumPy array) through `float()`. 0.2.0 raised
  `decimal.InvalidOperation` for both. NumPy booleans and complex numbers are refused
  like `bool` and `complex`, and so is a NumPy scalar or array whose data type is not
  an integer or float type (`np.array(True)`, a string or timedelta array), although
  NumPy gives each of them `__float__`. A value read through `float()` that is too
  large for one (`Fraction(10**400)`) raises `ValueError`, where 0.2.0 raised
  `decimal.InvalidOperation`.
- A `TypeError` message names a type outside the builtins by module and name
  (`trim_zeros must be a bool, not numpy.bool`); a longer name than 80 characters is cut
  to its first 80 and `...`.
- `format` computes with exact decimal arithmetic whatever the size of the value. In
  0.2.0 it used the caller's `decimal` context (28 digits by default), so
  `format(123456789012345678901234567890123, precision=3)` printed `123456789.012Sp`, and
  a context with `prec=3` made it raise `InvalidOperation`.
- `format` raises `TypeError` for a value that is not a real number: `bool` and strings
  included (0.2.0 formatted `"1200"`), and for a `precision` that is not an integer or a
  `unit` that is not a string (0.2.0 appended `5` for `unit=5`), and for a `trim_zeros`
  that is not a `bool` (0.2.0 read any value as true or false, so `trim_zeros="False"`
  trimmed). It raises `ValueError`
  for a value that is not finite (0.2.0 raised `decimal.InvalidOperation`), for a value
  with more than 4300 integer digits and for a `precision` above 4300.
- `parse` and `parse_decimal` raise `TypeError`, not `CompactError`, when `text` is not
  a string, and `TypeError` when `unit` or `decimal_sep` is not a string (0.2.0 raised
  `AttributeError` for `unit`).
- A `str` subclass passed as text, `style`, `unit` or `decimal_sep`, such as a string
  enum member, is read by its characters, never by its own `__str__` or `__eq__`.
- Only ASCII digits are read: 0.2.0 read `"١٢k"` (Arabic-Indic digits) as 12000.
  At most 8600 digits are read, which covers the longest text `format` writes, so every
  result of `format` reads back.
- `unit` is matched by Unicode case folding, so `"SS"` matches `"ß"` (0.2.0 compared
  lower case, and failed whenever folding changes the length).
- `parse_decimal` returns whole values with exponent 0 and other values without
  trailing zeros (0.2.0 returned `Decimal('1200.0')` for `"1.2k"`), and zero without a
  sign; a caller context no longer rounds the result.
- `parse` raises `CompactError` for a value that is not whole and too large for a
  `float`; 0.2.0 could return a wrong `int` for such text.
- Whitespace around `unit` is ignored.
- Error messages quote at most 40 characters of the input, and the unknown suffix message
  reads `unknown suffix: 'x'` (it was `unknown unit`).
- `CompactError` reports `compactnum` as its module.
- The command reads `format`'s value exactly as a decimal (0.2.0 went through `float` for
  any value with a point), prints whole results of any size, cuts messages at 300
  characters, exits 1 quietly when its output pipe closes, and reports output its
  encoding cannot hold instead of failing with a traceback.
- The command reads a value that starts with a minus sign (`format -1e3`,
  `parse -1.2k`) the same way on every Python version; before 3.14, argparse took such a
  value for an option unless `--` came first. `format -inf` and `format -nan` are read
  as values too and exit 1 because they are not finite; any other dash followed by a
  letter (`parse -k`, `--unit -B`) is still an option.
- An invalid `--precision` or `--decimal-sep` value is a usage error (exit 2) that names
  the option, like every other invalid option.
- An option given the value `--` with `=` reads it as the text `--` on every Python
  version, so `--unit=--` is the unit `--` and `--precision=--` is a usage error (exit
  2). On Python 3.10, 3.11 before 3.11.8 and 3.12 before 3.12.2, argparse handed such
  an option an empty list, and the command failed with a traceback.
- `Development Status :: 5 - Production/Stable`.

## [0.2.0]

- Add `style="metric"` for true SI prefixes (`k M G T P E Z Y`) and `style="short"` as an alias of `style="si"`.
- Extend the short scale to `Qa Qi Sx Sp` so values up to `10^24` keep a compact suffix.
- Add `base=1024` for binary (IEC) magnitudes (`Ki Mi Gi ...` and the `kibi` words).
- Add a `unit` argument to `format` and `parse` to glue and strip a trailing unit such as `B`.
- Add a `decimal_sep` argument to `format` and `parse` for locale decimal separators.
- Add `parse_decimal` for exact `Decimal` parsing without float rounding.
- Add a `compactnum` command-line interface with `format` and `parse` subcommands, `--version` and runnable help examples.

## [0.1.0]

- Add `format` to render numbers as compact notation with configurable precision, SI letters or long words, half-up rounding and scale carry.
- Add `parse` to read compact notation back into an `int` or `float`, with case-insensitive units and strict `CompactError` on invalid input.
