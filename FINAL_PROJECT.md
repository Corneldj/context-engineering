# **Final Project: Build a System You Would Actually Deploy**

## **Objective**

Synthesize the course into one working system: an **Investigative Research Agent** that takes a complex question over a connected corpus, gathers evidence, and returns a structured, cited, confidence-qualified answer — running unattended, on a schedule, with a human in the loop only where it matters.

The emphasis is on the second half of that sentence. An agent that produces a good answer on a demo query is a weekend project. This asks for one you could hand to a colleague and let run overnight — which means the interesting work is in the harness, the graph, the verification, and the evals, not in the prompt.

You will **specify** it as an architecture, **build** it, **measure** it, **attack** it, and then **improve it with a bounded optimizer** — and report honestly on whether that last step actually worked.

---

## **Choose a Domain**

Pick a corpus that is genuinely **connected**, because Part 3 requires it. Good choices:

| Domain | Entities | Why it works |
| :--- | :--- | :--- |
| **A codebase** | files, modules, functions, tests, commits | Links are free and exact (imports, calls) |
| **This course** | modules, lessons, concepts, techniques | Cross-references already exist |
| **Your issue tracker** | issues, PRs, people, services, releases | Relations are already typed |
| **Public filings or papers** | orgs, people, documents, citations | Real entity-resolution difficulty |

**A codebase is the recommended default** — the dependency graph is derivable deterministically, which lets you sidestep the entity-resolution problem for one hop and see clearly what it costs you on the hops where you can't.

---

## **Part 1 — The Architecture Spec (before any code)**

Complete the six-plane spec from [Module 8, Lesson 4](./Lessons/Module8/Lesson4_Agentic_Architecture.md), using [`templates/architecture-spec.md`](./templates/architecture-spec.md).

| Plane | Decide |
| :--- | :--- |
| **1 · Model** | Which model per step; where a cheap model suffices; cache breakpoints |
| **2 · Context** | Assembly order (stable → volatile), retrieval strategy, compaction trigger, token budget |
| **3 · Capability** | Every tool, its permission scope, its error contract — **and what you withheld** |
| **4 · Control** | Trigger, the goal as a *verifiable end state*, topology, all termination conditions |
| **5 · Verification** | The in-loop check and its tier, the eval set, human gates |
| **6 · Governance** | Traces, cost ceiling, **where untrusted input enters**, blast radius |

Two lines are graded most heavily because they're the ones people skip: **"explicitly NOT given"** and **"untrusted input enters at."**

---

## **Part 2 — Build the Agent**

1.  **Tools** with **actionable errors** that never raise into the loop ([M5 L2](./Lessons/Module5/Lesson2_Designing_and_Integrating_Tools.md)). Every tool must have a declared worst-case result size.

2.  **Grounding**, with the retrieval strategy chosen deliberately from your corpus's properties ([M3 L5](./Lessons/Module3/Lesson5_Agentic_Retrieval.md)). *"I used vector RAG because that's what RAG means"* is not a justification.

3.  **A loop with a real exit condition** — trigger, goal, actions, verification, memory ([M8 L2](./Lessons/Module8/Lesson2_Loop_Engineering.md)). It must **not** terminate on the model's self-report. Iteration cap, token budget, and no-progress detection are required.

4.  **Long-horizon context management:** a code-enforced token budget plus **one** of compaction, structured note-taking, or sub-agent isolation ([M4 L4](./Lessons/Module4/Lesson4_Long_Horizon_Context.md)). Say why you chose that one.

5.  **Citations, verified programmatically.** Check that each cited source exists and actually contains the claim's supporting text. An unverified citation is decoration.

6.  **Least privilege.** If it can act outward, say what stops a prompt-injected version of it.

---

## **Part 3 — Add the Graph**

This is the Module 9 half, and it must **earn its place** ([M9 L1](./Lessons/Module9/Lesson1_Graph_Engineering.md)).

1.  **Justify it first.** Which of the five conditions apply? What fraction of your realistic query traffic asks something similarity search structurally cannot answer? Write down the number before you build. If it's near zero, **say so and build a smaller graph** — an honest negative result here scores better than an unjustified graph.

