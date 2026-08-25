"""Module 9 L4 — durable execution, human gates, and the stop rule.

Run:  python3 examples/08_execution_graph.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce.execgraph import (
    END, Checkpointer, IdempotencyLedger, Interrupted, StateGraph,
    chain_reliability, route,
)

audit = {"tests": 0, "merged": 0, "notified": 0}


def build(fail_times=0):
    audit.update(tests=0, merged=0, notified=0)

    def analyze(s):   return {"findings": ["tax rounding"]}
    def run_tests(s):
        audit["tests"] += 1
        return {"passed": audit["tests"] > fail_times, "attempts": s.get("attempts", 0) + 1}
    def fix(s):       return {"findings": s["findings"] + ["patched"]}
    def merge(s):
        audit["merged"] += 1
        return {"merged": True}
    def notify(s):
        audit["notified"] += 1
        return {"notified": True}

    @route("merge", "fix", "escalate")
    def after_tests(s):
        if s.get("passed"):
            return "merge"
        return "fix" if s.get("attempts", 0) < 3 else "escalate"

    g = StateGraph("analyze")
    g.add_node("analyze", analyze)
    g.add_node("run_tests", run_tests)
    g.add_node("fix", fix)
    g.add_node("merge", merge, idempotency_key=lambda s: "pr-991",
               interrupt_before=True, on_skip=lambda s: {"merged": True})
    g.add_node("notify", notify)
    g.add_node("escalate", lambda s: {"escalated": True})
    g.add_edge("analyze", "run_tests")
    g.add_conditional_edges("run_tests", after_tests)
    g.add_edge("fix", "run_tests")
    g.add_edge("merge", "notify")
    g.add_edge("notify", END)
    g.add_edge("escalate", END)
    return g


print("=" * 72)
print("1. Routing is a pure function of state — testable in isolation")
print("=" * 72)
g = build()
print(g.to_mermaid())
print("\nvalidate():", g.validate() or "no problems")

print()
print("=" * 72)
print("2. The cycle terminates via the routing function, not a magic number")
print("=" * 72)
for fails in (0, 2, 99):
    g = build(fail_times=fails)
    out = g.run({"diff": "..."}, approvals={"merge": True})
    ending = "merged" if out.get("merged") else "ESCALATED"
    print(f"  tests fail {fails:>2}x -> {audit['tests']} test runs, {ending}")

print()
print("=" * 72)
print("3. A human gate that genuinely suspends the run")
print("=" * 72)
cp, ledger = Checkpointer(), IdempotencyLedger()
g = build()
try:
    g.run({"diff": "..."}, run_id="pr991", checkpointer=cp, ledger=ledger)
except Interrupted as e:
    print(f"  suspended at {e.node!r}; merges so far: {audit['merged']}")
    print("  the process can now exit. state is on disk.")

print("\n  ... three days later, the reviewer approves ...\n")
out = g.run({}, run_id="pr991", checkpointer=cp, ledger=ledger,
            resume=True, approvals={"merge": True})
print(f"  resumed and completed: merged={out['merged']}, notified={out['notified']}")
print("\n  Under the Module 8 loop this is either a blocked process for three days,")
print("  or you build your own state persistence — which is most of a graph runtime.")

print()
print("=" * 72)
print("4. Idempotence: the dangerous window is BEFORE the checkpoint writes")
print("=" * 72)


class DyingCheckpointer(Checkpointer):
    def __init__(self, inner, die_after):
        super().__init__()
        self.inner, self.die_after, self.armed = inner, die_after, True

    def save(self, run_id, state, next_node, completed):
        if self.armed and self.die_after in " ".join(completed):
            self.armed = False
            raise SystemExit("process killed")
        self.inner.save(run_id, state, next_node, completed)

    def load(self, run_id):
        return self.inner.load(run_id)


for use_ledger in (False, True):
    cp2 = Checkpointer()
    led = IdempotencyLedger() if use_ledger else None
    g = build()
    dying = DyingCheckpointer(cp2, die_after="merge")
    try:
        g.run({"diff": "..."}, run_id="x", checkpointer=dying, ledger=led,
              approvals={"merge": True})
    except SystemExit:
        pass
    merged_before = audit["merged"]
    try:
        g.run({}, run_id="x", checkpointer=cp2, ledger=led, resume=True,
              approvals={"merge": True})
    except SystemExit:
        pass
    label = "with ledger   " if use_ledger else "without ledger"
    print(f"  {label}: merged {audit['merged']} time(s)"
          f"{'  <-- DUPLICATE SIDE EFFECT' if audit['merged'] > 1 else ''}")

print("\n  The fence cannot live in the checkpoint, because the failure window is")
print("  exactly when the checkpoint did not write. It needs its own durable store.")

print()
print("=" * 72)
print("5. The stop rule: topology, not agent quality")
print("=" * 72)
print("   steps │  90%     92%     95%     98%   per-step reliability")
print("   ──────┼────────────────────────────────")
for n in (3, 5, 7, 9):
    row = "  ".join(f"{chain_reliability(p, n):>5.0%}" for p in (0.90, 0.92, 0.95, 0.98))
    print(f"     {n}   │  {row}")
print(f"\n  A 9-step chain at 92% completes {chain_reliability(0.92,9):.0%} of the time.")
print(f"  Restructured to 3 steps at the SAME 92%: {chain_reliability(0.92,3):.0%}.")
print(f"  Improving every step to 95% instead, still 9 steps: {chain_reliability(0.95,9):.0%}.")
print("\n  Shortening the chain beat a 3-point per-step improvement. Topology is")
print("  powerful, not magic — 9 steps at 98% still beats 3 steps at 92%.")
