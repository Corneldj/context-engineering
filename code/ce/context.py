"""Cache-aware, budgeted context assembly.

This is the Context plane of Module 8, Lesson 4, made executable.

Two rules are enforced structurally rather than by convention:

1.  **Stable before volatile.** A prompt cache prefix is valid only up to the
    first byte that changed, so a volatile section placed above a stable one
    destroys the cache for everything below it. `assemble()` refuses to do this.

2.  **The budget is real.** When over budget, sections are dropped by *value*,
    not by age — the naive implementation truncates oldest-first, which is
    usually the user's original goal.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterable

from . import tokens


class Stability(IntEnum):
    """How often a section's content changes. Lower = more stable = higher up.

    The ordering is the whole point: it makes the cache-safety rule a type-level
    property rather than a comment someone has to remember.
    """

    STATIC = 0      # system prompt, tool schemas, few-shot examples
    DURABLE = 1     # long-lived memory, project conventions
    SUMMARY = 2     # compacted history — changes only on compaction
    RETRIEVED = 3   # documents fetched for this request
    RECENT = 4      # recent turns and tool results
    VOLATILE = 5    # task state, the current instruction


@dataclass
class Section:
    name: str
    content: str
    stability: Stability
    # Higher survives longer when the budget is tight. Independent of stability:
    # the user's goal is volatile but must never be dropped.
    value: int = 50
    droppable: bool = True

    @property
    def tokens(self) -> int:
        return tokens.count(self.content)


@dataclass
class Budget:
    """A token budget, enforced in code. A budget you do not enforce is a comment."""

    total: int = 40_000
    response_headroom: int = 4_000

    @property
    def available(self) -> int:
        return max(0, self.total - self.response_headroom)


class CacheOrderError(ValueError):
    """Raised when the stable prefix changed between calls, killing the cache.

    This is the failure that actually happens in production: someone puts a
    timestamp, a request id, or a session counter in a section they declared
    STATIC. Sorting cannot catch that — the declaration is wrong, not the order.
    What catches it is noticing that the prefix you are billing as "cached"
    is not byte-identical to last turn's.
    """


@dataclass
class AssembledContext:
    text: str
    sections: list[Section]
    dropped: list[Section] = field(default_factory=list)
    truncated: list[str] = field(default_factory=list)
    cache_breakpoint_after: str | None = None
    # False when the stable prefix differs from the previous assembly on the
    # same assembler — i.e. your cache prefix just died and you will pay full
    # price for a context you believe is cached.
    cache_prefix_stable: bool = True

    @property
    def tokens(self) -> int:
        return tokens.count(self.text)

    @property
    def stable_tokens(self) -> int:
        return sum(s.tokens for s in self.sections if s.stability <= Stability.DURABLE)

    def breakdown(self) -> dict[str, int]:
        """Per-section token counts.

        Module 6, Lesson 2: log this on every call. Most teams discover a tool
        returning 8,000 tokens of JSON within a week of starting to look.
        """
        return {s.name: s.tokens for s in self.sections}


class ContextAssembler:
    """Assembles a context window from sections, under a budget, cache-safely."""

    def __init__(self, budget: Budget | None = None, *, strict_cache: bool = False) -> None:
        self.budget = budget or Budget()
        self.strict_cache = strict_cache
        self._prefix_hash: str | None = None
        self.cache_prefix_breaks = 0

    def assemble(self, sections: Iterable[Section]) -> AssembledContext:
        # Within stable tiers, importance sorts EARLY (primacy attention).
        # Within the volatile tier, importance sorts LATE — the most important
        # volatile content is the immediate task, and it belongs at the very
        # end of the window (recency attention). One sort key would put the
        # task above the timestamp, which is backwards.
        ordered = sorted(
            sections,
            key=lambda s: (
                s.stability,
                s.value if s.stability >= Stability.VOLATILE else -s.value,
            ),
        )
        kept, dropped = self._fit_to_budget(ordered)
        text = "\n\n".join(self._render(s) for s in kept)
        stable = self._audit_prefix(kept)
        return AssembledContext(
            text=text,
            sections=kept,
            dropped=dropped,
            cache_breakpoint_after=self._breakpoint(kept),
            cache_prefix_stable=stable,
        )

    def _audit_prefix(self, kept: list[Section]) -> bool:
        """Compare this turn's stable prefix to the last one, byte for byte."""
        prefix = "".join(
            self._render(s) for s in kept if s.stability <= Stability.DURABLE
        )
        digest = hashlib.sha256(prefix.encode()).hexdigest()
        if self._prefix_hash is None:
            self._prefix_hash = digest
            return True
        if digest == self._prefix_hash:
            return True

        self.cache_prefix_breaks += 1
        self._prefix_hash = digest
        if self.strict_cache:
            raise CacheOrderError(
                "The stable prefix changed between turns, so the prompt cache "
                "prefix is invalid and every token above the breakpoint will bill "
                "at full rate. Something declared STATIC or DURABLE contains a "
                "value that varies per call — a timestamp, a request id, a counter."
            )
        return False

    # -- internals ---------------------------------------------------------

    def _fit_to_budget(self, ordered: list[Section]) -> tuple[list[Section], list[Section]]:
        limit = self.budget.available
        total = sum(s.tokens for s in ordered)
        if total <= limit:
            return ordered, []

        # Drop by ascending value — the least valuable content goes first,
        # regardless of how recent it is.
        dropped: list[Section] = []
        candidates = sorted(
            (s for s in ordered if s.droppable), key=lambda s: (s.value, -s.tokens)
        )
        keep = {id(s) for s in ordered}
        for section in candidates:
            if total <= limit:
                break
            keep.discard(id(section))
            dropped.append(section)
            total -= section.tokens

        kept = [s for s in ordered if id(s) in keep]
        if total > limit:
            kept = self._truncate_largest(kept, total - limit)
        return kept, dropped

    @staticmethod
    def _truncate_largest(kept: list[Section], overflow: int) -> list[Section]:
        """Last resort: shrink the largest non-droppable section, visibly."""
        if not kept:
            return kept
        target = max(kept, key=lambda s: s.tokens)
        keep_chars = max(0, (target.tokens - overflow)) * 4
        target.content = (
            target.content[:keep_chars]
            + f"\n...[TRUNCATED to fit the context budget: {target.name}]..."
        )
        return kept

    @staticmethod
    def _breakpoint(kept: list[Section]) -> str | None:
        """The last stable section — where a cache breakpoint belongs."""
        stable = [s for s in kept if s.stability <= Stability.DURABLE]
        return stable[-1].name if stable else None

    @staticmethod
    def _render(section: Section) -> str:
        tag = section.name.lower().replace(" ", "_")
        return f"<{tag}>\n{section.content}\n</{tag}>"


def edge_load(items: list[str]) -> list[str]:
    """Reorder ranked items so the strongest sit at the block's edges.

    Module 4, Lesson 1: recall is best at the beginning and end of a span and
    worst in the middle. Given [1,2,3,4,5] best-first this returns
    [1, 3, 5, 4, 2] — best first, second-best last, weakest buried.
    """
    head: list[str] = []
    tail: list[str] = []
    for i, item in enumerate(items):
        (head if i % 2 == 0 else tail).append(item)
    return head + tail[::-1]
