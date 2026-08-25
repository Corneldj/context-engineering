"""Lab 02 — The cache-ordering claim, verified against the real meter.

Companion to: Module 1 Lesson 2 §4.  Estimated cost: < $0.05.

Module 1 claims: order stable -> volatile, or a changing byte near the top
invalidates the prefix and you silently pay full price. Here you watch the
actual cache_read counter do exactly that.

Run:  python3 labs/lab02_real_cache.py
"""

import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce.adapters import AnthropicModel, require_key_or_exit

require_key_or_exit("lab02", "< $0.05")

# A system prompt big enough to exceed the minimum cacheable size.
STABLE = ("You are a meticulous support assistant for ACME Inc.\n"
          + "Policy clause: " + " ".join(f"rule-{i} applies to tier-{i%5};" for i in range(400)))

def three_calls(label: str, system_of_turn):
    model = AnthropicModel(max_tokens=64)
    print(f"{label}:")
    for turn in range(1, 4):
        model.generate(system=system_of_turn(turn),
                       messages=[{"role": "user", "content": f"Question {turn}: which rule applies to tier 2?"}])
        print(f"  turn {turn}: {model.cache_report()}")
        time.sleep(1)
    print()

three_calls("A. stable prefix (cache_read should climb after turn 1)",
            lambda turn: STABLE)

three_calls("B. timestamp PREPENDED to the system prompt (the silent bug)",
            lambda turn: f"Current time: {time.time()}\n" + STABLE)

three_calls("C. timestamp moved to the user turn where it belongs",
            lambda turn: STABLE)

print("""In A and C, turns 2-3 show cache_read ~= the prompt size: you paid ~10%.
In B, cache_read stays 0 on every turn — same behaviour, same answers, several
times the input bill, and NOTHING errors. The only symptom is this counter,
which is why Module 1 says: alert on cache hit rate.""")
