"""Reference solution for exercise 08."""

from ce import EdgeType, Graph, GraphNode


def build_graph() -> Graph:
    g = Graph([
        EdgeType("owns", "Team", "Service", time_varying=True, accuracy=0.95),
        EdgeType("caused_by", "Incident", "Deploy", accuracy=0.85),
        EdgeType("touched", "Deploy", "Service", accuracy=0.98),
    ])
    for nid, ntype, name in [
        ("platform", "Team", "Platform"), ("payments", "Team", "Payments"),
        ("auth-lib", "Service", "auth-lib"), ("payments-api", "Service", "payments-api"),
        ("legacy-cron", "Service", "legacy-cron"),
        ("INC-7", "Incident", "INC-7"), ("deploy-412", "Deploy", "deploy-412"),
    ]:
        g.add_node(GraphNode(nid, ntype, name))
    g.add_edge("platform", "owns", "auth-lib")
    g.add_edge("payments", "owns", "payments-api")
    g.add_edge("INC-7", "caused_by", "deploy-412")
    g.add_edge("deploy-412", "touched", "payments-api")
    return g
