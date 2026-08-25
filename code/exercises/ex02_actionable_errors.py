"""Exercise 02 — Tool errors an agent can act on.

Lesson: Module 5 Lesson 2 §3C.

`ToolError("Not found")` teaches the agent nothing; it will retry blind or give
up. Implement `register_customer_tools` so that a failed lookup returns an
error the agent can RECOVER from on its next turn:

  * name the input that failed,
  * suggest the closest known email (difflib.get_close_matches is your friend),
  * point at `search_customers` as the fuzzy fallback (register it too).

Grade with:  python3 exercises/check.py ex02
"""

from ce import ToolRegistry

CUSTOMERS = {
    "john@acme.com": "John Doe, plan=pro, since 2024-03-01",
    "priya@acme.com": "Priya Nair, plan=starter, since 2025-11-12",
    "kim@nakamura.dev": "Kim Nakamura, plan=growth, since 2026-01-30",
}


def register_customer_tools(reg: ToolRegistry) -> ToolRegistry:
    raise NotImplementedError(
        "register get_customer(email) and search_customers(name) — "
        "failures must carry a hint and candidates, and must never raise "
        "into the loop"
    )
