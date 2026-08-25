"""Exercise 07 — A judge rubric that two people would score identically.

Lesson: Module 6 Lesson 1 §5.

"Is the answer good? 1-5" gives kappa ~0.3. A usable rubric is a set of
BINARY, TEXTUALLY VERIFIABLE checks. Implement `score(answer, sources)` for a
grounded-answer rubric, one point each, max 4:

  +1 CITES:      the answer contains at least one [S:<id>] marker whose id
                 exists in `sources`
  +1 NO_FAKES:   the answer contains NO [S:<id>] marker whose id does NOT exist
                 (an answer with zero markers earns this point vacuously)
  +1 GROUNDED:   every number (\\d+) in the answer, excluding those inside the
                 [S:...] markers themselves, appears in at least one CITED
                 source's text
  +1 HONEST_GAP: if `sources` is empty, the answer admits it (contains
                 "not in the provided sources", any case); if sources are
                 non-empty, the answer does NOT falsely claim absence

`sources` is a list of {"id": str, "text": str}.

Grade with:  python3 exercises/check.py ex07
"""


def score(answer: str, sources: list[dict]) -> int:
    raise NotImplementedError("four binary checks, one point each")
