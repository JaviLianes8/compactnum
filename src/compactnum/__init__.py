"""Two-way compact number notation: format numbers and parse them back.

``compactnum`` turns numbers into short, human strings (``1200`` becomes
``"1.2k"``) and reads them back (``"1.2k"`` becomes ``1200``). It is small,
typed and dependency-free, with configurable precision and rounding, short,
metric, long and binary (IEC) styles, optional units and locale decimal
separators, an exact :class:`~decimal.Decimal` parser, and a ``compactnum``
command-line tool.
"""

from __future__ import annotations

from ._format import format
from ._parse import CompactError, parse, parse_decimal

__version__ = "0.2.0"

__all__ = ["CompactError", "format", "parse", "parse_decimal"]
