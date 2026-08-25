#!/usr/bin/env python3
"""The course's own harness: every check that gates a change, in one command.

    python3 tools/validate_course.py            # everything
    python3 tools/validate_course.py --fast     # skip subprocess-heavy checks

Checks:
  1. library tests        (code/tests — the course's claims, falsifiable)
  2. examples run         (code/examples/*.py, offline by design)
  3. internal links       (every [text](path) resolves)
  4. task alignment       (every Hands-On Task has a matching solution)
  5. prose python         (every ```python block in the lessons parses)
  6. exercises solvable   (reference solutions pass their tests, 10/10)
  7. exercises non-vacuous(skeletons must NOT pass)
  8. labs + adapters parse (they need an API key, so syntax only)
  9. mermaid              (delegated to tools/mermaid/validate.mjs if node_modules
                           is installed there; otherwise reported as skipped)

Exit code 0 only if every executed check passes. The course preaches "run the
evals on every harness change" — this file is that doctrine applied to itself.
"""

from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
CODE = ROOT / "code"
SKIP_DIRS = {".git", "node_modules", "__pycache__"}

RESULTS: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"  [{'ok' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def markdown_files() -> list[pathlib.Path]:
    return [
        p for p in sorted(ROOT.rglob("*.md"))
        if not SKIP_DIRS & set(p.parts)
    ]


def check_library_tests() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-q"],
        cwd=CODE, capture_output=True, text=True, timeout=600,
    )
    ran = re.search(r"Ran (\d+) tests", proc.stdout + proc.stderr)
    record("library tests", proc.returncode == 0,
           f"{ran.group(1) if ran else '?'} tests")


def check_examples() -> None:
    failed = []
    for example in sorted((CODE / "examples").glob("*.py")):
        proc = subprocess.run([sys.executable, str(example)], cwd=CODE,
                              capture_output=True, timeout=120)
        if proc.returncode != 0:
            failed.append(example.name)
    record("examples run", not failed, ", ".join(failed) or f"{len(list((CODE / 'examples').glob('*.py')))} examples")


def check_links() -> None:
    broken = []
    for md in markdown_files():
        for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", md.read_text()):
            target = m.group(2)
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = urllib.parse.unquote(target.split("#")[0])
            if path and not (md.parent / path).resolve().exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    record("internal links", not broken, broken[0] if broken else f"{len(markdown_files())} files")


def check_task_alignment() -> None:
    mismatched = []
    for module in sorted((ROOT / "Lessons").iterdir()):
        solutions = module / "SOLUTIONS.md"
        if not solutions.exists():
            continue
        solved = set(re.findall(r"^#### \*\*Task: (.+?)\*\*", solutions.read_text(), re.M))
        asked: set[str] = set()
        for lesson in sorted(module.glob("Lesson*.md")):
            asked |= set(re.findall(r"^### \*\*(?:Hands-On|Final) Task: (.+?)\*\*",
                                    lesson.read_text(), re.M))
        if solved != asked:
            mismatched.append(f"{module.name}: {sorted(solved ^ asked)}")
    record("task alignment", not mismatched, mismatched[0] if mismatched else "all modules")


def check_prose_python() -> None:
    bad, total = [], 0
    for md in markdown_files():
        for i, block in enumerate(re.findall(r"```python\n([\s\S]*?)```", md.read_text()), 1):
            total += 1
            try:
                ast.parse(block)
            except SyntaxError as exc:
                bad.append(f"{md.relative_to(ROOT)} block {i}: {exc.msg}")
    record("prose python blocks", not bad, bad[0] if bad else f"{total} blocks")


def exercise_names() -> list[str]:
    return sorted(p.stem.removeprefix("test_")
                  for p in (CODE / "exercises" / "tests").glob("test_ex*.py"))


def run_exercise(name: str, impl_dir: pathlib.Path) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", f"exercises.tests.test_{name}", "-q"],
        cwd=CODE, capture_output=True, timeout=120,
        env={**os.environ, "EXERCISE_IMPL_DIR": str(impl_dir)},
    )
    return proc.returncode == 0


def check_exercises_solvable() -> None:
    solutions = CODE / "exercises" / "solutions"
    failing = [n for n in exercise_names() if not run_exercise(n, solutions)]
    record("exercise solutions pass", not failing,
           ", ".join(failing) or f"{len(exercise_names())}/{len(exercise_names())}")


def check_exercises_non_vacuous() -> None:
    skeletons = CODE / "exercises"
    vacuous = [n for n in exercise_names() if run_exercise(n, skeletons)]
    record("exercise skeletons do NOT pass", not vacuous,
           ", ".join(vacuous) or "all require real work")


def check_labs_parse() -> None:
    bad = []
    for py in list((CODE / "labs").glob("*.py")) + [CODE / "ce" / "adapters.py"]:
        if not py.exists():
            continue
        try:
            ast.parse(py.read_text())
        except SyntaxError as exc:
            bad.append(f"{py.name}: {exc.msg}")
    record("labs + adapter parse", not bad, bad[0] if bad else "syntax only (labs need a key)")


def check_mermaid() -> None:
    mermaid_dir = ROOT / "tools" / "mermaid"
    if not (mermaid_dir / "node_modules").exists():
        print("  [skip] mermaid — run `npm install` in tools/mermaid to enable")
        return
    proc = subprocess.run(["node", str(mermaid_dir / "validate.mjs")],
                          capture_output=True, text=True, timeout=600)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    record("mermaid diagrams", proc.returncode == 0, tail[-1] if tail else "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true",
                        help="skip examples, exercises, and mermaid")
    args = parser.parse_args()

    print("validating the course against its own doctrine:\n")
    check_library_tests()
    check_links()
    check_task_alignment()
    check_prose_python()
    check_labs_parse()
    if not args.fast:
        check_examples()
        check_exercises_solvable()
        check_exercises_non_vacuous()
        check_mermaid()

    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed"
          + (f" — FAILED: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
