"""Reference solution for exercise 01."""

from ce import Section, Stability


def build_sections(
    *, system_prompt: str, tool_schemas: str, conventions: str,
    documents: str, chatter: str, goal: str, timestamp: str, task: str,
) -> list[Section]:
    return [
        # Stable prefix: cached across every turn of the session.
        Section("system", system_prompt, Stability.STATIC, value=100, droppable=False),
        Section("tools", tool_schemas, Stability.STATIC, value=100, droppable=False),
        Section("conventions", conventions, Stability.DURABLE, value=80),
        # Per-request material.
        Section("documents", documents, Stability.RETRIEVED, value=60),
        Section("chatter", chatter, Stability.RECENT, value=5),
        # The goal is volatile in position but must never be dropped — value
        # and stability are deliberately separate axes.
        Section("goal", goal, Stability.VOLATILE, value=100, droppable=False),
        # Anything that changes every turn lives at the bottom, never above
        # the stable prefix. A timestamp at the top costs you the whole cache.
        Section("timestamp", timestamp, Stability.VOLATILE, value=10),
        Section("task", task, Stability.VOLATILE, value=100, droppable=False),
    ]
