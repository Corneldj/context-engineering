"""Module 9 L6-L7 — the meta-harness loop, and the pathologies it must catch.

Run:  python3 examples/09_meta_harness.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce.metaharness import (
    DEFAULT_FROZEN, Archive, Candidate, FailureSignature, FrozenSurfaceError,
    HeldOutGate, MetaHarness, Scores, mine_weaknesses,
)

print("=" * 72)
print("1. Weakness mining: cluster by MECHANISM, not error code")
print("=" * 72)

# 40 failures. All report the same error. They are four different problems.
raw = (
    [{"err": "SchemaValidationError", "why": "total_in_image"}] * 14
    + [{"err": "SchemaValidationError", "why": "page_2_only"}] * 11
    + [{"err": "SchemaValidationError", "why": "synonym_balance_due"}] * 9
    + [{"err": "SchemaValidationError", "why": "genuinely_absent"}] * 6
)
MECHANISMS = {
    "total_in_image":       ("total rendered as an image, not text", "tool_implementations"),
    "page_2_only":          ("multi-page doc, only page 1 was read", "workflow"),
    "synonym_balance_due":  ("field label synonym not recognized", "system_prompt"),
    "genuinely_absent":     ("no total exists on the document", "NOT-A-HARNESS-BUG"),
}
sigs = mine_weaknesses(raw, classify=lambda f: FailureSignature(
    f["err"], f["why"], *(MECHANISMS[f["why"]][0],), surface=MECHANISMS[f["why"]][1]))

print(f"  40 failures, all reporting {raw[0]['err']}.")
print(f"  Grouped by error code:  1 problem.")
print(f"  Grouped by mechanism:   {len(sigs)} problems.\n")
for s in sigs:
    print("   ", s)
print("\n  The last one is not a harness bug. No prompt edit makes a missing")
print("  number appear — it needs a schema change to allow null, plus a review queue.")

print()
print("=" * 72)
print("2. The frozen set is a runtime property, not a policy document")
print("=" * 72)
mh = MetaHarness(
    editable=frozenset({"system_prompt", "workflow", "tool_implementations", "retry_policy"}),
    evaluate=lambda h: Scores(0.99, 0.99),      # would score brilliantly if reached
)
for surface, edit in [
    ("eval_data", "drop the 6 hardest cases"),
    ("permissions", "grant filesystem write"),
    ("budget", "remove the token ceiling"),
    ("model_weights", "fine-tune"),
]:
    try:
        mh.check_surface(Candidate(surface, edit))
        print(f"  {surface:<22} ALLOWED (!)")
    except FrozenSurfaceError as e:
        why = "frozen" if surface in DEFAULT_FROZEN else "not declared editable"
        print(f"  {surface:<22} REFUSED — {why}")
print("\n  Note the eval_data proposal never reaches evaluation, so it never gets")
print("  the chance to score 0.99. Refusal happens before scoring, by design.")

print()
print("=" * 72)
print("3. The held-out gate: four candidates, one accepted")
print("=" * 72)
gate = HeldOutGate()
baseline = Scores(0.70, 0.70, per_category={"invoices": 0.75, "contracts": 0.65})

candidates = [
    ("genuine improvement",
     Scores(0.78, 0.76, cost=1.0, per_category={"invoices": 0.82, "contracts": 0.71})),
    ("fits the held-in split",
     Scores(0.87, 0.705, cost=1.0, per_category={"invoices": 0.90, "contracts": 0.66})),
    ("REWARD HACK: return total=0 on failure",
     Scores(0.76, 0.75, cost=1.0, per_category={"invoices": 0.88, "contracts": 0.40})),
    ("noise",
     Scores(0.7009, 0.7003, cost=1.0, per_category={"invoices": 0.75, "contracts": 0.65})),
]
for label, scores in candidates:
    v = gate.judge(baseline, scores)
    mark = "ACCEPT" if v.accepted else "reject"
    print(f"  [{mark}] {label}")
    print(f"           {v.reason}")

print("\n  The reward hack is instructive. It raised BOTH held-in and held-out,")
print("  because returning 0 satisfies the schema on every unparseable document.")
print("  Only per-category tracking caught it: contracts collapsed 0.65 -> 0.40")
print("  while the mean improved. An aggregate score would have accepted it.")

print()
print("=" * 72)
print("4. Diversity collapse and the Pareto frontier")
print("=" * 72)
collapsed, diverse = Archive(), Archive()
for i in range(5):
    collapsed.record(Candidate("system_prompt", f"v{i}"),
                     gate.judge(baseline, Scores(0.75 + i / 200, 0.74 + i / 200)))
for surface in ("system_prompt", "workflow", "retry_policy", "tool_implementations"):
    diverse.record(Candidate(surface, "x"), gate.judge(baseline, Scores(0.77, 0.755)))
print(f"  collapsed search: diversity {collapsed.diversity():.2f}  <-- one surface, 5 edits")
print(f"  healthy search:   diversity {diverse.diversity():.2f}")
print("\n  A collapsing search plateaus smoothly and looks like convergence.")
print("  It is the search dying. Sample from the archive, not just the best.")

pareto = Archive()
for label, acc, cost in [("accurate+expensive", 0.80, 9.0),
                         ("nearly-as-good+cheap", 0.79, 1.2),
                         ("dominated", 0.76, 5.0)]:
    pareto.record(Candidate("workflow", label),
                  gate.judge(baseline, Scores(acc + 0.01, acc, cost=cost)))
print("\n  Pareto frontier (accuracy vs cost):")
for cand, sc in pareto.pareto():
    print(f"    {cand.edit:<24} held_out={sc.held_out:.2f}  cost={sc.cost:.1f}")
print("    'dominated' is excluded — worse on both axes.")
print("\n  Optimizing accuracy alone would have picked the 9.0-cost option and")
print("  never surfaced that 1.2-cost gets you within a point of it.")

print()
print("=" * 72)
print("5. The loop, end to end")
print("=" * 72)


def evaluate(harness):
    """A toy evaluator with a ceiling — improvements run out."""
    gains = {"system_prompt": 0.05, "workflow": 0.04, "retry_policy": 0.02}
    total = sum(gains.get(k, 0) for k in harness)
    return Scores(
        held_in=0.70 + total,
        held_out=0.70 + total * 0.9,
        cost=1.0 + 0.3 * len(harness),
        per_category={"invoices": 0.75 + total, "contracts": 0.65 + total},
    )


def propose(harness, archive):
    tried = {c.surface for c, _ in archive.entries}
    for surface in ("eval_data", "system_prompt", "workflow", "retry_policy", "logging"):
        if surface not in tried:
            yield Candidate(surface, f"edit-{surface}", rationale="from weakness mining")


mh = MetaHarness(
    editable=frozenset({"system_prompt", "workflow", "retry_policy"}),
    evaluate=evaluate,
)
final, scores = mh.run({}, propose, rounds=10, plateau_after=2)
print(f"  final harness surfaces: {sorted(final)}")
print(f"  held-out: 0.700 -> {scores.held_out:.3f}")
print(f"  archive:  {len(mh.archive.accepted)} accepted, {len(mh.archive.rejected)} rejected")
print(f"  diversity: {mh.archive.diversity():.2f}")
print("\n  eval_data and logging were proposed and refused without ever being scored.")
print("\n  And the honest caveat: this held-out split has now gated several accept")
print("  decisions, so it has been indirectly optimized against. Rotate it, and")
print("  report against a genuinely fresh set before believing the number.")
