"""Reference solution for exercise 07."""

import re

_MARKER = re.compile(r"\[S:([^\]]+)\]")
_ABSENT = "not in the provided sources"


def score(answer: str, sources: list[dict]) -> int:
    ids = {s["id"] for s in sources}
    cited = _MARKER.findall(answer)
    points = 0

    # CITES — at least one valid marker.
    points += any(c in ids for c in cited)

    # NO_FAKES — no marker naming a nonexistent source (vacuous if none).
    points += all(c in ids for c in cited)

    # GROUNDED — numbers outside the markers must appear in a cited source.
    stripped = _MARKER.sub("", answer)
    numbers = re.findall(r"\d+", stripped)
    cited_text = " ".join(s["text"] for s in sources if s["id"] in cited)
    points += all(n in cited_text for n in numbers) if numbers else 1

    # HONEST_GAP — admit absence iff sources are actually absent.
    claims_absence = _ABSENT in answer.lower()
    points += claims_absence if not sources else not claims_absence

    return points
