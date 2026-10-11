# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- Add `format` to render numbers as compact notation with configurable precision, SI letters or long words, half-up rounding and scale carry.
- Add `parse` to read compact notation back into an `int` or `float`, with case-insensitive units and strict `CompactError` on invalid input.
