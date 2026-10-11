# Improvements round

Ranked, substantial improvements for `compactnum`, measured against the `0.1.0`
surface: `format(value, *, precision, style, trim_zeros)`,
`parse(text) -> int | float`, `CompactError`, and the `k/M/B/T` short-scale table
with long words. Every item below is additive. Nothing changes the meaning of an
existing call, so code written against `0.1.0` keeps its exact behaviour.

## Shipped in this round (0.2.0)

1. **Binary (IEC) mode.** A `base` argument (`1000` or `1024`). With `base=1024`
   the thresholds and prefixes become `Ki Mi Gi Ti Pi Ei Zi Yi` (and `kibi` to
   `yobi` under `style="long"`), so `1536` formats as `1.5Ki`. This is the single
   most requested capability for a compact-number library used for file sizes and
   memory, and the parser reads the IEC prefixes back.

2. **Unit suffix.** A `unit` argument glued to the prefix, so the library covers
   `kB`, `MiB`, `900B` and `1.5 million` plus a unit without the caller joining
   strings. `parse` takes the same `unit` and strips it back off, keeping the
   round-trip intact and parsing strict: a missing expected unit raises.

3. **More magnitudes.** The decimal table now reaches `10^24`: short-scale
   letters `Qa Qi Sx Sp` (quadrillion to septillion). Large values no longer fall
   back to a bare number with a huge mantissa.

4. **Metric style.** `style="metric"` yields correct SI prefixes (`1.5G`,
   `1.5P`), distinct from the finance-flavoured short scale (`1.5B`). The historic
   `style="si"` keeps its exact old meaning and gains the alias `style="short"`.

5. **Locale decimal separator.** A `decimal_sep` argument on both `format` and
   `parse` (default `"."`), so `1,5k` is a first-class input and output for
   locales that use the comma. It is validated to be a single, safe character.

6. **Exact parsing.** A new `parse_decimal` returns an exact
   `decimal.Decimal`, free of binary-float rounding, for very large magnitudes or
   money. `format` stays intentionally lossy (rounded); `parse_decimal` is the
   exact counterpart, so the lossy round-trip is a documented, tested contract.

7. **Command-line interface.** A `compactnum` console script (argparse) with
   `format` and `parse` subcommands, options mirroring the library
   (`--precision`, `--style`, `--base`, `--unit`, `--decimal-sep`, `--no-trim`,
   `--exact`), `--version`, help with runnable examples, and errors to stderr with
   exit code `1`.

8. **Stronger tests and docs.** A full-promise contract test that sweeps format
   and parse across every style, base, precision and edge value with round-trip
   assertions, a real end-to-end test that pip-installs the package editable into
   a throwaway virtual environment and drives the installed console script through
   `subprocess`, expanded docstrings on every public callable, and a README guide
   covering styles, bases, units, separators, rounding, exact values and the CLI.

## Considered and deliberately deferred

- **Sub-unit metric prefixes** (`m`, `u`, `n` for values below 1). Useful, but it
  makes case-insensitive parsing ambiguous (`m` milli versus `M` mega) and would
  weaken the strict parser. Left for a dedicated round with an explicit opt-in.
- **Thousands grouping on input** (`1,200,000`). The comma already serves as a
  decimal separator in many locales, so accepting it as a group separator too
  would be ambiguous. Not added.
- **Significant-figure mode** (round to N significant digits rather than N
  decimals). A reasonable future `precision`-style option; out of scope here.
