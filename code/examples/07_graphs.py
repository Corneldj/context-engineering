"""Module 9 L1-L2 — typed edges, bi-temporal memory, and the arithmetic.

Run:  python3 examples/07_graphs.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce.graph import (
    EdgeType, Graph, Node, OntologyError, hop_confidence, required_per_hop,
)

JAN, FEB, MAR, JUN = 100, 200, 300, 600

g = Graph([
    EdgeType("owns",       "Team",     "Service", time_varying=True, accuracy=0.95),
    EdgeType("depends_on", "Service",  "Service", accuracy=0.90),
    EdgeType("caused_by",  "Incident", "Deploy",  accuracy=0.85),
    EdgeType("touched",    "Deploy",   "Service", accuracy=0.98),
])
for nid, ntype, name in [
    ("platform", "Team", "Platform"), ("payments", "Team", "Payments"),
    ("auth-lib", "Service", "auth-lib"), ("payments-api", "Service", "payments-api"),
    ("web", "Service", "web"), ("legacy-cron", "Service", "legacy-cron"),
    ("INC-7", "Incident", "INC-7"), ("deploy-412", "Deploy", "deploy-412"),
]:
    g.add_node(Node(nid, ntype, name))

print("=" * 72)
print("1. The ontology is a gate, not documentation")
print("=" * 72)
try:
    g.add_edge("platform", "is_associated_with", "auth-lib")
except OntologyError as e:
    print("REFUSED:", str(e)[:110], "...")
try:
    g.add_edge("auth-lib", "owns", "web")            # a Service cannot own
except OntologyError as e:
    print("REFUSED:", e)
print("\nAn unconstrained extractor invents synonyms and no query is ever complete.")

print()
print("=" * 72)
print("2. Bi-temporal: invalidate, never delete")
print("=" * 72)
owned = g.add_edge("platform", "owns", "payments-api", t_valid=JAN, t_created=JAN)
print("  Jan: Platform owns payments-api")
g.supersede(owned, new_target="web", at=MAR)
print("  Mar: ownership transfers to web\n")

for label, when in [("in February", FEB), ("today", JUN)]:
    edges = g.out_edges("platform", type="owns", at=when)
    print(f"  What did Platform own {label}?  {[e.target for e in edges]}")
print("\n  Both answers are available. A summary would have kept only the second.")

print()
print("=" * 72)
print("3. Correcting the record without destroying history")
print("=" * 72)
wrong = g.add_edge("payments", "owns", "auth-lib", t_valid=MAR, t_created=MAR)
print("  Recorded in March: Payments owns auth-lib since March.")
g.correct(wrong, actual_t_valid=FEB, discovered_at=JUN)
print("  In June we learn it actually transferred in February.\n")
print("  Truth now says it was owned since Feb:",
      any(e.true_at(FEB + 10) for e in g.out_edges("payments", type="owns")))
print("  But what we BELIEVED in April was still 'since March':",
      [e.t_valid for e in g.out_edges("payments", type="owns", believed_at=400)])
print("\n  That second query is what auditability means: reconstructing what the")
print("  system knew when a decision was made, not what it knows now.")

print()
print("=" * 72)
print("4. Queries vector search structurally cannot answer")
print("=" * 72)
g.add_edge("platform", "owns", "auth-lib", t_valid=0, t_created=0)
g.add_edge("web", "depends_on", "payments-api")
g.add_edge("payments-api", "depends_on", "auth-lib")

print("  ABSENCE — which services have no owner?")
print("   ", [n.name for n in g.missing("Service", "owns", direction="in")])
print("\n  TRANSITIVE — what does 'web' depend on, at any depth?")
for p in g.transitive("web", "depends_on"):
    print("    ", p.explain())

print()
print("=" * 72)
print("5. The arithmetic that kills graph projects")
print("=" * 72)
print("   per-hop │  2 hops   3 hops   5 hops")
print("   ────────┼──────────────────────────")
for p in (0.95, 0.90, 0.85, 0.80):
    row = "  ".join(f"{hop_confidence(p, n):>6.0%}" for n in (2, 3, 5))
    flag = "   <-- 'respectable' extraction" if p == 0.85 else ""
    print(f"     {p:.0%}   │  {row}{flag}")

print("\n  Compliance needs 95% over a 3-hop traversal. Required per-hop:")
print(f"    {required_per_hop(0.95, 3):.1%}  <-- not achievable by LLM extraction from contracts")
print("\n  So you do not fix the extractor. You shorten the traversal, or you")
print("  restrict which questions users may ask.")

print()
print("=" * 72)
print("6. Withholding beats presenting a 44%-confident answer flatly")
print("=" * 72)
g.add_edge("INC-7", "caused_by", "deploy-412")
g.add_edge("deploy-412", "touched", "payments-api")
for floor in (0.0, 0.9):
    paths = g.traverse("INC-7", ["caused_by", "touched"], min_confidence=floor)
    got = paths[0].explain() if paths else "(withheld — below the confidence floor)"
    print(f"  floor={floor:.0%}: {got}")
