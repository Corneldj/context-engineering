"""Module 9 L3 — a continuous vector memory graph: one store, three query modes.

Run:  python3 examples/10_vector_memory_graph.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce.graph import EdgeType, Graph, Node
from ce.vectorgraph import VectorMemoryGraph

JAN, MAR = 100, 300

g = Graph([
    EdgeType("subscribes_to", "Customer", "Plan", time_varying=True, accuracy=0.95),
    EdgeType("billed_to", "Invoice", "Customer", accuracy=0.98),
    EdgeType("mentions", "Ticket", "Plan", accuracy=0.90),
])
vmg = VectorMemoryGraph(g)
for nid, ntype, name in [
    ("kim", "Customer", "Kim Nakamura"), ("starter", "Plan", "Starter"),
    ("growth", "Plan", "Growth"), ("inv7712", "Invoice", "Invoice 7712"),
]:
    vmg.add_node(Node(nid, ntype, name))

starter = vmg.add_fact("kim", "subscribes_to", "starter",
                       text="Kim Nakamura signed up for Starter",
                       t_valid=JAN, t_created=JAN)
vmg.add_fact("inv7712", "billed_to", "kim",
             text="Invoice 7712 billed to Kim Nakamura", t_valid=JAN, t_created=JAN)

print("=" * 72)
print("1. The entry problem, and the pipeline that solves it")
print("=" * 72)
query = "which tier is invoice 7712 under"
print(f'  query: "{query}"')
print("\n  Pure vector over facts (the answer shares NO tokens with the query):")
for r in vmg.semantic_only(query):
    print("    ", r.text, f"(score {r.score:.2f})")
print("\n  ENTRY -> EXPAND -> FILTER -> RANK:")
for r in vmg.recall(query, hops=2):
    print("    ", r.explain())
print("\n  The subscription fact is unreachable by similarity — zero shared")
print("  vocabulary — and two hops away through the graph. Entry via the")
print("  invoice node, expand through Kim, and it surfaces, with the path")
print("  as provenance.")

print()
print("=" * 72)
print("2. Vectors outlive truth: supersede, then ask 'now' and 'as of'")
print("=" * 72)
vmg.supersede(starter, new_target="growth", at=MAR,
              text="Kim Nakamura signed up for Growth")
print("  March: Kim moves from Starter to Growth.\n")
for label, at in [("now", None), ("as of February", 200)]:
    hits = [r.text for r in vmg.recall("Kim Nakamura signed up", at=at)]
    print(f"  recall({label}): {hits}")
print("\n  The superseded fact's embedding was KEPT and filtered by validity.")
print("  Delete it (the naive fix) and 'as of February' silently breaks.")

print()
print("=" * 72)
print("3. Node embeddings refresh at the mutation point")
print("=" * 72)
entries = dict(vmg.entry_points("Growth", k=4))
print(f"  entry_points('Growth') now includes kim: {entries.get('kim', 0):.2f}")
print("  Kim's summary re-embedded when the subscription changed — a stale")
print("  summary would still route Growth queries through the old plan.")

print()
print("=" * 72)
print("4. 'Continuous' is a cost claim: embed-on-write vs batch rebuild")
print("=" * 72)
for i in range(30):
    vmg.add_node(Node(f"t{i}", "Ticket", f"Ticket {i}"))
    vmg.add_fact(f"t{i}", "mentions", "growth", text=f"ticket {i} asks about the growth tier")
before = vmg.embed_calls
vmg.add_node(Node("t_new", "Ticket", "Ticket 31"))
vmg.add_fact("t_new", "mentions", "starter", text="ticket 31 asks about starter pricing")
delta = vmg.embed_calls - before
s = vmg.stats()
print(f"  graph: {s['nodes']} nodes, {s['facts']} facts")
print(f"  cost of adding ONE fact: {delta} embed calls (fact + touched nodes)")
print(f"  cost of a nightly batch rebuild: {s['nodes'] + s['facts']} embed calls, every night")
print("\n  At 50,000 facts and 400 writes/day, embed-on-write is ~1,600 calls/day.")
print("  A nightly rebuild is 50,000+ — 30x the cost, plus a staleness window")
print("  the width of a day. That gap is what 'continuous' means operationally.")
