"""The README and GUIDE examples run and print what their comments say; docs agree."""

from __future__ import annotations

import contextlib
import io
import itertools
import re
from pathlib import Path

import compactnum

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
GUIDE = (ROOT / "GUIDE.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def _python_blocks(text: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)


def _expected_output(block: str) -> list[str]:
    """Comment lines right after a print (or after the block holding it) are its output."""
    expected: list[str] = []
    printing = False
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and printing:
            expected.append(stripped[2:])
            continue
        if not stripped:
            printing = False
        else:
            printing = stripped.startswith("print(") or (printing and not stripped.startswith("#"))
    return expected


def _run_blocks(text: str) -> int:
    checked = 0
    for block in _python_blocks(text):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(block, "docs", "exec"), {"__name__": "docs"})
        expected = _expected_output(block)
        assert expected, block
        assert out.getvalue().splitlines() == expected
        checked += len(expected)
    return checked


def test_every_readme_example_runs_and_prints_its_comment() -> None:
    assert len(_python_blocks(README)) == 3
    assert _run_blocks(README) == 10


def test_every_guide_example_runs_and_prints_its_comment() -> None:
    assert len(_python_blocks(GUIDE)) == 4
    assert _run_blocks(GUIDE) == 15


def test_the_readme_command_line_transcript_is_real(capsys: object) -> None:
    from compactnum._cli import main

    transcript = README.split("## Command line", 1)[1].split("```", 2)[1]
    commands = re.findall(r"^\$ compactnum (.*)\n(.*)$", transcript, flags=re.MULTILINE)
    assert len(commands) == 4
    for command, output in commands:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            assert main(command.split()) == 0
        assert buffer.getvalue() == output + "\n"


def test_the_links_are_absolute() -> None:
    for text in (README, GUIDE):
        for target in re.findall(r"\]\(([^)]+)\)", text):
            assert target.startswith("https://"), target
    assert "/blob/main/GUIDE.md" in README and "/blob/main/CHANGELOG.md" in README


def test_the_readme_carries_the_certification_badge() -> None:
    badge = (
        "[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)]"
        "(https://lianes8studio.com/certified)"
    )
    assert README.splitlines()[2] == badge


def test_the_api_table_lists_every_public_name() -> None:
    table = README.split("## API", 1)[1].split("\n## ", 1)[0]
    for name in compactnum.__all__:
        assert f"`{name}" in table, name


def test_changelog_has_a_dated_entry_for_this_version() -> None:
    assert f"## [{compactnum.__version__}] - 2026-10-22" in CHANGELOG


def test_no_em_dash_anywhere_in_the_tree() -> None:
    suffixes = {".py", ".md", ".toml", ".ps1", ".txt", ".json", ".mjs", ".cfg"}
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if parts[:2] == ("tests", "upstream") and path.name != "MANIFEST.json":
            continue
        if any(part.startswith(".") or part in ("__pycache__", "build", "dist") for part in parts):
            continue
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_source_files_stay_under_two_hundred_lines() -> None:
    for path in [*(ROOT / "src").rglob("*.py"), *(ROOT / "tests").glob("*.py")]:
        lines = path.read_text(encoding="utf-8").count("\n")
        assert lines <= 200, path


def test_pairs_of_print_and_output_line_up() -> None:
    for block in _python_blocks(README) + _python_blocks(GUIDE):
        prints = sum(1 for line in block.splitlines() if line.strip().startswith("print("))
        assert prints <= len(_expected_output(block))
    assert list(itertools.islice(_expected_output("print(1)\n# 1\n"), 2)) == ["1"]
