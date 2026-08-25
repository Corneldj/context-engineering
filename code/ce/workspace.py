"""Structured note-taking: agent state that lives outside the context window.

Module 4, Lesson 3. The test for what belongs here is simple: **if losing it
would make the agent redo work or repeat a mistake, it goes in a file.**

Compaction is lossy by construction. Anything held only in the conversation can
be summarized away. Anything written here survives compaction, a crash, and a
process restart — which turns the context window into a cache over durable
storage, where cache loss is an inconvenience rather than a catastrophe.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Workspace:
    """A file-backed agent workspace.

    The four canonical files map to the four things an agent cannot afford to
    lose. `blockers` is the one people forget, and its absence is why agents
    cheerfully retry an approach that already failed three times.
    """

    root: Path

    GOAL = "goal.md"
    PLAN = "plan.md"
    FINDINGS = "findings.md"
    BLOCKERS = "blockers.md"

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    # -- raw access --------------------------------------------------------

    def path(self, name: str) -> Path:
        """Resolve a name inside the workspace, refusing anything that escapes.

        Uses `is_relative_to`, not string prefix matching: a root of `/tmp/ws`
        string-prefixes `/tmp/ws-evil`, so the obvious `startswith` check lets a
        sibling directory through. Path containment is a path question.
        """
        root = self.root.resolve()
        p = (root / name).resolve()
        if not p.is_relative_to(root):
            raise ValueError(f"Refusing to touch a path outside the workspace: {name!r}")
        return p

    def read(self, name: str, default: str = "") -> str:
        p = self.path(name)
        return p.read_text(encoding="utf-8") if p.exists() else default

    def write(self, name: str, content: str) -> None:
        self.path(name).write_text(content, encoding="utf-8")

    def append(self, name: str, line: str) -> None:
        with self.path(name).open("a", encoding="utf-8") as fh:
            fh.write(line.rstrip("\n") + "\n")

    # -- the canonical four -------------------------------------------------

    def set_goal(self, goal: str) -> None:
        """Written once. Never rewritten — this is the anchor a long run drifts from."""
        if not self.path(self.GOAL).exists():
            self.write(self.GOAL, goal)

    @property
    def goal(self) -> str:
        return self.read(self.GOAL)

    def record_finding(self, fact: str, source: str) -> None:
        self.append(self.FINDINGS, f"- {fact}  [source: {source}]")

    def record_blocker(self, what: str, why: str) -> None:
        """What was tried, and why it failed. Read this before retrying anything."""
        self.append(self.BLOCKERS, f"- TRIED: {what}\n  FAILED: {why}")

    def set_plan(self, steps: list[dict[str, str]]) -> None:
        self.write(self.PLAN, json.dumps(steps, indent=2))

    def plan(self) -> list[dict[str, str]]:
        raw = self.read(self.PLAN)
        return json.loads(raw) if raw.strip() else []

    def mark(self, step_id: str, status: str) -> None:
        steps = self.plan()
        for step in steps:
            if step.get("id") == step_id:
                step["status"] = status
        self.set_plan(steps)

    # -- what the agent reads back every turn -------------------------------

    def brief(self) -> str:
        """The small, always-loaded slice of durable state.

        Deliberately excludes findings, which grow without bound — those are
        retrieved on demand. Goal, plan, and blockers are needed every turn and
        stay small.
        """
        parts = [f"## Goal\n{self.goal or '(not set)'}"]
        plan = self.plan()
        if plan:
            lines = "\n".join(
                f"- [{s.get('status', 'todo')}] {s.get('id', '?')}: {s.get('what', '')}"
                for s in plan
            )
            parts.append(f"## Plan\n{lines}")
        blockers = self.read(self.BLOCKERS).strip()
        if blockers:
            parts.append(f"## Do not retry these\n{blockers}")
        return "\n\n".join(parts)

    def is_resumable(self) -> bool:
        """Enough state on disk to continue rather than start over."""
        return self.path(self.GOAL).exists() and bool(self.plan())
