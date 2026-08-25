"""Continuous vector memory graphs: one store, three query modes.

Module 9, Lesson 3. A memory graph (typed edges, bi-temporal validity — see
`ce.graph`) whose nodes and facts also carry embeddings, maintained
**continuously**: embedded at write time, refreshed at mutation time, never
batch-rebuilt. That gives one store answering three kinds of question:

* fuzzy   — "that thing the customer said about billing"   (vector entry)
* exact   — "what does invoice 7712 relate to"             (graph traversal)
* temporal— "what was true in March"                        (validity filter)

Retrieval is the ENTRY -> EXPAND -> FILTER -> RANK pipeline: embed the query,
find entry nodes by similarity, expand along typed edges, filter by validity at
the asked-about time, rank by a fusion of similarity, entry strength, hop
distance, and edge confidence.

Two subtleties this implementation gets right, because naive designs get them
wrong (Lesson 3 §4):

1. **An embedding outlives the truth of the fact it encodes.** A superseded
   fact still matches queries semantically, forever. Deleting its vector breaks
   "as of March" queries; keeping it unfiltered pollutes "now" queries. The
   answer is keep + filter by validity at query time.
2. **Node embeddings rot when their neighbourhood changes.** A node summary
   embedded once drifts from reality as facts are superseded. Refresh at the
   mutation point — the same place the control-plane research puts the
   intelligence for invalidation.

The default embedder is a deterministic, dependency-free bag-of-tokens hash:
cosine similarity approximates token overlap. That makes every test and example
runnable offline — and it is honestly LEXICAL, not semantic. A real embedding
model finds "subscription" ~ "plan"; this one does not. Swap it in via the
`embed` parameter, and version-pin it: changing embedders invalidates every
stored vector at once (Lesson 5 §3).
"""

from __future__ import annotations

import math
import re
import zlib
from dataclasses import dataclass, field
from typing import Callable, Iterable

from .graph import FOREVER, Edge, Graph, Node

Vector = tuple[float, ...]

_TOKEN = re.compile(r"[a-z0-9]+")


def hash_embed(text: str, dims: int = 256) -> Vector:
    """Deterministic bag-of-tokens embedding. Lexical, offline, documented as such.

    Uses crc32, not Python's built-in `hash()` — string hashing is salted per
    process, so `hash()` would make "deterministic" quietly false across runs.
    """
    counts = [0.0] * dims
    for token in _TOKEN.findall(text.lower()):
        counts[zlib.crc32(token.encode()) % dims] += 1.0
    norm = math.sqrt(sum(c * c for c in counts))
    if norm == 0:
        return tuple(counts)
    return tuple(c / norm for c in counts)


