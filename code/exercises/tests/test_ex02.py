import unittest

from ce import ToolRegistry
from exercises._loader import load

ex = load("ex02_actionable_errors")


class TestActionableErrors(unittest.TestCase):
    def setUp(self):
        self.reg = ex.register_customer_tools(ToolRegistry())

    def test_success_path(self):
        r = self.reg.dispatch("1", "get_customer", {"email": "john@acme.com"})
        self.assertFalse(r.is_error)
        self.assertIn("John", str(r.content))

    def test_a_typo_returns_a_recovery_not_a_dead_end(self):
        r = self.reg.dispatch("1", "get_customer", {"email": "jon@acme.com"})
        self.assertTrue(r.is_error)
        content = str(r.content)
        self.assertIn("jon@acme.com", content)          # names the failing input
        self.assertIn("john@acme.com", content)         # suggests the near-miss
        self.assertIn("search_customers", content)      # points at the fallback

    def test_nothing_raises_into_the_loop(self):
        r = self.reg.dispatch("1", "get_customer", {"email": "zzz@nowhere"})
        self.assertTrue(r.is_error)                     # returned, not raised

    def test_the_fallback_tool_exists_and_works(self):
        r = self.reg.dispatch("1", "search_customers", {"name": "nakamura"})
        self.assertFalse(r.is_error)
        self.assertIn("kim@nakamura.dev", str(r.content))

    def test_descriptions_disambiguate_the_pair(self):
        schema = next(s for s in self.reg.schemas() if s["name"] == "get_customer")
        self.assertIn("search_customers", schema["description"],
                      "get_customer's description should say when to use the other tool")


if __name__ == "__main__":
    unittest.main()
