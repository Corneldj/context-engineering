"""Reference solution for exercise 10."""

from ce import HeldOutGate


def make_gate(held_out_n: int) -> HeldOutGate:
    # At n=200 this is min_gain=1.5% — three cases that actually flipped,
    # not one coin toss dressed as progress.
    return HeldOutGate.for_split(held_out_n, min_net_flips=3)


def editable_surfaces() -> frozenset[str]:
    return frozenset({
        "system_prompt",
        "field_descriptions",
        "few_shot_examples",
        "workflow",
        "retry_policy",
    })
    # Deliberately absent: eval_data (editing the exam), permissions and
    # egress (privilege escalation), budget (removing its own limits),
    # logging (silencing the audit trail), output_schema (loosening the spec
    # until every failure passes — the total=0 reward hack).
