"""Command-line details: negative values, option checks, exact reading, lost output."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from compactnum._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def _run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["format", "-1e3"], "-1k"),
        (["format", "-1.2e3"], "-1.2k"),
        (["format", "-1.5E+3"], "-1.5k"),
        (["format", "-1."], "-1"),
        (["format", "-1_000"], "-1k"),
        (["format", "-.5"], "-0.5"),
        (["format", "-1250", "--precision", "2"], "-1.25k"),
        (["parse", "-1.2k"], "-1200"),
        (["parse", "-1.5KiB", "--unit", "B"], "-1536"),
        (["parse", "--", "-1.2k"], "-1200"),
    ],
)
def test_negative_values_need_no_separator_on_any_python(
    capsys: pytest.CaptureFixture[str], args: list[str], expected: str
) -> None:
    assert _run(capsys, *args) == (0, expected + "\n", "")


def test_negative_values_work_as_a_real_subprocess() -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    for args, expected in ((["format", "-1e3"], b"-1k"), (["parse", "-1.2k"], b"-1200")):
        done = subprocess.run(
            [sys.executable, "-m", "compactnum", *args], capture_output=True, env=env, timeout=60
        )
        assert (done.returncode, done.stdout.strip(), done.stderr) == (0, expected, b"")


@pytest.mark.parametrize(
    ("args", "flag"),
    [
        (["format", "5", "--precision", "-1"], "--precision"),
        (["format", "5", "--precision", "4301"], "--precision"),
        (["format", "5", "--precision", "abc"], "--precision"),
        (["format", "5", "--decimal-sep", "ab"], "--decimal-sep"),
        (["format", "5", "--decimal-sep", "k"], "--decimal-sep"),
        (["parse", "5k", "--decimal-sep", "ab"], "--decimal-sep"),
        (["parse", "5k", "--decimal-sep", ""], "--decimal-sep"),
    ],
)
def test_invalid_option_values_are_usage_errors_naming_the_flag(
    capsys: pytest.CaptureFixture[str], args: list[str], flag: str
) -> None:
    code, out, err = _run(capsys, *args)
    assert (code, out) == (2, "")
    assert f"argument {flag}" in err and "decimal_sep" not in err
    assert len(err) < 1500


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (
            ["format", "5", "--precision", "abc"],
            "argument --precision: invalid integer value: 'abc'",
        ),
        (["format", "5", "--precision", "-1"], "argument --precision: must be between 0 and 4300"),
        (
            ["format", "5", "--precision", "4301"],
            "argument --precision: must be between 0 and 4300",
        ),
    ],
)
def test_precision_usage_errors_say_what_is_wrong(
    capsys: pytest.CaptureFixture[str], args: list[str], message: str
) -> None:
    code, out, err = _run(capsys, *args)
    assert (code, out) == (2, "") and err.rstrip().endswith(message), err


@pytest.mark.parametrize("value", ["-inf", "-Infinity", "-INF", "-nan", "-NaN", "-sNaN", "-nan12"])
def test_negative_infinities_and_nans_are_values_rejected_as_not_finite(
    capsys: pytest.CaptureFixture[str], value: str
) -> None:
    expected = (1, "", "compactnum: error: value must be finite\n")
    assert _run(capsys, "format", value) == expected
    assert _run(capsys, "format", "--", value) == expected
    assert _run(capsys, "format", value[1:]) == expected


@pytest.mark.parametrize(
    "args",
    [
        ["parse", "-k"],
        ["parse", "-B"],
        ["format", "-x"],
        ["format", "-information"],
        ["format", "-nancy"],
        ["parse", "1k-B", "--unit", "-B"],
        ["format", "5", "--unit", "-B"],
    ],
)
def test_a_dash_and_text_that_is_no_number_stays_an_option(
    capsys: pytest.CaptureFixture[str], args: list[str]
) -> None:
    code, out, err = _run(capsys, *args)
    assert (code, out) == (2, "") and "usage:" in err


@pytest.mark.parametrize("word", ["-information", "-nancy", "-infk", "-nanB", "-k"])
@pytest.mark.parametrize(("command", "argument"), [("parse", "text"), ("format", "value")])
def test_a_dash_and_a_word_is_an_option_so_the_value_is_missing(
    capsys: pytest.CaptureFixture[str], command: str, argument: str, word: str
) -> None:
    code, out, err = _run(capsys, command, word)
    assert (code, out) == (2, "")
    assert err.rstrip().endswith(f"the following arguments are required: {argument}"), err


def test_an_option_value_that_starts_with_a_dash_takes_an_equals_sign() -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    for args, expected in (
        (["parse", "1k-B", "--unit=-B"], b"1000"),
        (["format", "5", "--unit=-B"], b"5-B"),
        (["parse", "--unit=-B", "--", "-1k-B"], b"-1000"),
    ):
        done = subprocess.run(
            [sys.executable, "-m", "compactnum", *args], capture_output=True, env=env, timeout=60
        )
        assert (done.returncode, done.stdout.strip(), done.stderr) == (0, expected, b"")


def test_option_values_at_their_limits_are_accepted(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "format", "1200", "--precision", "4300", "--no-trim")
    assert (code, out) == (0, "1.2" + "0" * 4299 + "k\n")
    assert _run(capsys, "format", "1500", "--precision", "0") == (0, "2k\n", "")
    assert _run(capsys, "parse", "1;5k", "--decimal-sep", ";") == (0, "1500\n", "")


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["format", "1.15"], "1.2"),
        (["format", "0.15"], "0.2"),
        (["format", "2.675", "--precision", "2"], "2.68"),
        (
            ["format", "123456789012345678901234567", "--precision", "20"],
            "123.45678901234567890123Sp",
        ),
        (["format", "1e400"], "1" + "0" * 370 + "No"),
    ],
)
def test_the_value_is_read_exactly(
    capsys: pytest.CaptureFixture[str], args: list[str], expected: str
) -> None:
    assert _run(capsys, *args) == (0, expected + "\n", "")


class _Closed(io.StringIO):
    """A stdout whose reader went away: every write fails."""

    def write(self, text: str) -> int:
        raise BrokenPipeError(32, "Broken pipe")


@pytest.mark.parametrize("args", [["--version"], ["--help"], ["format", "12"]])
def test_lost_output_exits_one(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> None:
    monkeypatch.setattr(sys, "stdout", _Closed())
    assert main(args) == 1
