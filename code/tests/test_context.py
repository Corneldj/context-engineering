"""Tests for cache-aware, budgeted context assembly (Module 4, Module 8 L4)."""

import unittest

from ce import Budget, CacheOrderError, ContextAssembler, Section, Stability, edge_load


class TestCacheSafety(unittest.TestCase):
    def test_stable_content_sorts_above_volatile(self):
        asm = ContextAssembler()
        ctx = asm.assemble([
            Section("task", "do the thing", Stability.VOLATILE),
            Section("system", "you are helpful", Stability.STATIC),
            Section("docs", "retrieved text", Stability.RETRIEVED),
        ])
        order = [s.name for s in ctx.sections]
        self.assertEqual(order, ["system", "docs", "task"])

    def test_cache_breakpoint_is_the_last_stable_section(self):
        asm = ContextAssembler()
        ctx = asm.assemble([
            Section("system", "rules", Stability.STATIC),
            Section("memory", "conventions", Stability.DURABLE),
            Section("task", "now", Stability.VOLATILE),
        ])
        self.assertEqual(ctx.cache_breakpoint_after, "memory")

    def test_a_stable_prefix_that_does_not_change_is_reported_as_cacheable(self):
        asm = ContextAssembler()
        for _ in range(3):
            ctx = asm.assemble([
                Section("system", "you are helpful", Stability.STATIC),
                Section("task", "turn " + str(_), Stability.VOLATILE),
            ])
            self.assertTrue(ctx.cache_prefix_stable)
        self.assertEqual(asm.cache_prefix_breaks, 0)

    def test_a_timestamp_mislabelled_static_is_caught_across_turns(self):
        """Sorting cannot catch this — the declaration is wrong, not the order.

        What catches it is noticing the prefix is no longer byte-identical.
        """
        asm = ContextAssembler()
        first = asm.assemble([
            Section("clock", "now: 2026-08-24T11:00:03Z", Stability.STATIC),
            Section("task", "go", Stability.VOLATILE),
        ])
        second = asm.assemble([
            Section("clock", "now: 2026-08-24T11:00:09Z", Stability.STATIC),
            Section("task", "go", Stability.VOLATILE),
        ])
        self.assertTrue(first.cache_prefix_stable)     # nothing to compare against yet
        self.assertFalse(second.cache_prefix_stable)   # the prefix died here
        self.assertEqual(asm.cache_prefix_breaks, 1)

    def test_strict_mode_turns_a_silent_cost_bug_into_an_exception(self):
        asm = ContextAssembler(strict_cache=True)
        asm.assemble([Section("system", "build 1", Stability.STATIC)])
        with self.assertRaises(CacheOrderError):
            asm.assemble([Section("system", "build 2", Stability.STATIC)])


class TestBudget(unittest.TestCase):
    def test_assembled_context_never_exceeds_the_budget(self):
        asm = ContextAssembler(Budget(total=1_000, response_headroom=200))
        ctx = asm.assemble([
            Section("system", "x" * 400, Stability.STATIC, value=100, droppable=False),
            Section("docs", "y" * 40_000, Stability.RETRIEVED, value=10),
            Section("task", "z" * 100, Stability.VOLATILE, value=100, droppable=False),
        ])
        self.assertLessEqual(ctx.tokens, 800 + 40)  # small rendering overhead
        self.assertIn("docs", [s.name for s in ctx.dropped])

    def test_drops_by_value_not_by_age(self):
        """The naive implementation truncates oldest-first, which is often the goal."""
        # available = 500 tokens; each big section is ~1000 tokens, so exactly
        # one of them must be dropped and the choice must be made on value.
        asm = ContextAssembler(Budget(total=1_600, response_headroom=100))
        ctx = asm.assemble([
            Section("old_but_vital", "a" * 4_000, Stability.DURABLE, value=95),
            Section("new_but_noise", "b" * 4_000, Stability.RECENT, value=5),
            Section("task", "go", Stability.VOLATILE, value=100, droppable=False),
        ])
        kept = [s.name for s in ctx.sections]
        self.assertIn("old_but_vital", kept)
        self.assertNotIn("new_but_noise", kept)

    def test_non_droppable_sections_survive_and_are_truncated_visibly(self):
        asm = ContextAssembler(Budget(total=200, response_headroom=50))
        ctx = asm.assemble([
            Section("task", "q" * 4_000, Stability.VOLATILE, value=100, droppable=False)
        ])
        self.assertEqual([s.name for s in ctx.sections], ["task"])
        self.assertIn("TRUNCATED", ctx.text)

    def test_breakdown_reports_per_section_tokens(self):
        asm = ContextAssembler()
        ctx = asm.assemble([
            Section("system", "a" * 400, Stability.STATIC),
            Section("task", "b" * 40, Stability.VOLATILE),
        ])
        self.assertEqual(set(ctx.breakdown()), {"system", "task"})
        self.assertGreater(ctx.breakdown()["system"], ctx.breakdown()["task"])


class TestVolatileZoneOrdering(unittest.TestCase):
    def test_within_the_volatile_tier_importance_sorts_late(self):
        """Primacy for stable content, recency for volatile: the immediate task
        is the most important volatile section, so it goes LAST — a timestamp
        (volatile, low value) belongs in the cheap seats above it."""
        ctx = ContextAssembler().assemble([
            Section("task", "do the thing", Stability.VOLATILE, value=100, droppable=False),
            Section("timestamp", "11:03:07Z", Stability.VOLATILE, value=10),
            Section("system", "rules", Stability.STATIC, value=100),
        ])
        self.assertEqual([s.name for s in ctx.sections], ["system", "timestamp", "task"])


class TestEdgeLoading(unittest.TestCase):
    def test_best_first_second_best_last_weakest_buried(self):
        ranked = ["best", "2nd", "3rd", "4th", "worst"]
        placed = edge_load(ranked)
        self.assertEqual(placed[0], "best")
        self.assertEqual(placed[-1], "2nd")
        self.assertIn("worst", placed[1:-1])


if __name__ == "__main__":
    unittest.main()
