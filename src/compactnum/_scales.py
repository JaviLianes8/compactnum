"""Canonical magnitude scales shared by formatting and parsing."""

from __future__ import annotations

# Exponent, SI letter, long word. Ordered by ascending exponent. This single
# table keeps the two directions in sync: format reads the suffixes, parse reads
# the exponents.
SCALES: tuple[tuple[int, str, str], ...] = (
    (3, "k", "thousand"),
    (6, "M", "million"),
    (9, "B", "billion"),
    (12, "T", "trillion"),
)
