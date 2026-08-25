import unittest

from exercises._loader import load

ex = load("ex03_tool_schema")


class TestPrunedRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = ex.build_registry()
        self.by_name = {s["name"]: s for s in self.reg.schemas()}

    def test_exactly_the_four_tools(self):
        self.assertEqual(
            set(self.by_name),
            {"search_products", "get_product", "get_orders", "modify_order"},
        )

    def test_cross_referencing_descriptions(self):
        self.assertIn("get_product", self.by_name["search_products"]["description"])
        self.assertIn("search_products", self.by_name["get_product"]["description"])

    def test_category_enum_is_closed(self):
        props = self.by_name["search_products"]["input_schema"]["properties"]
        self.assertEqual(set(props["category"]["enum"]),
                         {"electronics", "apparel", "home_goods"})

    def test_action_enum_is_closed(self):
        props = self.by_name["modify_order"]["input_schema"]["properties"]
        self.assertEqual(set(props["action"]["enum"]), {"cancel", "refund", "delete"})

    def test_only_modify_order_is_destructive(self):
        flags = {name: t.destructive for name, t in self.reg.tools.items()}
        self.assertTrue(flags["modify_order"])
        self.assertFalse(any(v for n, v in flags.items() if n != "modify_order"))

    def test_reason_and_confirm_are_required(self):
        req = set(self.by_name["modify_order"]["input_schema"]["required"])
        self.assertLessEqual({"order_id", "action", "reason", "confirm"}, req)

    def test_required_fields_are_sane_elsewhere(self):
        self.assertIn("query", self.by_name["search_products"]["input_schema"]["required"])
        self.assertIn("sku", self.by_name["get_product"]["input_schema"]["required"])
        self.assertNotIn("order_id", self.by_name["get_orders"]["input_schema"]["required"])


if __name__ == "__main__":
    unittest.main()
