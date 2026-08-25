"""Loads an exercise implementation from EXERCISE_IMPL_DIR.

Default: the exercises directory itself (the learner's skeletons).
The course validator sets EXERCISE_IMPL_DIR to exercises/solutions to prove
every exercise is solvable — the same tests, run against the reference answers.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import pathlib


def load(name: str):
    base = pathlib.Path(os.environ.get(
        "EXERCISE_IMPL_DIR", str(pathlib.Path(__file__).parent)
    ))
    path = base / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"No implementation at {path}")
    # Deterministic module name (Python's str hash is salted per process).
    digest = hashlib.sha256(str(base.resolve()).encode()).hexdigest()[:8]
    unique = f"exercise_{name}_{digest}"
    spec = importlib.util.spec_from_file_location(unique, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
