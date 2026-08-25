import unittest

from ce import Budget, ContextAssembler, Stability
from exercises._loader import load

ex = load("ex01_cache_order")

FIXED = dict(
    system_prompt="You are a careful assistant. Cite every claim.",
    tool_schemas="[search(query), read(path)]",
    conventions="This repo uses pnpm. Do not touch legacy/.",
    documents="Q2 revenue was $4.2M, up 12% QoQ.",
    chatter="ok cool — sounds good, thanks!",
    goal="Find why EU checkout conversion dropped 8% and report causes.",
)


def sections(turn: int, **overrides):
    kw = {**FIXED, "timestamp": f"2026-08-26T11:0{turn}:00Z",
          "task": "Continue the investigation.", **overrides}
    return ex.build_sections(**kw)


class TestCacheSafety(unittest.TestCase):
    def test_the_timestamp_does_not_poison_the_stable_prefix(self):
        asm = ContextAssembler()
        asm.assemble(sections(1))
        second = asm.assemble(sections(2))       # only the timestamp differs
        self.assertTrue(
            second.cache_prefix_stable,
            "the stable prefix changed between turns — something volatile "
            "(the timestamp?) is declared STATIC or DURABLE",
        )

    def test_there_is_a_stable_prefix_at_all(self):
        ctx = ContextAssembler().assemble(sections(1))
        self.assertIsNotNone(ctx.cache_breakpoint_after,
                             "no STATIC/DURABLE sections — nothing can cache")
        self.assertGreater(ctx.stable_tokens, 0)


class TestBudgetBehaviour(unittest.TestCase):
    def test_chatter_dies_first_and_the_goal_survives(self):
        squeezed = ContextAssembler(Budget(total=900, response_headroom=100)).assemble(
            sections(1, documents="D " * 1200, chatter="c " * 1200)
        )
        kept = [s.name for s in squeezed.sections]
        self.assertTrue(any("goal" in n for n in kept),
                        "the goal was dropped under budget pressure")
        dropped = [s.name for s in squeezed.dropped]
        self.assertTrue(dropped, "nothing was dropped despite an oversized input")
        self.assertIn(dropped[0], [n for n in dropped if "chatter" in n] or dropped,
                      )
        self.assertTrue(any("chatter" in n for n in dropped),
                        "chatter should be the first thing sacrificed")


class TestOrdering(unittest.TestCase):
    def test_the_task_is_the_last_section(self):
        ctx = ContextAssembler().assemble(sections(1))
        self.assertIn("task", ctx.sections[-1].name.lower())

    def test_nothing_volatile_sits_in_the_stable_prefix(self):
        for s in sections(1):
            if "timestamp" in s.name.lower():
                self.assertGreaterEqual(
                    s.stability, Stability.RETRIEVED,
                    "the timestamp is declared stable — it changes every turn",
                )


if __name__ == "__main__":
    unittest.main()
