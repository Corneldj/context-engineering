"""Exercise 08 — Model the domain before extracting.

Lesson: Module 9 Lesson 2 §2 (and Lesson 1 §2 on typed edges).

Implement `build_graph()`: declare an ontology and load the incident-domain
facts below into a `ce.Graph`, such that the tests can answer:

  * "who owns the service that caused INC-7?"        (a 3-hop traversal)
  * "which services have no owner?"                  (an absence query)
  * and an undeclared edge type is REFUSED, not stored.

Entities:  Team platform, Team payments · Service auth-lib, payments-api,
           legacy-cron · Incident INC-7 · Deploy deploy-412
Facts:     platform owns auth-lib · payments owns payments-api ·
           INC-7 caused_by deploy-412 · deploy-412 touched payments-api

Choose node ids, node types, and edge types yourself — the tests query through
YOUR graph's API, but the ontology gate and the two questions must hold.
Keep the edge vocabulary minimal: three types suffice.

Grade with:  python3 exercises/check.py ex08
"""

from ce import Graph


def build_graph() -> Graph:
    raise NotImplementedError("declare EdgeTypes FIRST, then nodes, then facts")
