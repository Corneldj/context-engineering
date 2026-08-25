"""Reference solution for exercise 09."""

from ce import Graph


def _edge(g: Graph, team: str, service: str):
    return next(e for e in g.out_edges(team, type="owns") if e.target == service)


def record_transfer(g: Graph, service: str, from_team: str, to_team: str, at: int):
    old = _edge(g, from_team, service)
    g.invalidate(old, t_invalid=at)                       # close — never delete
    g.add_edge(to_team, "owns", service, t_valid=at, t_created=at)


def correct_transfer(g: Graph, service: str, from_team: str, to_team: str,
                     actual_at: int, discovered_at: int):
    # Both halves of the correction: the old owner's edge ENDED earlier,
    # and the new owner's edge BEGAN earlier. World clock moves; belief
    # clock records when we found out.
    old = next(e for e in g.edges
               if e.source == from_team and e.target == service and e.type == "owns")
    new = next(e for e in g.edges
               if e.source == to_team and e.target == service and e.type == "owns")
    g.correct(old, actual_t_invalid=actual_at, discovered_at=discovered_at)
    g.correct(new, actual_t_valid=actual_at, discovered_at=discovered_at)
