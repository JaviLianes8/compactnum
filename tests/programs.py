"""Seeded cases for two independent programs, and how to run them.

ICU (through Node.js ``Intl.NumberFormat`` compact notation, ``scripts/icu_compact.mjs``)
formats short-scale letters and words with half-up rounding and carry. GNU coreutils
``numfmt`` formats and reads IEC binary prefixes. Their output was captured into
``tests/fixtures`` with ``python tests/programs.py``; the tests compare against those
captures always and against the live programs when they are installed.
"""

from __future__ import annotations

import datetime
import json
import random
import re
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
NODE = shutil.which("node")
NUMFMT = shutil.which("numfmt")


def icu_cases(seed: int, count: int) -> list[list[object]]:
    """[value as decimal text, precision, "short" or "long"] below ICU's largest scale."""
    rng = random.Random(seed)
    cases: list[list[object]] = []
    while len(cases) < count:
        value = Decimal(rng.randrange(10 ** rng.randint(1, 15))).scaleb(-rng.randint(0, 6))
        if rng.random() < 0.3:
            value = -value
        if abs(value) < Decimal("999e12"):
            cases.append([str(value), rng.randint(0, 3), rng.choice(["short", "long"])])
    return cases


def run_icu(cases: list[list[object]]) -> tuple[dict[str, str], list[str]]:
    assert NODE is not None
    script = ROOT / "scripts" / "icu_compact.mjs"
    done = subprocess.run(
        [NODE, str(script)], input=json.dumps(cases), capture_output=True, encoding="utf-8"
    )
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    return result["versions"], result["results"]


def from_icu(output: str, display: str) -> str:
    """ICU's text in compactnum's spelling: lower-case k, and no sign on a zero."""
    if display == "short":
        output = output.replace("K", "k")
    if re.fullmatch(r"-0(\.0*)?", output):
        output = output[1:]
    return output


def numfmt_format_cases(seed: int, count: int) -> list[list[int]]:
    """[integer below 2**52, precision]: numfmt computes these exactly in long double."""
    rng = random.Random(seed)
    return [
        [rng.choice([1, -1]) * rng.randrange(2 ** rng.randint(1, 52)), rng.randint(0, 3)]
        for _ in range(count)
    ]


def run_numfmt_format(cases: list[list[int]]) -> list[str]:
    assert NUMFMT is not None
    outputs = []
    for precision in range(4):
        values = [str(value) for value, p in cases if p == precision]
        command = [NUMFMT, "--to=iec-i", "--round=nearest", f"--format=%.{precision}f", "--"]
        done = subprocess.run(command + values, capture_output=True, text=True, check=True)
        outputs.append(iter(done.stdout.split()))
    return [next(outputs[p]) for _, p in cases]


def numfmt_parse_cases(seed: int, count: int) -> list[str]:
    """Compact IEC text whose value is a whole number (a dyadic mantissa)."""
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        power = rng.randint(1, 5)  # numfmt prints results below 2**63 only
        mantissa = Decimal(rng.randrange(1, 1024 * 2**10)) / 2**10
        sign = rng.choice(["", "-"])
        cases.append(f"{sign}{mantissa}{' KMGTPE'[power]}i")
    return cases


def run_numfmt_parse(cases: list[str]) -> list[str]:
    assert NUMFMT is not None
    done = subprocess.run(
        [NUMFMT, "--from=iec-i", "--", *cases], capture_output=True, text=True, check=True
    )
    return done.stdout.split()


def capture() -> None:
    """Write the fixtures from the live programs."""
    FIXTURES.mkdir(exist_ok=True)
    cases = icu_cases(2026, 3000)
    versions, outputs = run_icu(cases)
    today = datetime.date.today().isoformat()
    icu = {
        "program": versions,
        "captured": today,
        "cases": [[*case, out] for case, out in zip(cases, outputs, strict=True)],
    }
    (FIXTURES / "icu-compact-en.json").write_text(json.dumps(icu) + "\n", newline="\n")
    version = subprocess.run([NUMFMT or "numfmt", "--version"], capture_output=True, text=True)
    formats = numfmt_format_cases(2026, 2000)
    texts = numfmt_parse_cases(2026, 1000)
    numfmt = {
        "program": version.stdout.splitlines()[0],
        "captured": today,
        "commands": ["numfmt --to=iec-i --round=nearest --format=%.<p>f", "numfmt --from=iec-i"],
        "format": [
            [*case, out] for case, out in zip(formats, run_numfmt_format(formats), strict=True)
        ],
        "parse": [[text, out] for text, out in zip(texts, run_numfmt_parse(texts), strict=True)],
    }
    (FIXTURES / "numfmt-iec.json").write_text(json.dumps(numfmt) + "\n", newline="\n")


if __name__ == "__main__":
    capture()
