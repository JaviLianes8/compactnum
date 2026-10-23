"""The command line, in process and as a real subprocess (``python -m compactnum``)."""

from __future__ import annotations

import decimal
import os
import subprocess
import sys
from pathlib import Path

import pytest

from compactnum import __version__
from compactnum._cli import main

OMEGA = chr(0x3A9)
NINES = decimal.Decimal("9" * 4300)
SRC = Path(__file__).resolve().parents[1] / "src"


def _run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["format", "1200"], "1.2k"),
        (["format", "1536", "--base", "1024", "--unit", "B", "--precision", "2"], "1.5KiB"),
        (["format", "3500000", "--style", "long"], "3.5 million"),
        (["format", "1500000000", "--style", "metric"], "1.5G"),
        (["format", "999999999999999999", "--style", "metric"], "1E"),
        (["format", "123456789012345678901234567890.5", "--precision", "3"], "123.457Oc"),
        (["format", "-1250"], "-1.3k"),
        (["format", "1e3", "--no-trim"], "1.0k"),
        (["format", "1500", "--decimal-sep", ","], "1,5k"),
        (["format", "1.05"], "1.1"),
        (["parse", "1.2k"], "1200"),
        (["parse", "1.2345k"], "1234.5"),
        (["parse", "1.2345k", "--exact"], "1234.5"),
        (["parse", "0.1"], "0.1"),
        (["parse", "1.5KiB", "--unit", "B"], "1536"),
        (["parse", "1,5k", "--decimal-sep", ","], "1500"),
        (["parse", "--", "-1.2k"], "-1200"),
        (["parse", "9" * 4300 + "Yi"], f"{decimal.Context(prec=5000).multiply(NINES, 2**80):f}"),
    ],
    ids=lambda item: str(item)[:30],
)
def test_prints_the_result_and_exits_zero(
    capsys: pytest.CaptureFixture[str], args: list[str], expected: str
) -> None:
    assert _run(capsys, *args) == (0, expected + "\n", "")


def test_parse_exact_keeps_every_digit(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "parse", "1.123456789012345678901234567k", "--exact")
    assert (code, out) == (0, "1123.456789012345678901234567\n")
    code, out, _ = _run(capsys, "parse", "1.123456789012345678901234567k")
    assert (code, out) == (0, "1123.4567890123458\n")


@pytest.mark.parametrize(
    "args",
    [
        ["parse", "nonsense"],
        ["parse", "1.5Ki", "--unit", "B"],
        ["parse", "9" * 400 + ".3Yi"],
        ["format", "nan"],
        ["format", "1" * 5000],
        ["format", "1e4300"],
    ],
)
def test_rejected_values_exit_one_with_a_short_message(
    capsys: pytest.CaptureFixture[str], args: list[str]
) -> None:
    code, out, err = _run(capsys, *args)
    assert (code, out) == (1, "")
    assert err.startswith("compactnum: error: ") and err.endswith("\n")
    assert len(err) < 400


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["format"],
        ["format", "abc"],
        ["format", "1", "--style", "fancy"],
        ["format", "1", "--base", "2"],
        ["format", "1", "--precision", "1" * 5000],
        ["format", "x" * 100_000],
        ["frobnicate"],
    ],
)
def test_usage_errors_exit_two_with_a_bounded_message(
    capsys: pytest.CaptureFixture[str], args: list[str]
) -> None:
    code, out, err = _run(capsys, *args)
    assert (code, out) == (2, "")
    assert "usage: compactnum" in err and len(err) < 1500


def test_too_large_for_a_float_suggests_exact(capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = _run(capsys, "parse", "1" * 300 + ".3Yi")
    assert code == 1 and "--exact" in err
    assert _run(capsys, "parse", "1" * 300 + ".3Yi", "--exact")[0] == 0


def test_version_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, "--version") == (0, f"compactnum {__version__}\n", "")
    code, out, _ = _run(capsys, "--help")
    assert code == 0 and "compactnum parse -1.2k " in out
    code, out, _ = _run(capsys, "format", "--help")
    assert code == 0 and "{short,metric,long,si}" in out and "(default short)" in out


def _subprocess(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[bytes]:
    variables = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "", "PYTHONUTF8": ""}
    variables.update(env or {})
    command = [sys.executable, "-m", "compactnum", *args]
    return subprocess.run(command, capture_output=True, env=variables, timeout=60, check=False)


def test_module_entry_point_runs_as_a_subprocess() -> None:
    done = _subprocess("format", "7200000", "--style", "long")
    assert (done.returncode, done.stdout.strip(), done.stderr) == (0, b"7.2 million", b"")
    done = _subprocess("parse", "7.2 million")
    assert (done.returncode, done.stdout.strip()) == (0, b"7200000")
    done = _subprocess("parse", "bad")
    assert done.returncode == 1 and done.stdout == b""


def test_unencodable_output_is_reported_not_garbled() -> None:
    done = _subprocess("format", "1500", "--unit", OMEGA, env={"PYTHONIOENCODING": "ascii"})
    assert done.returncode == 1 and done.stdout == b""
    assert b"cannot be written as ascii" in done.stderr
    done = _subprocess("parse", OMEGA + "k", env={"PYTHONIOENCODING": "ascii"})
    assert done.returncode == 1 and b"\\u03a9k" in done.stderr
    done = _subprocess("format", "1500", "--unit", OMEGA, env={"PYTHONIOENCODING": "utf-8"})
    assert done.stdout.decode("utf-8").strip() == "1.5k" + OMEGA


def test_a_closed_output_pipe_exits_quietly() -> None:
    code = (
        "import subprocess, sys\n"
        "p = subprocess.Popen([sys.executable, '-m', 'compactnum', 'format', '12'],"
        " stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n"
        "p.stdout.close()\n"
        "err = p.stderr.read()\n"
        "print(p.wait(), len(err))\n"
    )
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, env=env, timeout=60)
    status, length = done.stdout.split()
    assert status in (b"0", b"1") and length == b"0"