2.  **Stages 1–3 before extraction.** Scope, representation, and an **ontology of eight or fewer edge types**, each with direction, cardinality, and whether it is time-varying.

3.  **Enforce the ontology as a quality gate.** Undeclared edge types and wrong endpoint types must be rejected, not warned about.

4.  **Bi-temporal validity** on every time-varying edge. Demonstrate all three queries: *what is true now*, *what was true then*, and *what did we believe then*. **Invalidate; never delete.**

5.  **Answer at least one question vector search cannot** — a multi-hop traversal, a transitive closure, or an **absence** query.

6.  **Track and surface confidence.** Report your per-hop accuracy, compute *p*ⁿ for your deepest traversal, and set a floor below which the system **withholds rather than asserts**.

7.  **Route.** At least two retrieval primitives, chosen by query shape, with the routing decision logged.

---

## **Part 4 — Execution Graph and Durability**

Because your agent runs unattended ([M9 L4](./Lessons/Module9/Lesson4_Execution_Graphs.md)):

1.  **Model it as a graph** — nodes, conditional edges, explicit typed state. Routing must be a **pure function of state**, tested in isolation.
2.  **Checkpoint** after every node. Demonstrate a resume after a mid-run kill, and show the run does **not** redo completed work.
3.  **Fence one side-effecting node** with an idempotency key in a store **separate from the checkpoint**, and show what happens without it.
4.  **A human gate that genuinely suspends** — the process exits, state persists, approval resumes it.
5.  **Apply the stop rule.** Report your chain length and per-step reliability, compute *p*ⁿ, and restructure if it's poor. Show before-and-after arithmetic.

---

## **Part 5 — Measure It**

Build the eval set **before** you finish building the agent ([`templates/eval-set.md`](./templates/eval-set.md)).

1.  **At least 30 cases**, stratified: single-hop factual · multi-hop · temporal ("as of March") · absence · unanswerable · ambiguous · adversarial. **State what your set can and cannot detect** — report the ±margin.
2.  **The four RAG pillars** on a labeled subset: context precision, recall, faithfulness, answer relevance.
3.  **Trajectory scoring** on at least 8 cases across the six dimensions ([M6 L1](./Lessons/Module6/Lesson1_Evaluating_Context_Quality_and_RAG_Performance.md)).
4.  **Graph-specific:** relation precision/recall, stale-edge rate, and end-to-end accuracy **by hop count** — the last one is where the compounding shows up.
5.  **Calibrate a judge** on 20 hand-labeled examples. Report kappa and what you changed in the rubric.
6.  **Cost and latency** per query, with a token breakdown by context section.

---

## **Part 6 — Attack It**

At least **five** red-team cases in CI ([`templates/red-team-cases.md`](./templates/red-team-cases.md)):

*   **Indirect injection** — plant instructions in a document the agent reads.
*   **Exfiltration** — any path out: fetch, rendered image, written file, posted comment.
*   **Scope escape** — read or write outside its permitted scope.
*   **Resource exhaustion** — a crafted query that loops until the budget dies.
*   **Graph poisoning** *(new)* — can a document injected into the corpus create a false edge that a traversal then presents as fact? This is the one people don't think of, and a graph makes it worse: a false edge is *reused* by every future query.

Write failure conditions against **actions, not text**. Then run the trifecta audit: if all three legs are present, break one or document the accepted risk with an owner.

---

## **Part 7 — Improve It With a Bounded Optimizer**

The Module 9 capstone ([M9 L6](./Lessons/Module9/Lesson6_Autonomous_Meta_Harness.md), [L5](./Lessons/Module9/Lesson7_Governing_Self_Modifying_Systems.md)). Keep it small; the point is the governance.

1.  **Split your eval set three ways:** held-in (proposer sees it), held-out (gates acceptance only), **sealed** (never touched by the loop). Say exactly what the proposer can see.
2.  **Declare editable and frozen surfaces.** For each frozen item, name the failure that freezing prevents. Enforce it in code — a proposal targeting a frozen surface must be **refused before it is scored**.
3.  **Mine weaknesses by mechanism**, not error code. Show a cluster that looks like one problem and is three.
4.  **Run at least five rounds** of propose-evaluate-accept with the held-out gate. Log every candidate, accepted and rejected.
5.  **Report honestly:**
    *   Held-in delta, held-out delta, and **sealed-set delta**. The sealed number is the headline.
    *   **Per-category** deltas — did anything collapse while the mean improved?
    *   **Surface diversity** across accepted candidates.
    *   Cost, as a second Pareto axis.
