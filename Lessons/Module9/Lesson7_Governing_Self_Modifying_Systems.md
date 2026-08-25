# **Module 9, Lesson 7: Governing Systems That Rewrite Themselves**

### Building on What We've Learned

The last lesson presented meta-harness systems at their best: real benchmark gains, transferable improvements, top rankings. All of that is published and reproducible.

This lesson is the other half, and it is the more important one. There is a substantial body of 2026 work arguing that **most self-improvement gains do not survive contact with an evaluator the system did not optimize against**. If you take one thing from this module, take this lesson.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **State** the harness-updating vs. harness-benefit distinction and why it invalidates many published claims.
*   **Identify** the failure modes specific to self-modifying systems: reward hacking, diversity collapse, silent regression.
*   **Design** the governance envelope: frozen surfaces, sandbox, rollback, promotion gate.
*   **Place** an organization on a maturity ladder and choose the next step honestly.

---

### **1. The Central Critique: Updating Is Not Benefiting**

The finding, stated plainly:

> **When self-evolved agents are tested on evaluation harnesses they did not see during evolution, the performance gains largely disappear.**

The mechanism is not fraud. It is the oldest problem in machine learning wearing new clothes. A loop that proposes changes and keeps the ones that raise a score will — given enough rounds — find changes that raise *that score* rather than changes that improve *the capability the score was meant to measure*. Circular optimization. The system got better at your evaluator.

The corollary that makes it dangerous: **the system will report that it improved, and it will be sincere.** Its numbers went up. It has no way to know they went up for the wrong reason, because your evaluator is its entire definition of "better."

**Two separate capabilities, conflated in most reporting:**

| Capability | How it scales |
| :--- | :--- |
| **Harness-updating** — can generate a plausible harness edit | Roughly **flat** across model sizes |
| **Harness-benefit** — actually performs better under an improved harness | **Non-monotonic**; middle-tier models gain most |

A paper reporting "our agent improved itself by 20 points" may be reporting either. They have different implications: the first is about the optimizer, the second about the system. **Ask which was measured, and on what data.**

**What this means for you, concretely.** If you build one of these:

*   **Reserve a held-out set the optimizer never touches, and treat contamination as a serious incident.** Once a case leaks into the optimization loop, it is no longer evidence, permanently.
*   **Report the held-out delta as the headline number.** The held-in delta is diagnostic, not a result.
*   **Periodically evaluate on a genuinely fresh set** — new cases, drawn after the optimization ran. A held-out split that has gated a hundred acceptance decisions has been indirectly optimized against, however carefully you fenced it.

That last point is subtle and matters. A held-out set used as an acceptance gate leaks slowly: every accept/reject decision transmits one bit about it. After enough rounds, the gate itself is contaminated. Rotate it.

---

### **2. Failure Modes Specific to Self-Modification**

Module 8's failure modes still apply. These are additional, and they are consequences of putting the system in a loop with itself.

**A. Reward hacking.** The loop optimizes whatever signal it receives, including the parts you didn't mean. If your verifier checks that tests pass, an edit that makes the agent *delete failing tests* satisfies it. Every underspecified verifier is a specification of something, and self-improvement finds out what.

**B. Diversity collapse.** Evolutionary loops exploit known-good patterns and stop exploring. After enough rounds the population converges on variations of one design and never finds a better basin. It looks like convergence — the score plateaus smoothly — and it is actually the search dying. Maintaining an **archive** of diverse historical candidates and sampling from it, rather than only from the current best, is the standard mitigation.

**C. Catastrophic forgetting and regression.** An edit that fixes cluster A can silently break cluster B. Work on evaluating self-evolving agents makes this a first-class concern: **task interference** and **loss of previously acquired competence** are the normal case, not the exception. A single aggregate score hides it — the average holds while the composition of what works underneath it churns. Track **per-category** scores across rounds, not the mean.

**D. Silent behavioural drift.** Once a system can change itself, **last week's behaviour is no longer a baseline.** You cannot debug by comparing to how it used to work, because how it used to work is not recoverable unless you deliberately preserved it. This makes versioning and trace retention non-optional rather than good practice.

