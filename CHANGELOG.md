# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
