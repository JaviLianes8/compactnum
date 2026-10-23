"""Build the wheel and sdist, install the wheel in a throwaway venv and use it from outside.

Slow and needs the ``build`` package, so it runs only with COMPACTNUM_E2E=1. Set
COMPACTNUM_DIST to a folder holding an already built wheel and sdist to test those
instead of building from this tree.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("COMPACTNUM_E2E") != "1", reason="set COMPACTNUM_E2E=1 to build and install"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources, inspect, pickle
from decimal import Decimal
import compactnum
from compactnum import CompactError, format, parse, parse_decimal

assert "site-packages" in compactnum.__file__, compactnum.__file__
assert compactnum.__version__ == importlib.metadata.version("compactnum") == "1.0.0"
assert sorted(compactnum.__all__) == sorted(n for n in dir(compactnum) if not n.startswith("_"))
assert importlib.resources.files("compactnum").joinpath("py.typed").is_file()
assert all("extra ==" in r for r in importlib.metadata.requires("compactnum") or [])
assert format(1200) == "1.2k" and format(999_999) == "1M" and format(-1250) == "-1.3k"
assert format(1536, base=1024, unit="B") == "1.5KiB"
assert format(10**30, style="metric") == "1Q" and format(10**27, style="long") == "1 octillion"
assert parse("1.2k") == 1200 and parse("1.2345k") == 1234.5
assert parse_decimal("1.5 KiB", unit="b") == Decimal(1536)
try:
    parse("1.2x")
except CompactError as error:
    assert isinstance(error, ValueError)
    assert str(pickle.loads(pickle.dumps(error))) == "unknown suffix: 'x'"
else:
    raise AssertionError("parse accepted 1.2x")
assert "precision: 'int' = 1" in str(inspect.signature(format))
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False, timeout=300
    )


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    given = os.environ.get("COMPACTNUM_DIST")
    if given:
        return Path(given)
    out = tmp_path_factory.mktemp("dist")
    built = _run(sys.executable, "-m", "build", "--outdir", out, ROOT)
    assert built.returncode == 0, built.stderr
    return out


def test_wheel_and_sdist_contents(dist: Path) -> None:
    (wheel,) = dist.glob("compactnum-1.0.0-py3-none-any.whl")
    (sdist,) = dist.glob("compactnum-1.0.0.tar.gz")
    names = zipfile.ZipFile(wheel).namelist()
    package = sorted(name for name in names if name.startswith("compactnum/"))
    modules = ["__init__", "__main__", "_cli", "_cli_io", "_errors", "_format", "_parse"]
    expected = [f"compactnum/{name}.py" for name in [*modules, "_scales", "_value"]]
    assert package == sorted([*expected, "compactnum/py.typed"])
    assert any(name.endswith(".dist-info/licenses/LICENSE") for name in names)
    metadata = next(name for name in names if name.endswith(".dist-info/METADATA"))
    text = zipfile.ZipFile(wheel).read(metadata).decode("utf-8")
    assert "Classifier: Development Status :: 5 - Production/Stable" in text
    assert "Requires-Python: >=3.10" in text
    requires = [line for line in text.splitlines() if line.startswith("Requires-Dist:")]
    assert requires and all(line.endswith("extra == 'dev'") for line in requires)
    with tarfile.open(sdist) as archive:
        listing = [name.split("/", 1)[1] for name in archive.getnames() if "/" in name]
    for present in ("LICENSE", "README.md", "CHANGELOG.md", "GUIDE.md", "src/compactnum/py.typed"):
        assert present in listing, present
    assert "tests/upstream/MANIFEST.json" in listing
    assert "tests/fixtures/icu-compact-en.json" in listing
    for name in listing:
        assert not name.startswith("tests/upstream/") or name.endswith("MANIFEST.json")
        assert not name.startswith(".") or name in (
            ".gitignore",
            ".gitattributes",
            ".github/FUNDING.yml",
        )
        assert "IMPROVEMENTS-round" not in name and "CERT-1.0" not in name
        assert "__pycache__" not in name and not name.endswith(".pyc")


def test_installed_wheel_end_to_end(dist: Path, tmp_path: Path) -> None:
    (wheel,) = dist.glob("compactnum-1.0.0-py3-none-any.whl")
    venv.create(tmp_path / "venv", with_pip=True)
    scripts = tmp_path / "venv" / ("Scripts" if sys.platform == "win32" else "bin")
    python = scripts / "python"
    installed = _run(python, "-m", "pip", "install", "-q", "--no-index", wheel)
    assert installed.returncode == 0, installed.stderr
    work = tmp_path / "work"  # an empty folder, so the source tree cannot shadow the install
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert (result.returncode, result.stdout.strip()) == (0, "e2e ok"), result.stderr
    script = scripts / ("compactnum.exe" if sys.platform == "win32" else "compactnum")
    cases = [
        (["format", "1536", "--base", "1024", "--unit", "B"], 0, "1.5KiB"),
        (["format", "7200000", "--style", "long"], 0, "7.2 million"),
        (["parse", "7.2 million"], 0, "7200000"),
        (["parse", "1.2345k", "--exact"], 0, "1234.5"),
        (["parse", "--", "-1.5Ki"], 0, "-1536"),
        (["--version"], 0, "compactnum 1.0.0"),
        (["parse", "bad"], 1, ""),
        (["format", "bad"], 2, ""),
    ]
    for args, code, out in cases:
        for command in ([script], [python, "-I", "-m", "compactnum"]):
            done = _run(*command, *args, cwd=work)
            assert (done.returncode, done.stdout.strip()) == (code, out), (args, done.stderr)
            assert ("error" in done.stderr) == (code != 0)
