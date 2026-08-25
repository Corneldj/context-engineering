"""Lab 04 — Calibrate a live judge, and watch a vague rubric fail.

Companion to: Module 6 Lesson 1 §5.  Estimated cost: < $0.15.

Module 6 claims an uncalibrated judge is a random number generator with good
manners, and that when agreement is poor you fix the RUBRIC, not the model.
This lab runs both rubrics over the same hand-labeled set and reports kappa.

Run:  python3 labs/lab04_judge_calibration.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce import cohens_kappa
from ce.adapters import AnthropicModel, require_key_or_exit

require_key_or_exit("lab04", "< $0.15")

# Hand-labeled: 1 = adequately empathetic, 0 = not. Deliberately includes the
# two cases that separate a good rubric from a bad one: short-and-genuine, and
# long-and-hollow.
LABELED = [
    ("I'm sorry for the inconvenience. Please try again later.", 0),
    ("You missed your filing deadline because our export failed — I've escalated "
     "this to billing and you'll have the file within the hour.", 1),
    ("Just clear your cache and it should work.", 0),
    ("That sounds frustrating, especially right before your launch. I've refunded "
     "the charge and I'm watching the ticket myself until it's closed.", 1),
    ("We sincerely apologize for any inconvenience this may have caused you. "
     "Your satisfaction is extremely important to us and we truly value your "
     "business. We appreciate your patience during this time. Rest assured our "
     "dedicated team is committed to excellence.", 0),   # long and hollow
    ("Fixed — the duplicate charge is reversed. That was our error, not yours.", 1),
    ("Per policy, refunds are not available after 30 days.", 0),
    ("You've been waiting three days for a reply, which isn't acceptable. Here's "
     "the answer, and I've flagged the delay to my manager.", 1),
    ("Have you tried turning it off and on again?", 0),
    ("I can see this blocked your whole team this morning. It's resolved now, and "
     "I've added monitoring so it doesn't repeat.", 1),
]

VAGUE = "Does the response show empathy? Score 1 if yes, 0 if no. Reply with only the digit."

SPECIFIC = """Score the response for empathy using these criteria. Award one point each,
maximum 4. Judge only what is present in the text; do not infer intent.

+1 ACKNOWLEDGES the specific problem in the customer's own terms (not a generic
   "sorry for the inconvenience").
+1 VALIDATES the impact — names a consequence for the customer.
+1 TAKES OWNERSHIP with a concrete next step and who does it ("I've escalated
   this"), rather than deflecting ("you may wish to contact billing").
+1 AVOIDS minimizing language: "just", "simply", "actually", "as I mentioned".

Length is not a criterion; a two-sentence response scoring 4 beats a paragraph
scoring 1. Reply with 1 if the total is 2 or more, otherwise 0. Only the digit."""


def judge(model: AnthropicModel, rubric: str, text: str) -> int:
    r = model.generate(
        system=rubric,
        messages=[{"role": "user", "content": f"<response>{text}</response>"}],
    )
    return 1 if "1" in r.text.strip()[:3] else 0


def main() -> None:
    model = AnthropicModel(max_tokens=8)
    human = [label for _, label in LABELED]

    for name, rubric in (("VAGUE", VAGUE), ("SPECIFIC", SPECIFIC)):
        verdicts = [judge(model, rubric, text) for text, _ in LABELED]
        agree = sum(h == j for h, j in zip(human, verdicts)) / len(human)
        kappa = cohens_kappa(human, verdicts)
        print(f"{name:9} raw agreement {agree:.0%}   kappa {kappa:+.2f}")
        for (text, label), verdict in zip(LABELED, verdicts):
            if label != verdict:
                print(f"    disagreed (human {label}, judge {verdict}): {text[:64]}...")
        print()

    print("""Two things to look for:
  * raw agreement flatters both rubrics; kappa separates them. A judge that
    mostly says 1 scores well on a mostly-1 set and has learned nothing.
  * the long-and-hollow case is where the vague rubric usually breaks —
    verbosity bias, which the specific rubric names and neutralizes.
Same model both times. The rubric was the variable.""")


if __name__ == "__main__":
    main()
