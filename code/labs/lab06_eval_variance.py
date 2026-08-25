"""Lab 06 — Why one run of one case tells you nothing.

Companion to: Module 6 Lesson 1 §6.  Estimated cost: < $0.20.

Module 6 says a 20-case eval set has a ±22% margin. This lab makes that
concrete against a live model: run a small eval set several times and watch the
pass rate move without anything changing.

Run:  python3 labs/lab06_eval_variance.py
"""

import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce.adapters import AnthropicModel, require_key_or_exit

require_key_or_exit("lab06", "< $0.20")

# Deliberately borderline: the interesting variance lives at the boundary,
# not on cases every model gets right or wrong every time.
CASES = [
    ("Reply with exactly the word: ready", lambda s: s.strip().lower() == "ready"),
    ("Give the number of sides on a hexagon. Digits only.", lambda s: s.strip() == "6"),
    ("Reply with a single lowercase word naming the colour of the sky on a clear day.",
     lambda s: s.strip().lower().rstrip(".") == "blue"),
    ("Answer with exactly two words: the capital of France.",
     lambda s: len(s.strip().rstrip(".").split()) == 2),
    ("Output valid JSON with one key 'ok' set to true. No prose.",
     lambda s: s.strip().startswith("{") and '"ok"' in s),
    ("Reply with exactly three dashes and nothing else.", lambda s: s.strip() == "---"),
    ("Name one primary colour, single word, no punctuation.",
     lambda s: s.strip().isalpha()),
    ("Reply with the integer that is 17 plus 26. Digits only.", lambda s: s.strip() == "43"),
]

ROUNDS = 5


def main() -> None:
    model = AnthropicModel(max_tokens=32)
    rates = []
    print(f"{len(CASES)} cases, {ROUNDS} identical rounds, nothing changing between them:\n")
    for r in range(1, ROUNDS + 1):
        passed = 0
        for prompt, check in CASES:
            out = model.generate(system="Follow the instruction exactly.",
                                 messages=[{"role": "user", "content": prompt}])
            passed += bool(check(out.text))
        rate = passed / len(CASES)
        rates.append(rate)
        print(f"  round {r}: {passed}/{len(CASES)} = {rate:.0%}")

    spread = max(rates) - min(rates)
    margin = 1.96 * (0.25 / len(CASES)) ** 0.5
    print(f"\n  observed spread across identical rounds: {spread:.0%}")
    if len(rates) > 1:
        print(f"  stdev of the pass rate: {statistics.stdev(rates):.0%}")
    print(f"  unpaired 95% margin at n={len(CASES)}: ±{margin:.0%}")
    print(f"""
Nothing changed between rounds. If you had run this once before a change and
once after, you could have "measured" an improvement of up to {spread:.0%} that
was pure noise — and written it in a changelog.

This is why Module 6 sizes eval sets the way it does, and why Module 9's
acceptance gate denominates its threshold in NET FLIPPED CASES rather than a
percentage that sounds small enough to be safe.""")


if __name__ == "__main__":
    main()
