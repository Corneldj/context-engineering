"""Tests for externalized state (Module 4, Lesson 4)."""

import tempfile
import unittest
from pathlib import Path

from ce import MockModel, CompactionPolicy, Workspace, compact, say


class TestWorkspace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Workspace(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_goal_is_written_once_and_never_overwritten(self):
        self.ws.set_goal("migrate 400 files")
        self.ws.set_goal("something else entirely")
        self.assertEqual(self.ws.goal, "migrate 400 files")

    def test_state_survives_a_process_restart(self):
        self.ws.set_goal("migrate")
        self.ws.set_plan([{"id": "f1", "what": "file one", "status": "done"}])
        self.ws.record_blocker("regex rewrite", "broke fixtures in 3 files")

        reopened = Workspace(Path(self._tmp.name))
        self.assertEqual(reopened.goal, "migrate")
        self.assertTrue(reopened.is_resumable())
        self.assertIn("broke fixtures", reopened.read(Workspace.BLOCKERS))

    def test_externalized_state_survives_compaction(self):
        """The whole point: compaction cannot delete what was never in the conversation."""
        self.ws.set_goal("migrate 400 files")
        self.ws.record_blocker("regex rewrite", "broke fixtures")

        msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "go"}]
        msgs += [{"role": "assistant", "content": "tried the regex rewrite"} for _ in range(20)]
        model = MockModel(policy=lambda t, m: say("SUMMARY: did some work."))
        compact(msgs, model=model, policy=CompactionPolicy())

        self.assertIn("broke fixtures", self.ws.brief())

    def test_brief_is_small_and_excludes_unbounded_findings(self):
        self.ws.set_goal("g")
        for i in range(500):
            self.ws.record_finding(f"fact {i}", "src")
        self.assertLess(len(self.ws.brief()), 500)

    def test_writes_outside_the_workspace_are_refused(self):
        with self.assertRaises(ValueError):
            self.ws.write("../escaped.md", "nope")

    def test_deep_traversal_is_refused(self):
        with self.assertRaises(ValueError):
            self.ws.write("a/../../../etc/ce_should_never_write_here", "nope")

    def test_absolute_paths_are_refused(self):
        with self.assertRaises(ValueError):
            self.ws.write("/tmp/ce_should_never_write_here", "nope")

    def test_a_sibling_directory_sharing_our_prefix_is_refused(self):
        """`/tmp/ws` string-prefixes `/tmp/ws-evil`. Prefix matching lets this
        through; path containment does not."""
        sibling = self.ws.root.parent / (self.ws.root.name + "-evil")
        with self.assertRaises(ValueError):
            self.ws.write(f"../{sibling.name}/loot.md", "nope")

    def test_mark_updates_plan_status(self):
        self.ws.set_plan([{"id": "a", "what": "x", "status": "todo"}])
        self.ws.mark("a", "done")
        self.assertEqual(self.ws.plan()[0]["status"], "done")


if __name__ == "__main__":
    unittest.main()
