"""Real end-to-end test: pip-install the package editable into a throwaway
virtual environment and drive the installed ``compactnum`` console script.

No mocks and no import of the in-tree package. This proves that the console
entry point declared in ``pyproject.toml`` is wired correctly and that the real
executable produces the documented stdout and exit codes.
"""

import os
import subprocess
import venv
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def console_script(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a venv, install the package editable, return the console script."""
    env_dir = tmp_path_factory.mktemp("compactnum_e2e_venv")
    venv.create(env_dir, with_pip=True)
    bin_dir = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bin_dir / ("python.exe" if os.name == "nt" else "python")
    install = subprocess.run(
        [str(python), "-m", "pip", "install", "-e", str(PROJECT_ROOT), "--quiet"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert install.returncode == 0, install.stderr
    script = bin_dir / ("compactnum.exe" if os.name == "nt" else "compactnum")
    assert script.is_file(), f"console script not installed at {script}"
    return script


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(script), *args], capture_output=True, text=True, timeout=60)


def test_installed_script_formats(console_script: Path) -> None:
    result = _run(console_script, "format", "1200")
    assert result.returncode == 0
    assert result.stdout.strip() == "1.2k"


def test_installed_script_formats_binary_with_unit(console_script: Path) -> None:
    result = _run(console_script, "format", "1536", "--base", "1024", "--unit", "B")
    assert result.returncode == 0
    assert result.stdout.strip() == "1.5KiB"


def test_installed_script_parses(console_script: Path) -> None:
    result = _run(console_script, "parse", "3.5M")
    assert result.returncode == 0
    assert result.stdout.strip() == "3500000"


def test_installed_script_round_trips(console_script: Path) -> None:
    formatted = _run(console_script, "format", "7200000", "--style", "long")
    assert formatted.returncode == 0
    assert formatted.stdout.strip() == "7.2 million"
    parsed = _run(console_script, "parse", "7.2 million")
    assert parsed.returncode == 0
    assert parsed.stdout.strip() == "7200000"


def test_installed_script_reports_errors_on_stderr(console_script: Path) -> None:
    result = _run(console_script, "parse", "not-a-number")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "error" in result.stderr.lower()


def test_installed_script_reports_version(console_script: Path) -> None:
    result = _run(console_script, "--version")
    assert result.returncode == 0
    assert result.stdout.strip() == f"compactnum {_expected_version()}"


def test_module_entry_point_runs(console_script: Path) -> None:
    python = console_script.parent / ("python.exe" if os.name == "nt" else "python")
    result = subprocess.run(
        [str(python), "-m", "compactnum", "format", "1200"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "1.2k"


def _expected_version() -> str:
    text = (PROJECT_ROOT / "src" / "compactnum" / "__init__.py").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("__version__"):
            return line.split('"')[1]
    raise AssertionError("version not found")
