"""Lab 03 — The Module 8 harness, against a live model and a real sandbox.

Companion to: Module 8 Lessons 1-2, Module 6 Lesson 3.  Estimated cost: < $0.10.

The exact harness you tested offline — verifier, guardrails, actionable tool
errors — driving a real model. Two things this lab is careful about, because a
live model is genuinely untrusted input:

  * Every path the model supplies is resolved and CONTAINED. A tool that does
    `workdir / name` on a model-chosen name is a path-traversal hole; the model
    only has to emit "../../.ssh/authorized_keys" once.
  * The loop carries a hard cost ceiling as well as an iteration cap, so a
    pathological run stops on money, not just on turns.

The sandbox is a temp directory, removed on exit.

Run:  python3 labs/lab03_live_loop.py
"""

import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce import AgentLoop, Deterministic, Guardrails, ToolError, ToolRegistry
from ce.adapters import AnthropicModel, require_key_or_exit

require_key_or_exit("lab03", "< $0.10")


def build_registry(workdir: pathlib.Path) -> ToolRegistry:
    root = workdir.resolve()

    def contained(name: str) -> pathlib.Path:
        """Resolve a model-supplied name inside the sandbox, or refuse it.

        This is Module 6, Lesson 3's least-privilege rule in four lines. Note
        it uses `is_relative_to`, not a string prefix: `/tmp/ws` prefixes
        `/tmp/ws-evil`.
        """
        p = (root / name).resolve()
        if not p.is_relative_to(root):
            raise ToolError(
                f"Refused: {name!r} resolves outside the working directory.",
                hint="Use a plain filename in the working directory, e.g. 'greeting.txt'.",
            )
        return p

    reg = ToolRegistry()

    @reg.register("list_files", "List the files in the working directory.", {})
    def list_files() -> str:
        return "\n".join(sorted(f.name for f in root.iterdir())) or "(empty)"

    @reg.register("read_file", "Read one file from the working directory.",
                  {"name": {"type": "string", "description": "Filename, e.g. 'greeting.txt'."}},
                  required=("name",))
    def read_file(name: str) -> str:
        p = contained(name)
        if not p.is_file():
            raise ToolError(f"No file {name!r}.",
                            hint=f"Files present: {sorted(f.name for f in root.iterdir())}")
        return p.read_text(encoding="utf-8")

    @reg.register("write_file", "Overwrite one file in the working directory.",
                  {"name": {"type": "string"},
                   "content": {"type": "string", "description": "Full new contents."}},
                  required=("name", "content"))
    def write_file(name: str, content: str) -> str:
        p = contained(name)
        p.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} chars to {name}"

    return reg


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ce_lab03_") as tmp:
        workdir = pathlib.Path(tmp)
        target = workdir / "greeting.txt"
        target.write_text("helo wrold\n", encoding="utf-8")

        loop = AgentLoop(
            model=AnthropicModel(max_tokens=600),
            tools=build_registry(workdir),
            # The verifier reads the FILESYSTEM. The model cannot talk its way
            # to success, however confidently it reports one.
            verifier=Deterministic(
                lambda _s: target.is_file() and target.read_text().strip() == "hello world",
                "greeting.txt contains exactly 'hello world'",
            ),
            system_prompt=("You fix files using the provided tools. "
                           "Act using tools; do not narrate a plan."),
            guardrails=Guardrails(
                max_iterations=6,
                max_tokens=50_000,
                max_cost_usd=0.25,        # a real ceiling, not just a turn count
                no_progress_after=3,
            ),
        )

        outcome = loop.run(
            "The file greeting.txt contains a misspelled greeting. "
            "Fix it to contain exactly: hello world"
        )

        print(outcome)
        print(f"file now contains: {target.read_text()!r}\n")
        print(outcome.trace.render())

        print("""
Notice, then compare against your offline tests:
  * the loop exited when the FILE was right, not when the model said it was
  * every path the model supplied was contained before it touched the disk
  * tokens, cost, and every tool call are accounted for in the trace
  * re-run this: the trajectory may differ, the OUTCOME must not

The sandbox directory is removed when this exits.""")


if __name__ == "__main__":
    main()