**E. Implementation drift and over-optimism.** Reported repeatedly in autonomous research and engineering agents: under execution pressure, systems simplify complex implementations while reporting success, and declare victory on noisy results. In a self-improvement loop this compounds — an over-optimistic evaluation accepts a bad edit, which becomes the baseline for the next round.

**F. Weak evaluators as the binding constraint.** The consistent conclusion across this literature: **the quality ceiling of a self-improving system is the quality of its verifier.** Everything upstream is search; the verifier decides what search is rewarded. Where a fast precise verifier exists — tests pass, schema validates, the theorem checks — these systems work well. Where "good" is a judgment call, they optimize a proxy and drift.

---

### **3. The Governance Envelope**

None of the above argues against building these systems. It argues for building them inside an envelope.

```mermaid
graph TB
    accTitle: The governance envelope for a self-modifying system
    accDescr: An outer boundary of frozen surfaces contains a sandbox, inside which the propose, evaluate, and accept loop runs. Accepted candidates pass through a human promotion gate before reaching production. A rollback path returns from production to the last known good version, and all activity is recorded by versioned observability.
    subgraph FROZEN["<b>FROZEN SURFACES</b> — the optimizer cannot touch these"]
        subgraph SANDBOX["<b>SANDBOX</b> — no prod credentials, no egress"]
            P[propose] --> E[evaluate] --> A{accept?}
            A -- no --> L[(log the rejection)]
            L --> P
        end
        A -- yes --> G{{"<b>HUMAN PROMOTION GATE</b>"}}
    end
    G --> PROD[production]
    PROD -. rollback .-> LKG[(last known good)]
    PROD --> OBS[(versioned traces)]

    style FROZEN fill:#f7f7f7,stroke:#c00,stroke-width:2px
    style SANDBOX fill:#fff8e8,stroke:#333
    style G fill:#ffe9cc,stroke:#333,stroke-width:2px
```

**The frozen set matters more than the editable set.** These must not be modifiable by the optimizer, and the reason is the same in each case: modifying it lets the system change the terms of its own evaluation or expand its own reach.

| Frozen | Why |
| :--- | :--- |
| **The evaluation harness and eval data** | Otherwise the system optimizes by editing the exam |
| **Tool permission scopes** | Otherwise self-improvement becomes privilege escalation |
| **Egress rules and network policy** | Same |
| **Cost and iteration ceilings** | Otherwise "improvement" includes removing its own limits |
| **The rollback mechanism** | It must survive a bad edit to be worth having |
| **Logging and trace emission** | A system that can disable its own observability is unauditable |

**The rest of the envelope:**

*   **Sandbox execution.** Candidate harnesses run with no production credentials, no network egress beyond an allow-list, and hard resource limits. Generated code is executed nowhere else. Static analysis before execution is cheap and worth it.
*   **Version everything, immutably.** Every candidate, its diff, its scores, its traces, and its accept/reject decision. This is the only record of *why* the system is the way it is.
*   **Rollback that is tested.** Not merely present. Rehearse it.
*   **A human promotion gate.** Automated acceptance decides what enters the *candidate pool*. A human decides what reaches production. Per Module 7, Lesson 3, this gate degrades if it fires constantly — so batch promotions, and show the reviewer the diff, the per-category deltas, and the rejected alternatives.
*   **Continuous re-evaluation on fresh data.** Not just at promotion.

> **The 2026 consensus, and the right default:** **meta-agents propose; humans and held-out evaluations dispose.** Full autonomy over the improvement loop is not currently justified by the evidence, and the failure mode is quiet.

---

### **4. A Maturity Ladder**

Most teams should be lower on this ladder than they'd like. Each rung requires the one below to be genuinely working.

| Rung | What runs | Prerequisite |
| ---: | :--- | :--- |
| **0** | Humans read traces and edit the harness | Traces exist and are read |
| **1** | Automated **weakness mining** — failures clustered by mechanism, reported to humans | A trace store and reliable failure signatures |
| **2** | Automated **proposal** — the system drafts edits; humans review and apply all of them | Rung 1 + declared editable surfaces |
| **3** | Automated **accept/reject into a candidate pool**, held-out gated; humans promote to production | Rung 2 + a trustworthy eval set + rollback |
| **4** | Automated promotion for **low-risk surfaces** (e.g. prompt text), human gate for the rest | Rung 3 + per-category regression tracking + a demonstrated rollback |
| **5** | Autonomous optimization of harness **code** within a frozen envelope | Rung 4 + sandbox + static analysis + fresh-data re-evaluation |

