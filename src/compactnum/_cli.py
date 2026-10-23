"""Command-line interface for compactnum: ``compactnum format`` and ``compactnum parse``."""

from __future__ import annotations

import argparse
import math
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from . import __version__
from ._cli_io import Parser, bounded, finish, write
from ._errors import CompactError
from ._format import format as format_number
from ._parse import parse_decimal
from ._scales import BASES, MAX_DIGITS, STYLES, validate_separator

_EXAMPLES = """examples:
  compactnum format 1200                        ->  1.2k
  compactnum format 3500000 --style long        ->  3.5 million
  compactnum format 1536 --base 1024 --unit B   ->  1.5KiB
  compactnum format 1234 --precision 2          ->  1.23k
  compactnum parse 1.2k                         ->  1200
  compactnum parse 1.5KiB --unit B              ->  1536
  compactnum parse 1,5k --decimal-sep ,         ->  1500
  compactnum parse 1.2345k --exact              ->  1234.5
  compactnum parse -1.2k                        ->  -1200

A value may start with a minus sign (-inf and -nan included) on every Python version;
-- before it works too.
Exit codes: 0 done, 1 the value was rejected (or the output could not be written),
2 bad usage (an invalid option value included).
"""


def _number(text: str) -> Decimal:
    """Read a command-line number exactly (integer, decimal or scientific notation)."""
    try:
        return Decimal(text.strip())
    except InvalidOperation:
        raise ValueError(text) from None


def _precision(text: str) -> int:
    number = int(text)  # a ValueError reads as "invalid integer value"
    if not 0 <= number <= MAX_DIGITS:
        raise argparse.ArgumentTypeError(f"must be between 0 and {MAX_DIGITS}")
    return number


def _separator(text: str) -> str:
    try:
        return validate_separator(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "must be one character that is not a digit, letter, sign or space"
        ) from None


# argparse names the type in its messages.
_number.__name__ = "number"
_precision.__name__ = "integer"


def _build_parser() -> argparse.ArgumentParser:
    parser = Parser(
        prog="compactnum",
        description="Format numbers as compact notation and parse them back.",
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"compactnum {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fmt = subparsers.add_parser("format", help="format a number into compact notation")
    fmt.add_argument("value", type=_number, help="the number to format, read exactly")
    fmt.add_argument("--precision", type=_precision, default=1, help="mantissa decimals, 0 to 4300")
    fmt.add_argument(
        "--style", choices=STYLES, default="short", help="suffix style (default short)"
    )
    fmt.add_argument("--base", type=int, choices=BASES, default=1000, help="1000 or 1024")
    fmt.add_argument("--unit", default="", help="trailing unit, for example B")
    fmt.add_argument("--decimal-sep", type=_separator, default=".", help="decimal separator")
    fmt.add_argument("--no-trim", action="store_true", help="keep trailing zeros")

    prs = subparsers.add_parser("parse", help="parse compact notation into a number")
    prs.add_argument("text", help="the compact string to parse")
    prs.add_argument("--unit", default="", help="trailing unit to strip, for example B")
    prs.add_argument("--decimal-sep", type=_separator, default=".", help="decimal separator")
    prs.add_argument("--exact", action="store_true", help="print the exact decimal value")
    return parser


def _run(args: argparse.Namespace) -> str:
    if args.command == "format":
        return format_number(
            args.value,
            precision=args.precision,
            style=args.style,
            base=args.base,
            unit=args.unit,
            trim_zeros=not args.no_trim,
            decimal_sep=args.decimal_sep,
        )
    value = parse_decimal(args.text, unit=args.unit, decimal_sep=args.decimal_sep)
    if args.exact or value.as_tuple().exponent == 0:
        # parse_decimal gives whole values exponent 0 and others no trailing zeros, so
        # plain notation is exact; Decimal has no int-to-str digit limit.
        return f"{value:f}"
    result = float(value)  # what parse() returns for a value that is not whole
    if math.isinf(result):
        raise CompactError("too large for a float; use --exact")
    return repr(result)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return a process exit code.

    Exit codes: 0 done, 1 the value was rejected or the output could not be
    written, 2 bad usage.
    """
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else 2
    try:
        output = _run(args)
    except (CompactError, ValueError) as error:
        write("stderr", f"compactnum: error: {bounded(str(error))}\n")
        return finish(1)
    return finish(0 if write("stdout", output + "\n") else 1)


if __name__ == "__main__":  # pragma: no cover - exercised through python -m compactnum
    raise SystemExit(main())
