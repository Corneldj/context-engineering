"""Reference solution for exercise 02."""

import difflib

from ce import ToolError, ToolRegistry

CUSTOMERS = {
    "john@acme.com": "John Doe, plan=pro, since 2024-03-01",
    "priya@acme.com": "Priya Nair, plan=starter, since 2025-11-12",
    "kim@nakamura.dev": "Kim Nakamura, plan=growth, since 2026-01-30",
}


def register_customer_tools(reg: ToolRegistry) -> ToolRegistry:
    @reg.register(
        "get_customer",
        "Look up a customer record by exact email address.",
        {"email": {"type": "string", "description": "Full email, e.g. 'john@acme.com'."}},
        required=("email",),
        when_to_use="Use with an exact email; use search_customers for fuzzy lookup.",
    )
    def get_customer(email: str) -> str:
        if email in CUSTOMERS:
            return CUSTOMERS[email]
        close = difflib.get_close_matches(email, CUSTOMERS, n=2, cutoff=0.6)
        raise ToolError(
            f"No customer with email {email!r}.",
            hint=(f"Did you mean {close[0]!r}? " if close else "")
            + "Use search_customers(name) for fuzzy lookup.",
            data={"similar": close},
        )

    @reg.register(
        "search_customers",
        "Fuzzy-search customers by any part of their name or email.",
        {"name": {"type": "string"}},
        required=("name",),
    )
    def search_customers(name: str) -> str:
        needle = name.lower()
        hits = [f"{e}: {r}" for e, r in CUSTOMERS.items() if needle in r.lower() or needle in e]
        return "\n".join(hits) or f"No customers matching {name!r}."

    return reg
