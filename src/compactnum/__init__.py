"""Two-way compact number notation: format numbers and parse them back.

``compactnum`` turns numbers into short, human strings (``1200`` becomes
``"1.2k"``) and reads them back (``"1.2k"`` becomes ``1200``). It is small,
typed and dependency-free, with configurable precision and half-up rounding,
short-scale, SI, word and binary (IEC) styles, optional units and decimal
separators, an exact :class:`~decimal.Decimal` parser, and a ``compactnum``
command-line tool.

Examples:
    >>> import compactnum
    >>> compactnum.format(1200)
    '1.2k'
    >>> compactnum.parse("1.2k")
    1200
"""

from ._errors import CompactError
from ._format import format
from ._parse import parse, parse_decimal

# Pickles and tracebacks name the public module, not the private one.
CompactError.__module__ = __name__

__version__ = "1.0.0"

__all__ = ["CompactError", "format", "parse", "parse_decimal"]
