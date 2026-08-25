"""Lab 01 — What MockModel deliberately hides: real non-determinism.

Companion to: Module 6 Lesson 1 (why eval sets need size) and the course's own
choice to teach offline.  Estimated cost: < $0.02.

Run:  python3 labs/lab01_nondeterminism.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce.adapters import AnthropicModel, require_key_or_exit

require_key_or_exit("lab01", "< $0.02")

PROMPT = ("Name the single most important guardrail for an unattended agent "
          "loop, in one sentence.")

print("Same prompt, five calls, default temperature:\n")
model = AnthropicModel(max_tokens=200)
answers = []
for i in range(5):
    r = model.generate(system="You are terse.", messages=[{"role": "user", "content": PROMPT}])
    answers.append(r.text.strip())
    print(f"  {i+1}. ({r.output_tokens} out-tokens) {r.text.strip()[:100]}")

distinct = len(set(answers))
spread = [len(a) for a in answers]
print(f"\n  distinct answers: {distinct}/5   length spread: {min(spread)}-{max(spread)} chars")

print("\nSame prompt, temperature 0:\n")
cold = AnthropicModel(max_tokens=200, temperature=0.0)
cold_answers = {cold.generate(system="You are terse.",
                              messages=[{"role": "user", "content": PROMPT}]).text.strip()
                for _ in range(3)}
print(f"  distinct answers at t=0: {len(cold_answers)}/3")

print("""
The point: every offline test in this course is deterministic BY CONSTRUCTION,
which is what makes the harness testable. The live system is not. This is why
Module 6 sizes eval sets the way it does — a single run of a single case is a
coin observed once — and why temperature 0 reduces variance without abolishing
it (serving infrastructure can still vary).""")
