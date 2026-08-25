"""Grade your exercise implementations.

Run from the code/ directory:

    python3 exercises/check.py            # all exercises
    python3 exercises/check.py ex03       # one exercise

Each exercise is graded by the same tests the course's CI runs against the
reference solutions — if it passes here, it passes.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

CODE_DIR = pathlib.Path(__file__).resolve().parent.parent


def discover() -> list[str]:
    return sorted(
        p.stem.removeprefix("test_")
        for p in (CODE_DIR / "exercises" / "tests").glob("test_ex*.py")
    )


def run_one(name: str) -> tuple[str, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", f"exercises.tests.test_{name}", "-q"],
        cwd=CODE_DIR, capture_output=True, text=True, timeout=120,
    )
    out = proc.stdout + proc.stderr
    if proc.returncode == 0:
        return "pass", ""
    if "NotImplementedError" in out:
        return "todo", "not started (skeleton still raises NotImplementedError)"
    first_fail = next(
        (line.strip() for line in out.splitlines()
         if line.startswith(("FAIL:", "ERROR:"))), "tests failing",
    )
    return "fail", first_fail


def main() -> int:
    wanted = sys.argv[1:]
    names = [n for n in discover() if not wanted or n in wanted]
    if not names:
        print(f"No exercises matching {wanted}. Available: {', '.join(discover())}")
        return 2

    icons = {"pass": "PASS", "todo": "----", "fail": "FAIL"}
    passed = 0
    print()
    for name in names:
        status, detail = run_one(name)
        passed += status == "pass"
        line = f"  [{icons[status]}]  {name}"
        if detail:
            line += f"   {detail}"
        print(line)
    print(f"\n  {passed}/{len(names)} passing")
    if passed < len(names):
        print("  Each exercise's docstring names the lesson it comes from.")
    return 0 if passed == len(names) else 1


if __name__ == "__main__":
    raise SystemExit(main())
