"""Knowledge and memory graphs: typed edges, bi-temporal validity, confidence decay.

Module 9, Lessons 1-2. Three ideas are made executable here:

* **Typed edges.** An untyped edge carries one bit and duplicates what vector
  search already does. `EdgeType` is a closed vocabulary by construction — the
  graph refuses an edge type it was not told about, which is the constraint that
  stops an extractor inventing `relates_to`, `is_associated_with`, and
  `has_connection_with` for one relationship.

* **Bi-temporal validity.** Four timestamps, two clocks: when a fact was true in
  the world, and when the system believed it. Invalidate, never delete.

* **Confidence decay.** Per-hop accuracy `p` gives `p**n` over `n` hops. The
  traversal tracks it and refuses to return a path below a floor, because the
  alternative is presenting a 44%-trustworthy answer flatly.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable, Iterator

# A sentinel far-future timestamp meaning "still true" / "still believed".
FOREVER = 10**15


class OntologyError(ValueError):
    """Raised when an edge violates the declared schema.

    This is stage 7 of the nine-stage pipeline — the quality gate — and it is
    only possible because stage 3 declared an ontology first.
    """


@dataclass(frozen=True)
class EdgeType:
    """A declared relationship type. The closed vocabulary is the point."""

    name: str
    source_type: str
    target_type: str
    # Does this relationship change over time? Ownership does; "was born in" doesn't.
    time_varying: bool = False
    # Typical extraction accuracy for this edge type, used for confidence decay.
    accuracy: float = 0.95

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Node:
    id: str
    type: str
    name: str
    properties: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    """A typed, bi-temporally-scoped claim.

    t_valid / t_invalid  — when the fact was true IN THE WORLD
    t_created / t_expired — when the system BELIEVED it

    Keeping both clocks is what lets you answer "what did we believe in March?",
    which is what auditability means when a decision was made on wrong data.
    """

    source: str
    type: str
    target: str
    t_valid: int = 0
    t_invalid: int = FOREVER
    t_created: int = 0
    t_expired: int = FOREVER
    confidence: float = 1.0
    provenance: str = ""

    def true_at(self, when: int) -> bool:
        """Was this true in the world at `when`?"""
        return self.t_valid <= when < self.t_invalid

    def believed_at(self, when: int) -> bool:
        """Did the system believe this at `when`?"""
        return self.t_created <= when < self.t_expired

    def __str__(self) -> str:
        window = "" if self.t_invalid == FOREVER else f" [until {self.t_invalid}]"
        return f"{self.source} --{self.type}--> {self.target}{window}"


@dataclass
class Path:
    """A traversal result, carrying its own trustworthiness.

    The path IS the explanation — the strongest form of citation available
    anywhere in this course, because it shows the reasoning and not just a source.
    """

    edges: list[Edge] = field(default_factory=list)

    @property
    def nodes(self) -> list[str]:
        if not self.edges:
            return []
        return [self.edges[0].source] + [e.target for e in self.edges]

    @property
    def hops(self) -> int:
        return len(self.edges)

    @property
    def confidence(self) -> float:
        """p**n. This is the number that kills graph projects."""
        c = 1.0
        for e in self.edges:
            c *= e.confidence
        return c

    def explain(self) -> str:
        return " ".join(str(e) for e in self.edges) + f"  (confidence {self.confidence:.2f})"


class Graph:
    """A small typed, bi-temporal property graph."""

    def __init__(self, edge_types: Iterable[EdgeType] = ()) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.edge_types: dict[str, EdgeType] = {et.name: et for et in edge_types}

    # -- construction ------------------------------------------------------

    def declare(self, edge_type: EdgeType) -> None:
        self.edge_types[edge_type.name] = edge_type

    def add_node(self, node: Node) -> Node:
        self.nodes[node.id] = node
        return node

    def add_edge(
        self,
        source: str,
        type: str,
        target: str,
        *,
        t_valid: int = 0,
        t_created: int = 0,
        confidence: float | None = None,
        provenance: str = "",
    ) -> Edge:
        """Add an edge, enforcing the ontology. This is the quality gate."""
        et = self.edge_types.get(type)
        if et is None:
            known = ", ".join(sorted(self.edge_types)) or "(none declared)"
            raise OntologyError(
                f"Undeclared edge type {type!r}. Declared types: {known}. "
                f"Model the domain before extracting — an unconstrained extractor "
                f"invents synonyms and no query returns complete results."
            )
        for endpoint, expected, role in (
            (source, et.source_type, "source"),
            (target, et.target_type, "target"),
        ):
            node = self.nodes.get(endpoint)
            if node is None:
                raise OntologyError(f"Unknown node {endpoint!r} as {role} of {type!r}.")
            if node.type != expected:
                raise OntologyError(
                    f"{type!r} expects a {expected!r} as {role}, got {node.type!r} ({endpoint})."
                )

        edge = Edge(
            source=source,
            type=type,
            target=target,
            t_valid=t_valid,
            t_created=t_created,
            confidence=et.accuracy if confidence is None else confidence,
            provenance=provenance,
        )
        self.edges.append(edge)
        return edge

    # -- the hard part: invalidation ---------------------------------------

    def invalidate(self, edge: Edge, *, t_invalid: int, t_expired: int | None = None) -> Edge:
        """Close an edge's validity window. Never delete.

        `t_invalid` says when it stopped being true in the world.
        `t_expired` says when we stopped believing it — defaults to the same.

        Edges are immutable: mutation replaces them. Always continue with the
        edge a mutating call RETURNS — the reference you held before it is
        stale, and using it here raises rather than silently corrupting.
        """
        try:
            i = self.edges.index(edge)
        except ValueError:
            raise ValueError(
                f"Edge not found: {edge}. It was probably already invalidated, "
                f"superseded, or corrected — those calls replace the edge, so "
                f"continue with the edge they returned, not the one you held."
            ) from None
        closed = replace(
            edge,
            t_invalid=t_invalid,
            t_expired=edge.t_expired if t_expired is None else t_expired,
        )
        self.edges[i] = closed
        return closed

    def supersede(
        self, edge: Edge, *, new_target: str, at: int, learned_at: int | None = None
    ) -> Edge:
        """Replace a fact with a new one, preserving history.

        This is the mutation point, and per the control-plane research it is
        where the intelligence belongs — the hard part of memory is not writing
        facts, it is correctly invalidating them.

        Scope note: this convenience replaces the TARGET (the team now owns a
        different service). The other common shape — the SOURCE changes, as in
        a service transferring to a new owner — is the two-step form:
        `invalidate(old, t_invalid=at)` then `add_edge(new_owner, type, target,
        t_valid=at)`. Same semantics, no magic.
        """
        learned_at = at if learned_at is None else learned_at
        self.invalidate(edge, t_invalid=at, t_expired=learned_at)
        return self.add_edge(
            edge.source, edge.type, new_target, t_valid=at, t_created=learned_at
        )

    def correct(
        self,
        edge: Edge,
        *,
        discovered_at: int,
        actual_t_valid: int | None = None,
        actual_t_invalid: int | None = None,
    ) -> Edge:
        """We were wrong about WHEN something was true — its start, its end, or both.

        The world-clock changes; the belief-clock records that we only found out
        now. The original edge is expired, not deleted — "what did we believe in
        March?" must still be answerable.

        Both directions matter, and a correction usually needs both: learning
        that an ownership transfer happened earlier than recorded means the OLD
        owner's edge ended earlier (`actual_t_invalid`) AND the new owner's edge
        began earlier (`actual_t_valid`). An API that can only correct the start
        of a fact cannot execute half of the corrections that occur in practice.
        """
        if actual_t_valid is None and actual_t_invalid is None:
            raise ValueError(
                "correct() needs actual_t_valid, actual_t_invalid, or both — "
                "otherwise there is nothing to correct."
            )
        self.invalidate(edge, t_invalid=edge.t_invalid, t_expired=discovered_at)
        replacement = Edge(
            source=edge.source,
            type=edge.type,
            target=edge.target,
            t_valid=edge.t_valid if actual_t_valid is None else actual_t_valid,
            t_invalid=edge.t_invalid if actual_t_invalid is None else actual_t_invalid,
            t_created=discovered_at,
            confidence=edge.confidence,
            provenance=f"correction of {edge.provenance or 'earlier record'}",
        )
        self.edges.append(replacement)
        return replacement

    # -- querying ----------------------------------------------------------

    def out_edges(
        self, node_id: str, *, type: str | None = None, at: int | None = None,
        believed_at: int | None = None,
    ) -> list[Edge]:
        out = []
        for e in self.edges:
            if e.source != node_id:
                continue
            if type is not None and e.type != type:
                continue
            if at is not None and not e.true_at(at):
                continue
            if believed_at is not None and not e.believed_at(believed_at):
                continue
            out.append(e)
        return out

    def traverse(
        self,
        start: str,
        pattern: list[str],
        *,
        at: int | None = None,
        min_confidence: float = 0.0,
    ) -> list[Path]:
        """Follow a typed edge pattern, dropping paths below the confidence floor.

        `min_confidence` is the guard rail from Lesson 1: at 85% per hop a
        five-hop traversal is 44% trustworthy, and returning it flatly is worse
        than returning nothing.
        """
        results: list[Path] = []

        def walk(node_id: str, remaining: list[str], sofar: Path) -> None:
            if not remaining:
                if sofar.confidence >= min_confidence:
                    results.append(sofar)
                return
            for edge in self.out_edges(node_id, type=remaining[0], at=at):
                extended = Path(sofar.edges + [edge])
                # Prune early — confidence is monotonically decreasing.
                if extended.confidence < min_confidence:
                    continue
                walk(edge.target, remaining[1:], extended)

        walk(start, list(pattern), Path())
        return sorted(results, key=lambda p: -p.confidence)

    def transitive(
        self, start: str, edge_type: str, *, max_hops: int = 5,
        at: int | None = None, min_confidence: float = 0.0,
    ) -> list[Path]:
        """Follow one edge type repeatedly — 'what depends on this, transitively'.

        Returns one path per reachable node — the MOST TRUSTWORTHY path when
        several exist. On a diamond (A→B→D, A→C→D) a naive enumeration returns
        D twice, which surprises every caller who wanted "the set of things
        downstream." Redundant paths are also the good news the p**n arithmetic
        leaves out: a node reachable two independent ways is more certain than
        either path alone claims, so keeping the best path is a conservative
        summary of it.
        """
        best: dict[str, Path] = {}
        seen: set[str] = {start}

        def walk(node_id: str, depth: int, sofar: Path) -> None:
            if depth >= max_hops:
                return
            for edge in self.out_edges(node_id, type=edge_type, at=at):
                if edge.target in seen:
                    continue          # cycles are normal in dependency graphs
                extended = Path(sofar.edges + [edge])
                if extended.confidence < min_confidence:
                    continue
                prior = best.get(edge.target)
                if prior is None or extended.confidence > prior.confidence:
                    best[edge.target] = extended
                seen.add(edge.target)
                walk(edge.target, depth + 1, extended)
                seen.discard(edge.target)

        walk(start, 0, Path())
        return sorted(best.values(), key=lambda p: -p.confidence)

    def in_edges(
        self, node_id: str, *, type: str | None = None, at: int | None = None
    ) -> list[Edge]:
        return [
            e for e in self.edges
            if e.target == node_id
            and (type is None or e.type == type)
            and (at is None or e.true_at(at))
        ]

    def missing(
        self,
        node_type: str,
        edge_type: str,
        *,
        direction: str = "in",
        at: int | None = None,
    ) -> list[Node]:
        """Nodes of a type with NO edge of a type — the absence query.

        `direction` matters and is easy to get wrong. "Which services have no
        owner?" asks about *incoming* `owns` edges, because `owns` runs
        Team -> Service. Defaulting to "in" because that is the shape most real
        absence questions take: the thing you are auditing is the target.

        Similarity search can only find things that exist. This is a class of
        question only a structured store can answer at all.
        """
        if direction not in ("in", "out"):
            raise ValueError("direction must be 'in' or 'out'")
        look = self.in_edges if direction == "in" else self.out_edges
        return [
            n for n in self.nodes.values()
            if n.type == node_type and not look(n.id, type=edge_type, at=at)
        ]

    def __iter__(self) -> Iterator[Edge]:
        return iter(self.edges)


def hop_confidence(per_hop: float, hops: int) -> float:
    """p**n — the arithmetic that kills graph projects."""
    return per_hop ** hops


def required_per_hop(target_confidence: float, hops: int) -> float:
    """What per-hop accuracy do I need for this end-to-end confidence?"""
    return target_confidence ** (1 / hops)
