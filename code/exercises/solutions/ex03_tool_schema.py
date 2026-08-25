"""Reference solution for exercise 03."""

from ce import ToolRegistry


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()

    reg.register(
        "search_products",
        "Search the catalog by keyword when you do NOT have a SKU; "
        "use get_product when you do.",
        {
            "query": {"type": "string", "description": "Keywords, e.g. 'running shoes'."},
            "category": {"type": "string", "enum": ["electronics", "apparel", "home_goods"]},
            "limit": {"type": "integer", "description": "Max results, default 5."},
        },
        required=("query",),
    )(lambda **kw: "results...")

    reg.register(
        "get_product",
        "Full record for one product — details, price, and stock in one object. "
        "Use search_products when you don't yet have a SKU.",
        {"sku": {"type": "string", "description": "Exact SKU, e.g. 'EL-9921'."}},
        required=("sku",),
    )(lambda **kw: "product...")

    reg.register(
        "get_orders",
        "A customer's orders; pass order_id to fetch exactly one.",
        {"customer_id": {"type": "string"}, "order_id": {"type": "string"}},
        required=("customer_id",),
    )(lambda **kw: "orders...")

    reg.register(
        "modify_order",
        "Change an order's state. 'cancel' is reversible; 'delete' is permanent "
        "and requires supervisor confirmation. Reason is recorded in the audit log.",
        {
            "order_id": {"type": "string"},
            "action": {"type": "string", "enum": ["cancel", "refund", "delete"]},
            "reason": {"type": "string", "description": "Required; audit-logged."},
            "confirm": {"type": "boolean", "description": "Must be true."},
        },
        required=("order_id", "action", "reason", "confirm"),
        destructive=True,
    )(lambda **kw: "modified...")

    return reg