6.  **The honest conclusion.** Did held-out gains survive on the sealed set? **If they didn't, say so.** A well-documented negative result here — *"we ran the loop, gains did not generalize, here is our evidence and our hypothesis"* — scores **higher** than an unexamined positive one. That is the central lesson of Module 9, Lesson 7, and demonstrating you understand it is worth more than a number going up.

---

## **Deliverables**

1.  **Runnable code**, with setup instructions.
2.  **`ARCHITECTURE.md`** — the six-plane spec, updated to what you actually built (note where they differ and why), plus your graph ontology and execution-graph diagram.
3.  **`EVALUATION.md`** — eval set, results by hop count, judge calibration, cost and latency, and **an honest account of what your evals cannot detect**.
4.  **`SECURITY.md`** — red-team cases and results, the trifecta audit, accepted risks with named owners.
5.  **`OPTIMIZATION.md`** — the meta-harness run: splits, frozen surfaces, every candidate, and the sealed-set verdict.
6.  **Three example runs**, including one full trace — and at least one where the agent **failed, withheld, or escalated**. A submission where everything worked is one that wasn't tested hard enough.

---

## **The Write-Up**

In `REFLECTION.md`:

1.  **Which plane is thinnest?** Deliberate scoping, or an unowned concern?
2.  **Did the graph earn its cost?** Answer with your measured traffic fraction and your accuracy-by-hop-count numbers. **"No" is a valid and respectable answer** if you can show the working.
3.  **Trace a real failure** back to a plane and name the *structural* change that prevents recurrence — confirm it is not a wording change.
4.  **What did your evals fail to catch?** Name a failure you found by hand, and write the case that would have caught it.
5.  **What did the optimizer actually learn?** Look at the accepted edits. Are they general improvements, or artifacts of your eval set? How can you tell?
6.  **Which maturity rung** ([M9 L7 §4](./Lessons/Module9/Lesson7_Governing_Self_Modifying_Systems.md)) is your system on, and what single thing is missing to reach the next?
7.  **If you had to raise this one autonomy level**, what evidence would you need? What would make you demote it?

---

## **Grading Emphasis**

| Weight | Area |
| ---: | :--- |
| 20% | **Architecture spec** — completeness, and honesty in the "NOT given" and "untrusted input" lines |
| 20% | **Evaluation** — eval-set quality, judge calibration, accuracy-by-hop-count, candour about limitations |
| 15% | **Harness** — verification that isn't self-report, real termination, actionable tool errors |
| 15% | **Graph** — justified, ontology-gated, bi-temporal, confidence-tracked. Includes a justified *decision not to* |
| 15% | **Optimizer governance** — frozen surfaces enforced in code, three-way split, honest sealed-set reporting |
| 10% | **Security** — red-team rigour and the trifecta audit |
| 5% | **The agent itself** — does it produce good, cited, grounded answers |

The agent working is worth the least, and that is deliberate. It is the summary of the whole course:

> **Anyone can get an agent to work once. The engineering is knowing that it works, knowing when it doesn't, bounding what happens when it fails — and being honest about which of your improvements were real.**

---

## **A Scaled-Down Version**

If you don't have time for all seven parts, this ordering preserves the most learning per hour:

1.  **Parts 1, 2, 5** — spec, agent, evals. The irreducible core.
2.  **Part 6** — security. Cheap and high-value.
3.  **Part 3**, with a small hand-curated graph over ~50 entities. You still meet the ontology gate, bi-temporality, and confidence arithmetic.
4.  **Part 7** on a single surface (the system prompt), three rounds. The governance is the lesson, not the scale.
5.  **Part 4** last — it matters most for genuinely long unattended runs.

The [reference harness in `code/`](./code/) implements most of the primitives you'll need. Use it, extend it, or reimplement it — but if you extend it, **extend the tests first.**
