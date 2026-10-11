"""In-process tests for the argparse command-line interface."""

import pytest

from compactnum import __version__
from compactnum._cli import main


def test_format_prints_compact_notation(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["format", "1200"]) == 0
    assert capsys.readouterr().out.strip() == "1.2k"


def test_format_honours_every_option(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["format", "1536", "--base", "1024", "--unit", "B", "--precision", "2"])
    assert code == 0
    assert capsys.readouterr().out.strip() == "1.5KiB"


def test_format_long_style(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["format", "3500000", "--style", "long"]) == 0
    assert capsys.readouterr().out.strip() == "3.5 million"


def test_format_keeps_integers_exact(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["format", "999999999999999999", "--style", "metric"]) == 0
    assert capsys.readouterr().out.strip() == "1E"


def test_parse_prints_a_number(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["parse", "1.2k"]) == 0
    assert capsys.readouterr().out.strip() == "1200"


def test_parse_exact_prints_a_decimal(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["parse", "1.5KiB", "--unit", "B", "--exact"]) == 0
    assert capsys.readouterr().out.strip() == "1536"


def test_parse_with_custom_separator(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["parse", "1,5k", "--decimal-sep", ","]) == 0
    assert capsys.readouterr().out.strip() == "1500"


def test_errors_go_to_stderr_with_exit_one(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["parse", "nonsense"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error" in captured.err.lower()


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out
