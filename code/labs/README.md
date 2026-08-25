# **Live-Model Labs**

Six optional labs that run against a **real model**. Everything else in this course is deliberately offline — `MockModel` is what makes the harness testable — and these exist to show you exactly what the mock removes.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
cd code
python3 labs/lab01_nondeterminism.py
```

**Without a key, every lab prints what it would do and exits 0.** Nothing runs by accident.

| Lab | Shows you | Companion | Est. cost |
| :--- | :--- | :--- | ---: |
| `lab01_nondeterminism` | The same prompt, five different answers — and what temperature 0 does and doesn't fix | M6 L1 | < $0.02 |
| `lab02_real_cache` | The cache-ordering claim on the real meter: a prepended timestamp taking `cache_read` to zero, silently | M1 L2 §4 | < $0.05 |
| `lab03_live_loop` | Your Module 8 harness driving a real model in a contained sandbox | M8 L1–L2 | < $0.10 |
| `lab04_judge_calibration` | The same judge, two rubrics, measured kappa — including the long-and-hollow case | M6 L1 §5 | < $0.15 |
| `lab05_injection` | A live model under injection, with and without the capability to act on it | M6 L3 | < $0.10 |
| `lab06_eval_variance` | A pass rate moving across identical runs — the noise you can mistake for progress | M6 L1 §6 | < $0.20 |

**Total, running each once: well under $1.** Costs are estimates; they scale with the model you pick.

## **Configuration**

| Variable | Default | Notes |
| :--- | :--- | :--- |
| `ANTHROPIC_API_KEY` | *(required)* | Without it, labs exit cleanly |
| `CE_LAB_MODEL` | `claude-haiku-4-5-20251001` | A small model is deliberate — the labs demonstrate mechanisms, not capability |

## **Safety**

The labs are written to the same standard the course teaches:

* **Contained filesystem access.** `lab03` gives a live model write tools scoped to a temp directory, and resolves every model-supplied path with `is_relative_to` before touching disk (a string-prefix check would let `/tmp/ws-evil` through). The sandbox is deleted on exit.
* **Cost ceilings, not just turn caps.** `Guardrails(max_cost_usd=...)` alongside `max_iterations`.
* **No real secrets, ever.** `lab05` runs a genuine injection attempt against a live model, but the "sensitive" tool returns a refusal string and records the attempt locally. Nothing leaves your machine.
* **Read-only to your repo.** No lab writes anywhere except its own temp directory.

## **Using a live model in your own code**

[`ce/adapters.py`](../ce/adapters.py) is the whole bridge — it implements the same three-argument `Model` protocol everything else is built on, so `AgentLoop`, `JudgeModel`, and `run_eval` work against it unchanged:

```python
from ce import AgentLoop, Deterministic, Guardrails
from ce.adapters import AnthropicModel

loop = AgentLoop(
    model=AnthropicModel(max_tokens=800),   # the only line that differs
    tools=my_registry,
    verifier=Deterministic(goal_is_met, "..."),
    guardrails=Guardrails(max_iterations=10, max_cost_usd=1.00),
)
```

Two notes. `AnthropicModel` sets a cache breakpoint after the system prompt by default (the Module 1 ordering discipline, on the wire) — pass `cache_system_prompt=False` to disable. And `last_usage` / `cache_report()` expose the provider's real cache counters, which is the only honest way to check the claims in `lab02`.

**Keep your own tests on `MockModel`.** These labs are for building intuition, not for CI: a test suite that needs a network and a credit card is a test suite that stops being run.
