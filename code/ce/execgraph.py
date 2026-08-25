"""Execution graphs: nodes, typed state, conditional edges, durable execution.

Module 9, Lesson 4. A minimal graph runtime, written to make the concepts
inspectable rather than to compete with a production framework.

What it demonstrates that a loop cannot:

* **Routing as a pure function of state** — testable in isolation, and (this is
  what Lessons 4-5 need) editable by something other than a human.
* **Checkpointing** — state persisted after every node, so a crashed run resumes
  from its last node instead of starting over.
* **Interrupts** — a human-approval node that genuinely suspends the run. The
  process can exit; approval resumes it days later.
* **Idempotence fencing** — side-effecting nodes must not re-run on replay.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path as FsPath
from typing import Any, Callable, Iterable

END = "__end__"
INTERRUPT = "__interrupt__"


class GraphError(ValueError):
    pass


class Interrupted(Exception):
    """Raised when the graph suspends at a human gate. Not a failure."""

    def __init__(self, node: str, state: dict, checkpoint_id: str):
        super().__init__(f"suspended at {node!r} awaiting approval")
        self.node = node
        self.state = state
        self.checkpoint_id = checkpoint_id


NodeFn = Callable[[dict], dict]
RouteFn = Callable[[dict], str]


@dataclass
class IdempotencyLedger:
    """Records completed side effects, durably and SEPARATELY from the checkpoint.

    This separation is the whole point. The dangerous window for a duplicate
    side effect is precisely when the process died *after* the effect landed but
    *before* the checkpoint was written — so a fence stored inside that
    checkpoint is not there when you need it. Write the key at the moment of the
    effect, to a store that survives independently.

    In production this is a row in your database, committed in the same
    transaction as the side effect, or the downstream service deduplicating on
    the key you send it.
    """

    root: FsPath | None = None
    _mem: set[str] = field(default_factory=set, init=False)

    def seen(self, key: str) -> bool:
        if self.root is None:
            return key in self._mem
        return (self.root / f"{_safe(key)}.done").exists()

    def record(self, key: str) -> None:
        if self.root is None:
            self._mem.add(key)
        else:
            self.root.mkdir(parents=True, exist_ok=True)
            (self.root / f"{_safe(key)}.done").write_text("")


def _safe(key: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in key)


@dataclass
class Checkpointer:
    """Durable state. The reason to adopt a graph runtime at all."""

    root: FsPath | None = None
    _mem: dict[str, dict] = field(default_factory=dict, init=False)

    def save(self, run_id: str, state: dict, next_node: str, completed: list[str]) -> None:
        # Deep-copy before storing. Storing the live objects means a later
        # mutation retroactively edits an already-written checkpoint -- so the
        # in-memory checkpointer silently lies about history, and a "crash"
        # appears to have saved work it never saved. The disk path is safe only
        # because json.dumps serializes; the memory path must copy explicitly.
        payload = {
            "state": deepcopy(state),
            "next_node": next_node,
            "completed": list(completed),
        }
        if self.root is None:
            self._mem[run_id] = payload
        else:
            self.root.mkdir(parents=True, exist_ok=True)
            (self.root / f"{run_id}.json").write_text(json.dumps(payload, indent=2))

    def load(self, run_id: str) -> dict | None:
        if self.root is None:
            return self._mem.get(run_id)
        p = self.root / f"{run_id}.json"
        return json.loads(p.read_text()) if p.exists() else None


@dataclass
class Node:
    name: str
    fn: NodeFn
    # A side-effecting node must not re-run on replay. If it declares an
    # idempotency key, the runtime skips it when that key is already recorded.
    idempotency_key: Callable[[dict], str] | None = None
    interrupt_before: bool = False
    # What to put in state when the node is skipped because its effect already
    # happened. Without this, downstream nodes see a state missing the fields
    # the skipped node would have written.
    on_skip: NodeFn | None = None


class StateGraph:
    def __init__(self, entry: str) -> None:
        self.entry = entry
        self.nodes: dict[str, Node] = {}
        self.static_edges: dict[str, str] = {}
        self.conditional: dict[str, RouteFn] = {}

    # -- construction ------------------------------------------------------

    def add_node(
        self,
        name: str,
        fn: NodeFn,
        *,
        idempotency_key: Callable[[dict], str] | None = None,
        interrupt_before: bool = False,
        on_skip: NodeFn | None = None,
    ) -> "StateGraph":
        self.nodes[name] = Node(name, fn, idempotency_key, interrupt_before, on_skip)
        return self

    def add_edge(self, src: str, dst: str) -> "StateGraph":
        self.static_edges[src] = dst
        return self

    def add_conditional_edges(self, src: str, route: RouteFn) -> "StateGraph":
        self.conditional[src] = route
        return self

    # -- static analysis ---------------------------------------------------

    def validate(self) -> list[str]:
        """Catch topology mistakes before running. Cheap, and it finds real bugs."""
        problems: list[str] = []
        if self.entry not in self.nodes:
            problems.append(f"entry node {self.entry!r} is not defined")
        for src, dst in self.static_edges.items():
            if src not in self.nodes:
                problems.append(f"edge from undefined node {src!r}")
            if dst not in self.nodes and dst != END:
                problems.append(f"edge to undefined node {dst!r}")
        for name in self.nodes:
            if name not in self.static_edges and name not in self.conditional:
                problems.append(f"node {name!r} has no outgoing edge — it is a dead end")
        reachable = self.reachable()
        for name in self.nodes:
            if name not in reachable:
                problems.append(f"node {name!r} is unreachable from {self.entry!r}")
        return problems

    def reachable(self) -> set[str]:
        """Static reachability. Conditional edges are opaque, so this is a
        lower bound unless routes are declared — see `declared_targets`."""
        seen: set[str] = set()
        frontier = [self.entry]
        while frontier:
            node = frontier.pop()
            if node in seen or node == END:
                continue
            seen.add(node)
            if node in self.static_edges:
                frontier.append(self.static_edges[node])
            for target in getattr(self.conditional.get(node), "targets", ()):
                frontier.append(target)
        return seen

    # -- execution ---------------------------------------------------------

    def run(
        self,
        state: dict,
        *,
        run_id: str = "run",
        checkpointer: Checkpointer | None = None,
        ledger: IdempotencyLedger | None = None,
        max_steps: int = 100,
        resume: bool = False,
        approvals: dict[str, bool] | None = None,
    ) -> dict:
        """Execute the graph, checkpointing after every node."""
        approvals = approvals or {}
        completed: list[str] = []
        current = self.entry

        if resume and checkpointer is not None:
            saved = checkpointer.load(run_id)
            if saved is not None:
                # Saved state is the base; caller-supplied keys override it.
                # A resume after fixing an environment problem must be able to
                # pass corrected inputs, or the run fails identically forever.
                state = {**saved["state"], **state}
                current = saved["next_node"]
                completed = saved["completed"]

        # Checkpoint the inputs before the first node runs. A run that dies on
        # its entry node should still be resumable with its original inputs.
        if checkpointer is not None and not resume:
            checkpointer.save(run_id, state, current, completed)

        for _ in range(max_steps):
            if current == END:
                return state
            node = self.nodes.get(current)
            if node is None:
                raise GraphError(f"no such node: {current!r}")

            if node.interrupt_before and not approvals.get(current):
                if checkpointer is not None:
                    checkpointer.save(run_id, state, current, completed)
                raise Interrupted(current, state, run_id)

            # Idempotence fence: never re-run a side-effecting node on replay.
            key = node.idempotency_key(state) if node.idempotency_key else None
            marker = f"{node.name}:{key}" if key is not None else None
            already_done = marker is not None and (
                marker in completed or (ledger is not None and ledger.seen(marker))
            )
            if already_done:
                state = {**state, **(node.on_skip(state) if node.on_skip else {})}
            else:
                state = {**state, **(node.fn(state) or {})}
                if marker is not None:
                    # Record the effect BEFORE the checkpoint. If the process
                    # dies in between, the ledger is what saves you.
                    if ledger is not None:
                        ledger.record(marker)
                    completed.append(marker)
                else:
                    completed.append(node.name)

            current = self._next(node.name, state)
            if checkpointer is not None:
                checkpointer.save(run_id, state, current, completed)

        raise GraphError(f"step limit ({max_steps}) reached — likely an unterminated cycle")

    def _next(self, name: str, state: dict) -> str:
        if name in self.conditional:
            return self.conditional[name](state)
        return self.static_edges.get(name, END)

    # -- inspection --------------------------------------------------------

    def to_mermaid(self) -> str:
        lines = ["graph TD"]
        for src, dst in self.static_edges.items():
            lines.append(f"    {src} --> {dst}")
        for src, route in self.conditional.items():
            for target in getattr(route, "targets", ("?",)):
                lines.append(f"    {src} -.-> {target}")
        return "\n".join(lines)


def route(*targets: str) -> Callable[[RouteFn], RouteFn]:
    """Declare a routing function's possible targets, so the graph is analyzable.

    Without this the topology is opaque to static analysis — and, more to the
    point for Module 9, opaque to a meta-agent that wants to reason about it.
    """

    def decorator(fn: RouteFn) -> RouteFn:
        fn.targets = targets  # type: ignore[attr-defined]
        return fn

    return decorator


def chain_reliability(per_step: float, steps: int) -> float:
    """p**n — the stop rule. A 9-step chain at 92% succeeds 47% of the time."""
    return per_step ** steps