def cosine(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


@dataclass(frozen=True)
class RecallResult:
    fact: Edge
    text: str
    score: float
    entry: str          # the node the vector search entered through
    hops: int           # graph distance from the entry node

    def explain(self) -> str:
        return (
            f"{self.text}  [via {self.entry}, hop {self.hops}, "
            f"score {self.score:.2f}, {self.fact}]"
        )


class VectorMemoryGraph:
    """A `Graph` plus continuously-maintained embeddings.

    All writes go through this class rather than the wrapped graph, because
    mutation is where the vector bookkeeping happens: embed-on-write for new
    facts, re-keying for closed edges, and neighbourhood refresh for touched
    nodes. Reads delegate to the graph for structure and to the vectors for
    entry.
    """

    def __init__(self, graph: Graph, *, embed: Callable[[str], Vector] = hash_embed) -> None:
        self.graph = graph
        self._embed_fn = embed
        self.embed_calls = 0                    # the cost meter for "continuous"
        self._node_vecs: dict[str, Vector] = {}
        self._fact_vecs: dict[Edge, Vector] = {}
        self._fact_text: dict[Edge, str] = {}

    # -- internals ---------------------------------------------------------

    def _embed(self, text: str) -> Vector:
        self.embed_calls += 1
        return self._embed_fn(text)

    def _node_summary(self, node_id: str) -> str:
        """A node's text is its name, type, properties, and CURRENT facts.

        Built from currently-valid facts only — a node's searchable identity
        should reflect what is true, while superseded facts stay reachable
        through as-of recall, not through today's entry points.
        """
        node = self.graph.nodes[node_id]
        parts = [node.name, node.type, *map(str, node.properties.values())]
        now = FOREVER - 1
        for e in self.graph.out_edges(node_id, at=now) + self.graph.in_edges(node_id, at=now):
            parts.append(self._fact_text.get(e, f"{e.source} {e.type} {e.target}"))
        return " ".join(parts)

    def _refresh_node(self, node_id: str) -> None:
        """Re-embed one node's summary. Called at every mutation touching it.

        This is O(neighbourhood) per write — the property that makes the graph
        *continuous* rather than batch-rebuilt.
        """
        self._node_vecs[node_id] = self._embed(self._node_summary(node_id))

    def _rekey(self, old: Edge, new: Edge) -> None:
        """Mutations replace frozen edges; the vector follows the fact."""
        if old in self._fact_vecs:
            self._fact_vecs[new] = self._fact_vecs.pop(old)
            self._fact_text[new] = self._fact_text.pop(old)

    def _render(self, source: str, type: str, target: str) -> str:
        s = self.graph.nodes[source].name
        t = self.graph.nodes[target].name
        return f"{s} {type.replace('_', ' ')} {t}"

    # -- writes (embed-on-write) -------------------------------------------

    def add_node(self, node: Node) -> Node:
        self.graph.add_node(node)
        self._refresh_node(node.id)
        return node

    def add_fact(
        self,
        source: str,
        type: str,
        target: str,
        *,
        text: str | None = None,
        t_valid: int = 0,
        t_created: int = 0,
        confidence: float | None = None,
        provenance: str = "",
    ) -> Edge:
        """Add a fact and embed it, plus refresh both endpoint nodes.

        Cost per write: 3 embed calls (1 fact + 2 nodes) — independent of how
        large the graph already is. Compare a nightly batch rebuild, which is
        O(corpus) every night whether anything changed or not.
        """
        edge = self.graph.add_edge(
            source, type, target,
            t_valid=t_valid, t_created=t_created,
            confidence=confidence, provenance=provenance,
        )
        rendered = text or self._render(source, type, target)
        self._fact_text[edge] = rendered
        self._fact_vecs[edge] = self._embed(rendered)
        self._refresh_node(source)
        self._refresh_node(target)
        return edge

    def supersede(self, edge: Edge, *, new_target: str, at: int,
                  text: str | None = None, learned_at: int | None = None) -> Edge:
        """Replace a fact, preserving history AND its vector.

        The closed fact keeps its embedding — it must remain findable by as-of
        recall. The replacement gets its own. Both endpoints refresh, so entry
        points reflect the new truth immediately.
        """
        old_source, old_target = edge.source, edge.target
        learned_at = at if learned_at is None else learned_at
        closed = self.graph.invalidate(edge, t_invalid=at, t_expired=learned_at)
        self._rekey(edge, closed)
        replacement = self.add_fact(
            old_source, closed.type, new_target,
            text=text, t_valid=at, t_created=learned_at,
        )
        self._refresh_node(old_target)      # the endpoint the fact LEFT rots too
        return replacement

    def invalidate(self, edge: Edge, *, t_invalid: int, t_expired: int | None = None) -> Edge:
        closed = self.graph.invalidate(edge, t_invalid=t_invalid, t_expired=t_expired)
        self._rekey(edge, closed)
        self._refresh_node(closed.source)
        self._refresh_node(closed.target)
        return closed

    # -- reads (entry -> expand -> filter -> rank) --------------------------

    def entry_points(self, query: str, *, k: int = 3) -> list[tuple[str, float]]:
        """Vector search over node summaries: the fuzzy way into the graph."""
        qv = self._embed_fn(query)          # not counted: queries aren't writes
        scored = [
            (node_id, cosine(qv, vec))
            for node_id, vec in self._node_vecs.items()
        ]
        scored = [(n, s) for n, s in scored if s > 0]
        return sorted(scored, key=lambda ns: (-ns[1], ns[0]))[:k]

    def recall(
        self,
        query: str,
        *,
        at: int | None = None,
        hops: int = 2,
        k_entry: int = 3,
        top: int = 5,
    ) -> list[RecallResult]:
        """ENTRY -> EXPAND -> FILTER -> RANK.

        `at=None` means "currently valid". Passing a timestamp answers the
        as-of question — including for facts whose vectors a naive design
        would have deleted.
        """
        when = (FOREVER - 1) if at is None else at
        qv = self._embed_fn(query)

        # ENTRY: fuzzy similarity finds where to start.
        entries = self.entry_points(query, k=k_entry)

        # EXPAND: breadth-first over ALL edge types, both directions,
        # recording the hop at which each fact was first reached.
        found: dict[Edge, tuple[str, float, int]] = {}
        for entry_id, entry_score in entries:
            frontier = {entry_id}
            for hop in range(1, hops + 1):
                next_frontier: set[str] = set()
                for node_id in frontier:
                    # FILTER: only edges true at the asked-about time.
                    incident = (
                        self.graph.out_edges(node_id, at=when)
                        + self.graph.in_edges(node_id, at=when)
                    )
                    for e in incident:
                        if e not in found:
                            found[e] = (entry_id, entry_score, hop)
                        next_frontier.add(e.target if e.source == node_id else e.source)
                frontier = next_frontier

        # RANK: fuse similarity, entry strength, hop distance, and confidence.
        results = []
        for e, (entry_id, entry_score, hop) in found.items():
            sim = cosine(qv, self._fact_vecs.get(e, ()))
            score = e.confidence * (0.6 * sim + 0.3 * entry_score + 0.1 / hop)
            results.append(RecallResult(
                fact=e,
                text=self._fact_text.get(e, str(e)),
                score=score,
                entry=entry_id,
                hops=hop,
            ))
        return sorted(results, key=lambda r: (-r.score, r.text))[:top]

    def semantic_only(self, query: str, *, at: int | None = None, top: int = 5) -> list[RecallResult]:
        """Pure vector search over facts — the comparison baseline.

        Still validity-filtered: even a plain vector memory must not surface a
        superseded fact for a "now" query. What it LACKS is expansion — a fact
        sharing no vocabulary with the query is unreachable, however closely
        it is connected to one that matches.
        """
        when = (FOREVER - 1) if at is None else at
        qv = self._embed_fn(query)
        results = [
            RecallResult(fact=e, text=self._fact_text[e],
                         score=e.confidence * cosine(qv, v), entry="(none)", hops=0)
            for e, v in self._fact_vecs.items()
            if e.true_at(when)
        ]
        results = [r for r in results if r.score > 0]
        return sorted(results, key=lambda r: (-r.score, r.text))[:top]

    # -- bookkeeping --------------------------------------------------------

    def stats(self) -> dict[str, int]:
        return {
            "nodes": len(self._node_vecs),
            "facts": len(self._fact_vecs),
            "embed_calls": self.embed_calls,
        }
