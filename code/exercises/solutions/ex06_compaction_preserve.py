"""Reference solution for exercise 06."""

import re

from ce import clear_stale_tool_results
from ce import tokens as tok

_PROTECTED = re.compile(r"TRIED:|INC-\d+")


def _total(messages: list[dict]) -> int:
    return sum(tok.count(str(m.get("content", ""))) for m in messages)


def shrink(messages: list[dict], budget: int) -> list[dict]:
    # Step 1 — the free, lossless win: old tool results become one-line stubs.
    out = clear_stale_tool_results(messages, keep_recent=2)
    if _total(out) <= budget:
        return out

    # Step 2 — drop by VALUE, not by age. Protected content never drops:
    # the goal (first user message), dead ends, exact identifiers.
    first_user = next((i for i, m in enumerate(out) if m.get("role") == "user"), None)

    def protected(i: int, m: dict) -> bool:
        if i == first_user:
            return True
        return bool(_PROTECTED.search(str(m.get("content", ""))))

    kept = list(out)
    for i, m in enumerate(out):                      # oldest first
        if _total(kept) <= budget:
            break
        if m.get("role") == "assistant" and not protected(i, m):
            kept.remove(m)
    return kept
