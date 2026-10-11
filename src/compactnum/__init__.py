"""Two-way compact number notation: format numbers and parse them back."""

from __future__ import annotations

from ._format import format
from ._parse import CompactError, parse

__version__ = "0.1.0"

__all__ = ["CompactError", "format", "parse"]
