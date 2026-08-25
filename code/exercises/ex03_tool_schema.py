"""Exercise 03 — A pruned, disambiguated tool set.

Lesson: Module 5 Lesson 2 §3A, §4 (and the Part C task you may have done on paper).

The e-commerce agent had fourteen overlapping tools. Build the pruned registry:
EXACTLY these four, designed so no pair is ambiguous:

  search_products(query, category?, limit?)
      - `category` constrained by enum to: electronics, apparel, home_goods
  get_product(sku)
      - absorbs the old get_price/check_inventory/get_details trio: one object
  get_orders(customer_id, order_id?)
  modify_order(order_id, action, reason, confirm)
      - `action` enum: cancel, refund, delete
      - `reason` and `confirm` REQUIRED (they feed the audit log and the gate)
      - the ONLY destructive tool

Descriptions are prompt surface: search_products and get_product must each say
when to use the OTHER ("use X when …"), by name.

Grade with:  python3 exercises/check.py ex03
"""

from ce import ToolRegistry


def build_registry() -> ToolRegistry:
    raise NotImplementedError("four tools, cross-referencing descriptions, one destructive")
