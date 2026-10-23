"""Command-line interface for compactnum: ``compactnum format`` and ``parse``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from decimal import Decimal

from . import __version__
from ._errors import CompactError
from ._format import format as format_number
from ._parse import parse, parse_decimal
from ._scales import BASES, STYLES

_EXAMPLES = """examples:
  compactnum format 1200                 ->  1.2k
  compactnum format 3500000 --style long ->  3.5 million
  compactnum format 1536 --base 1024 --unit B   ->  1.5KiB
  compactnum format 1234 --precision 2   ->  1.23k
  compactnum parse 1.2k                   ->  1200
  compactnum parse 1.5KiB --unit B        ->  1536
  compactnum parse 1,5k --decimal-sep ,   ->  1500
"""


def _number(text: str) -> float:
    """Parse a CLI number, keeping integers exact."""
    try:
        return int(text)
    except ValueError:
        return float(text)


def _plain(value: Decimal) -> str:
    """Render a Decimal in plain notation without trailing zeros or exponents."""
    text = f"{value:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compactnum",
        description="Format numbers as compact notation and parse them back.",
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"compactnum {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fmt = subparsers.add_parser("format", help="format a number into compact notation")
    fmt.add_argument("value", type=_number, help="the number to format")
    fmt.add_argument("--precision", type=int, default=1, help="mantissa decimals (default 1)")
    fmt.add_argument("--style", choices=STYLES, default="si", help="suffix style (default si)")
    fmt.add_argument("--base", type=int, choices=BASES, default=1000, help="1000 or 1024")
    fmt.add_argument("--unit", default="", help="trailing unit, for example B")
    fmt.add_argument("--decimal-sep", default=".", help="decimal separator (default .)")
    fmt.add_argument("--no-trim", action="store_true", help="keep trailing zeros")

    prs = subparsers.add_parser("parse", help="parse compact notation into a number")
    prs.add_argument("text", help="the compact string to parse")
    prs.add_argument("--unit", default="", help="trailing unit to strip, for example B")
    prs.add_argument("--decimal-sep", default=".", help="decimal separator (default .)")
    prs.add_argument("--exact", action="store_true", help="print an exact decimal value")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "format":
            print(
                format_number(
                    args.value,
                    precision=args.precision,
                    style=args.style,
                    base=args.base,
                    unit=args.unit,
                    trim_zeros=not args.no_trim,
                    decimal_sep=args.decimal_sep,
                )
            )
        else:
            if args.exact:
                value = parse_decimal(args.text, unit=args.unit, decimal_sep=args.decimal_sep)
                print(_plain(value))
            else:
                print(parse(args.text, unit=args.unit, decimal_sep=args.decimal_sep))
    except (CompactError, ValueError) as error:
        print(f"compactnum: error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via the console script
    raise SystemExit(main())
