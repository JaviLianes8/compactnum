"""The parse error type and the bounded input excerpt quoted in error messages."""

from __future__ import annotations

#: Longest piece of caller input quoted in an error message.
EXCERPT = 40


class CompactError(ValueError):
    """Raised by :func:`compactnum.parse` and :func:`compactnum.parse_decimal` when
    the text is not compact notation they accept.

    It subclasses :class:`ValueError`, so ``except ValueError`` catches it too.
    Messages quote at most 40 characters of the input, so a hostile or huge
    string never ends up whole in a log.

    Examples:
        >>> from compactnum import CompactError, parse
        >>> try:
        ...     parse("1.2x")
        ... except CompactError as error:
        ...     print(error)
        unknown suffix: 'x'
        >>> isinstance(CompactError("bad"), ValueError)
        True
    """


def excerpt(text: str) -> str:
    """Quote ``text`` for an error message, cut to :data:`EXCERPT` characters."""
    if len(text) <= EXCERPT:
        return repr(text)
    return f"{text[:EXCERPT]!r}... ({len(text)} characters)"


def type_name(value: object) -> str:
    """Name the type of ``value`` for a message: ``int`` for a builtin, else ``module.qualname``.

    A NumPy boolean is named ``numpy.bool``, never a bare ``bool``; a huge name is cut.
    """
    kind = type(value)
    module = getattr(kind, "__module__", None)
    name = kind.__qualname__
    if isinstance(module, str) and module != "builtins":
        name = f"{module}.{name}"
    if len(name) > 2 * EXCERPT:
        return name[: 2 * EXCERPT] + "..."
    return name