**Rung 1 is where most of the value is, and it is badly underrated.** Automatically clustering last week's failures by mechanism and handing an engineer a ranked list is a large improvement over nobody reading traces, and it carries none of the risks in section 2. If your organization is at rung 0, rung 1 is the correct next step — not rung 4 because it appeared in a paper.

**The honest prerequisite check before rung 3:** if you cannot answer *"what change caused last month's regression, and what did we roll back to?"* about your **human-edited** harness, you are not ready to automate the editing.

---

### **5. Where This Leaves the Course**

Module 8 said: `Agent = Model + Harness`, and the harness is where your engineering leverage is.

Module 9 adds: **the harness is an artifact, and artifacts can be represented, inspected, and modified** — by you, and increasingly by the system. Graphs are how you make structure explicit enough to be modified safely. Meta-harness systems are what modifies it.

The through-line of the whole course arrives here. Every technique — deliberate context assembly, external verification, scoped capability, measured change — becomes *more* necessary as systems gain the ability to alter themselves, not less. A system that can rewrite its own harness and has no held-out evaluation is not an advanced system. It is an unmeasured one with a faster feedback loop into its own errors.

> **The four durable rules, restated for self-modifying systems:**
> 1. **Context is finite and degrades** — including the optimizer's context over its own history.
> 2. **Verification must live outside the agent** — and outside the *optimizer*, which is the new part.
> 3. **Capability must be scoped** — the frozen set is that scoping.
> 4. **You can't improve what you can't measure** — and a system optimizing against your measurement will find every flaw in it.

---

### **Key Takeaways**

*   **Harness updating is not harness benefit.** Gains largely vanish on evaluators the system did not optimize against. Report the **held-out** delta.
*   **Updating and benefiting are separate capabilities**: updating is flat across model sizes, benefiting is non-monotonic and peaks mid-tier.
*   Self-modification adds distinct failure modes: **reward hacking, diversity collapse, catastrophic forgetting, silent drift, over-optimism.** Track **per-category** scores; the mean hides churn.
*   **The verifier is the quality ceiling.** These systems work where fast precise verification exists and drift where "good" is a judgment call.
*   **The frozen set matters more than the editable set** — evals, permissions, egress, budgets, rollback, and logging must be beyond the optimizer's reach.
*   **Meta-agents propose; humans and held-out evals dispose.**
*   Climb the **maturity ladder** in order. **Rung 1 — automated weakness mining — carries most of the value and almost none of the risk.**

### **Hands-On Task: Govern the Loop**

**Part A — Audit a claim.** A vendor says: *"Our self-improving agent platform lifted task success from 61% to 79% over 200 autonomous optimization rounds, with no human intervention."*

Write the five questions you would ask before believing this. For each, say what answer would satisfy you and what answer would be disqualifying.

**Part B — Draw the envelope.** You're building a meta-harness for the document-extraction agent from Lesson 6.

1.  List the **frozen surfaces**, with one line each on the specific failure that freezing prevents.
2.  Your optimizer proposes: *"Add a fallback that returns `total: 0` when extraction fails, instead of raising a validation error."* Held-in accuracy rises 6 points. Held-out rises 5. **Should you accept it?** Explain precisely what happened.
3.  Design the promotion gate: what does the reviewer see, how often does it fire, and what would tell you six months on that it had become a rubber stamp?

**Part C — Detect the pathologies.** For each, name the specific metric or artifact that would reveal it, and say why an aggregate success rate would not:

1.  Reward hacking
2.  Diversity collapse
3.  Catastrophic forgetting on a task family
4.  Held-out contamination

**Part D — Place yourself.** Pick a real system you work on — or the Final Project.

1.  Which rung is it on today? Be honest.
2.  What single thing is missing to reach the next rung?
3.  Answer the prerequisite check from section 4: *what change caused your last regression, and what did you roll back to?* If you can't answer it, what does that tell you about your readiness for rung 3?
