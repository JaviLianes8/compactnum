"""Command-line plumbing: bounded usage errors, safe encoding, quiet exits on closed pipes."""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

#: Usage and data error messages are cut here, so a huge argument is never echoed back.
MESSAGE_LIMIT = 300

# argparse matches this at the start of an argument; the words are anchored to its end.
_NEGATIVE_VALUE = re.compile(r"-(?:\.?\d|(?:inf|infinity|s?nan\d*)$)", re.IGNORECASE)


def bounded(message: str) -> str:
    """Cut ``message`` to :data:`MESSAGE_LIMIT` characters."""
    if len(message) > MESSAGE_LIMIT:
        return message[:MESSAGE_LIMIT] + "..."
    return message


def _silence(stream: object) -> None:
    """Point a stream's descriptor at the null device after its reader went away.

    Python flushes the streams at exit; on a closed pipe that flush fails and the
    process exits 120 with a warning. Redirecting the descriptor makes later writes succeed.
    """
    try:
        fd = stream.fileno()  # type: ignore[attr-defined]
    except (AttributeError, OSError, ValueError):
        return
    null = os.open(os.devnull, os.O_WRONLY)
    if null != fd:  # a closed descriptor is reused by open(): then it already is the null device
        os.dup2(null, fd)
        os.close(null)


def finish(code: int) -> int:
    """Flush both streams and return ``code``; a stream whose reader left is silenced."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except (AttributeError, OSError, ValueError):
            _silence(stream)
    return code


def write(stream_name: str, text: str) -> bool:
    """Write ``text`` to stdout or stderr; return False when it could not be written.

    Python's stderr escapes what its encoding cannot hold. Text that stdout cannot hold
    is reported on stderr instead, so a result is never silently changed.
    """
    stream = sys.stdout if stream_name == "stdout" else sys.stderr
    try:
        stream.write(text)
        stream.flush()
    except UnicodeEncodeError:
        name = getattr(stream, "encoding", None)
        hint = "set PYTHONIOENCODING=utf-8 to write it"
        write("stderr", f"compactnum: error: the result cannot be written as {name}; {hint}\n")
        return False
    except (AttributeError, OSError, ValueError):
        return False  # finish() silences the stream when it flushes it
    return True


class Parser(argparse.ArgumentParser):
    """An argument parser whose errors are bounded and survive a closed stream."""

    lost_output = False  # set when help or version text could not be written

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Up to 3.13 argparse takes "-1e3" or "-1.2k" for an option; 3.14 reads any
        # "-digit" or "-.digit" as a value. No option here looks like a number, so that
        # rule is set on every version and they all behave the same. It also covers the
        # whole words Decimal reads after a minus ("-inf", "-nan"), so "format -inf"
        # reports a value that is not finite; any other dash and letter stays an option.
        self._negative_number_matcher = _NEGATIVE_VALUE

    def _get_values(self, action: argparse.Action, arg_strings: list[str]) -> Any:
        # On 3.10, 3.11 before 3.11.8 and 3.12 before 3.12.2, argparse drops "--" from an
        # option's values, so "--unit=--" gave the option an empty list that skipped its
        # checks; read it as the text "--", as later versions do.
        if action.option_strings and action.nargs is None and arg_strings == ["--"]:
            value = self._get_value(action, "--")
            self._check_value(action, value)
            return value
        return super()._get_values(action, arg_strings)

    def error(self, message: str) -> NoReturn:
        self.exit(2, f"{self.format_usage()}{self.prog}: error: {bounded(message)}\n")

    def exit(self, status: int = 0, message: str | None = None) -> NoReturn:
        if message:
            write("stderr", message)
        raise SystemExit(finish(1 if status == 0 and self.lost_output else status))

    def _print_message(self, message: str, file: SupportsWrite[str] | None = None) -> None:
        if message and not write("stderr" if file is sys.stderr else "stdout", message):
            self.lost_output = True
