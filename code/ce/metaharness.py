"""The meta-harness loop: propose, evaluate, accept — with a held-out gate.

Module 9, Lessons 6-7. Implemented so the *failure* modes are demonstrable, not
just the success path. In particular:

* `HeldOutGate` refuses candidates that improve held-in and not held-out. This
  is the single mechanism separating real improvement from fitting your own
  evaluator, and `examples/09_meta_harness.py` shows a reward-hacking candidate
  being caught by it.

* `FrozenSurfaceError` makes the frozen set a runtime property rather than a
  policy document. A proposer that tries to edit the eval set gets an exception.

* `Archive` keeps rejected candidates and samples for diversity, because an
  evolutionary loop that only samples from the current best converges on one
  design and stops exploring.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence


class FrozenSurfaceError(PermissionError):
    """Raised when a proposal targets a surface the optimizer must not edit.

    The frozen set matters more than the editable set: each entry prevents the
    system from changing the terms of its own evaluation or expanding its reach.
    """


# Surfaces that must never be optimizer-editable. Each prevents a specific
# failure; see Module 9, Lesson 7 §3.
DEFAULT_FROZEN = frozenset({
    "eval_harness",      # else the system optimizes by editing the exam
    "eval_data",         # same
    "permissions",       # else self-improvement becomes privilege escalation
    "egress",            # same
    "budget",            # else "improvement" includes removing its own limits
    "rollback",          # it must survive a bad edit to be worth having
    "logging",           # a system that can silence itself is unauditable
})


@dataclass(frozen=True)
class FailureSignature:
    """A cluster of failures grouped by MECHANISM, not by error code.

    Twenty runs that all ended in TimeoutError may be three unrelated problems.
    Grouped by error code they look like one; grouped by mechanism, the fix for
    each is different.
    """

    terminal: str        # what the run ended with
    behaviour: str       # what the agent did that caused it
    mechanism: str       # the abstract, reusable description
    count: int = 0
    surface: str = ""    # the editable surface a fix would touch

    @property
    def id(self) -> str:
        return hashlib.sha256(self.mechanism.encode()).hexdigest()[:8]

    def __str__(self) -> str:
        return f"[{self.id}] {self.mechanism} (n={self.count}) -> {self.surface or 'unmapped'}"


def mine_weaknesses(
    failures: Sequence[dict], *, classify: Callable[[dict], FailureSignature]
) -> list[FailureSignature]:
    """Cluster failures by mechanism and rank by frequency."""
    counts: dict[str, FailureSignature] = {}
    for failure in failures:
        sig = classify(failure)
        existing = counts.get(sig.id)
        counts[sig.id] = FailureSignature(
            sig.terminal, sig.behaviour, sig.mechanism,
            (existing.count if existing else 0) + 1, sig.surface,
        )
    return sorted(counts.values(), key=lambda s: -s.count)


@dataclass
class Candidate:
    """One bounded edit to one declared surface.

    Minimality is not fastidiousness: a broad rewrite that improves the score is
    uninterpretable — you cannot tell which part helped or revert half of it.
    """

    surface: str
    edit: Any
    targets: str = ""            # the failure signature id this addresses
    rationale: str = ""
    parent: str | None = None

    @property
    def id(self) -> str:
        return hashlib.sha256(f"{self.surface}{self.edit}".encode()).hexdigest()[:8]


@dataclass(frozen=True)
class Scores:
    held_in: float
    held_out: float
    cost: float = 0.0
    per_category: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    reason: str
    scores: Scores | None = None
    regressions: tuple[str, ...] = ()


@dataclass
class HeldOutGate:
    """The acceptance criterion. This stage is load-bearing.

    A candidate is accepted only if held-in AND held-out both hold, with at
    least one positive gain and neither regressing. Without the held-out arm,
    the loop reliably discovers edits that raise the score on exactly the cases
    it was shown and nowhere else.

    **Set min_gain from your split size, not from optimism.** A delta of 0.005
    on a 200-case split is ONE flipped case — indistinguishable from noise, and
    a loop running hundreds of rounds against a gate that accepts single-case
    deltas will accumulate noise as "improvement." Use `for_split()` to derive
    a floor of several net case-flips. (Because the same cases are scored
    before and after, this is a PAIRED comparison — far more sensitive than the
    unpaired ±1.96·sqrt(0.25/n) margin from Module 6 suggests — but one net
    flip is still one coin toss, whatever the test.)
    """

    min_gain: float = 0.005
    regression_tolerance: float = 0.0
    # Per-category regression tracking: the mean holds while the composition
    # underneath it churns. Catastrophic forgetting is invisible to an average.
    max_category_regression: float = 0.05

    @classmethod
    def for_split(cls, held_out_n: int, *, min_net_flips: int = 3, **kwargs) -> "HeldOutGate":
        """A gate whose min_gain demands at least `min_net_flips` net flipped
        cases on the held-out split. At n=200 with the default, that is a
        min_gain of 1.5% — an improvement you can point at, not a lucky case.
        """
        if held_out_n <= 0:
            raise ValueError("held_out_n must be positive")
        return cls(min_gain=min_net_flips / held_out_n, **kwargs)

    def judge(self, baseline: Scores, candidate: Scores) -> Verdict:
        d_in = candidate.held_in - baseline.held_in
        d_out = candidate.held_out - baseline.held_out

        if d_in < -self.regression_tolerance:
            return Verdict(False, f"held-in regression ({d_in:+.3f})", candidate)
        if d_out < -self.regression_tolerance:
            return Verdict(False, f"held-out regression ({d_out:+.3f})", candidate)
        if max(d_in, d_out) < self.min_gain:
            return Verdict(False, f"no material gain (in {d_in:+.3f}, out {d_out:+.3f})", candidate)

        regressed = tuple(
            cat for cat, score in candidate.per_category.items()
            if baseline.per_category.get(cat, score) - score > self.max_category_regression
        )
        if regressed:
            return Verdict(
                False,
                f"per-category regression in {', '.join(regressed)} — "
                f"the mean improved while these got worse",
                candidate,
                regressed,
            )

        # The diagnostic case: big held-in gain, negligible held-out gain.
        if d_in >= 4 * max(d_out, 1e-9) and d_out < self.min_gain * 2:
            return Verdict(
                False,
                f"fits the held-in split ({d_in:+.3f}) but not held-out ({d_out:+.3f}) — "
                f"this is the optimizer learning your evaluator, not the task",
                candidate,
            )
        return Verdict(True, f"held-in {d_in:+.3f}, held-out {d_out:+.3f}", candidate)


@dataclass
class Archive:
    """Every candidate ever proposed, accepted or not.

    Rejected candidates are logged, not discarded — 'we tried this and it
    regressed' is high-value context for the next proposal round. Sampling from
    the archive rather than only from the current best is the standard
    mitigation for diversity collapse.
    """

    entries: list[tuple[Candidate, Verdict]] = field(default_factory=list)

    def record(self, candidate: Candidate, verdict: Verdict) -> None:
        self.entries.append((candidate, verdict))

    @property
    def accepted(self) -> list[Candidate]:
        return [c for c, v in self.entries if v.accepted]

    @property
    def rejected(self) -> list[tuple[Candidate, Verdict]]:
        return [(c, v) for c, v in self.entries if not v.accepted]

    def pareto(self) -> list[tuple[Candidate, Scores]]:
        """Non-dominated candidates on accuracy vs. cost.

        Single-objective optimization on accuracy reliably finds harnesses that
        are marginally better and dramatically more expensive. Keeping cost as
        an explicit axis surfaces the trade instead of hiding it.
        """
        scored = [(c, v.scores) for c, v in self.entries if v.accepted and v.scores]
        frontier = []
        for cand, sc in scored:
            dominated = any(
                other.held_out >= sc.held_out and other.cost <= sc.cost
                and (other.held_out > sc.held_out or other.cost < sc.cost)
                for _, other in scored
            )
            if not dominated:
                frontier.append((cand, sc))
        return sorted(frontier, key=lambda cs: -cs[1].held_out)

    def diversity(self) -> float:
        """Fraction of distinct surfaces touched by accepted candidates.

        A collapsing search converges on one surface. The score plateaus
        smoothly and it looks like convergence; it is the search dying.
        """
        accepted = self.accepted
        if not accepted:
            return 0.0
        return len({c.surface for c in accepted}) / len(accepted)


@dataclass
class MetaHarness:
    """The outer loop: propose -> evaluate -> accept, inside a frozen envelope."""

    editable: frozenset[str]
    evaluate: Callable[[dict], Scores]
    gate: HeldOutGate = field(default_factory=HeldOutGate)
    frozen: frozenset[str] = DEFAULT_FROZEN
    archive: Archive = field(default_factory=Archive)

    def __post_init__(self) -> None:
        overlap = self.editable & self.frozen
        if overlap:
            raise FrozenSurfaceError(
                f"Surfaces declared both editable and frozen: {sorted(overlap)}. "
                f"The frozen set exists so the optimizer cannot change the terms "
                f"of its own evaluation."
            )

    def check_surface(self, candidate: Candidate) -> None:
        if candidate.surface in self.frozen:
            raise FrozenSurfaceError(
                f"Proposal targets frozen surface {candidate.surface!r}. "
                f"Refused regardless of how much it would improve the score."
            )
        if candidate.surface not in self.editable:
            raise FrozenSurfaceError(
                f"Surface {candidate.surface!r} is not declared editable. "
                f"Editable surfaces: {sorted(self.editable)}."
            )

    def step(self, harness: dict, candidate: Candidate, baseline: Scores) -> Verdict:
        """Evaluate one bounded edit against the gate."""
        self.check_surface(candidate)
        trial = {**harness, candidate.surface: candidate.edit}
        verdict = self.gate.judge(baseline, self.evaluate(trial))
        self.archive.record(candidate, verdict)
        return verdict

    def run(
        self,
        harness: dict,
        propose: Callable[[dict, Archive], Iterable[Candidate]],
        *,
        rounds: int = 10,
        plateau_after: int = 3,
    ) -> tuple[dict, Scores]:
        """Run the outer loop until it improves no further."""
        baseline = self.evaluate(harness)
        barren = 0

        for _ in range(rounds):
            improved = False
            for candidate in propose(harness, self.archive):
                try:
                    verdict = self.step(harness, candidate, baseline)
                except FrozenSurfaceError:
                    continue                      # refused; never reaches evaluation
                if verdict.accepted and verdict.scores:
                    harness = {**harness, candidate.surface: candidate.edit}
                    baseline = verdict.scores
                    improved = True
            barren = 0 if improved else barren + 1
            if barren >= plateau_after:
                break
        return harness, baseline
