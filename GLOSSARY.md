# **Glossary of Key Terms**

Definitions for the key concepts used in the *Context Engineering for AI* course. Terms marked **(historical)** appear in older material and are included so you can recognize them, with a note on what superseded them.

---

### **A**

*   **Absence Query:** A question about what does *not* exist ("which services have no owner?"). Similarity search can only retrieve things that exist, so only a structured store can answer this class of question at all.
*   **A2A (Agent2Agent) Protocol:** An open standard for communication *between* independent AI agents, including across organizational boundaries. Agents publish "Agent Cards" advertising their capabilities; others discover them, assign tasks, and exchange artifacts. Reached v1.0 under Linux Foundation governance in April 2026. Complementary to MCP: **MCP connects an agent to its tools; A2A connects an agent to another agent.**
*   **Agent (AI Agent):** A system that uses a model to reason, plan, and use tools to achieve a goal, rather than only answering questions. See also **Harness**.
*   **`Agent = Model + Harness`:** The 2026 working definition of an agent. The model supplies reasoning; the harness makes that reasoning reliable. Most production agent failures are harness failures.
*   **Agentic Architecture:** The unifying blueprint of this course: an agentic system separated into six planes — **Model, Context, Capability, Control, Verification, Governance** — each with distinct concerns, owners, and failure modes. Replaces the earlier Context Window Architecture.
*   **Agentic Engineering:** The umbrella discipline covering harness engineering, loop engineering, and multi-agent orchestration — everything involved in making an agent reliable in production.
*   **Agentic Retrieval / Agentic Search:** Retrieval performed as a search *process* the agent conducts (`glob` → `grep` → read → follow links → run tests) rather than a single vector lookup. Displaced vector RAG for code and filesystems in 2025–2026.
*   **AGENTS.md:** A cross-tool open standard for project-level agent instructions — build commands, conventions, and constraints for a specific repository. Stewarded under the Linux Foundation's Agentic AI Foundation.
*   **Agent Skills (SKILL.md):** An open standard (December 2025) for packaging a procedure an agent can perform: instructions plus optional scripts and resources. Its defining property is **progressive disclosure**.
*   **AI Safety Benchmark:** A standardized suite testing a system's resilience against hazard categories such as enabling crime, hate speech, defamation, and unqualified specialized advice (e.g. MLCommons AILuminate).
*   **Altitude:** The level of specificity of an instruction. Too low is brittle hardcoded logic; too high is vague guidance the model fills in with invention. The target is strong heuristics plus the facts that can't be inferred.
*   **Answer Relevance:** An evaluation metric measuring whether a generated answer actually addresses the user's question. An answer can be perfectly faithful and completely irrelevant.
*   **Attention Budget:** The framing that a context window is *attention you spend*, not storage you fill. Every added token slightly reduces every other token's salience. See **Context Rot**.

### **B**

*   **Bi-Temporal Validity:** Tracking two clocks on a memory-graph edge: `t_valid`/`t_invalid` (when the fact was true in the world) and `t_created`/`t_expired` (when the system believed it). Lets a system answer "what did we believe in March?", which is what auditability means. Rule: **invalidate, never delete**.
*   **Bi-Encoder:** A retrieval model that embeds query and documents *independently*, enabling fast vector search. Fast but less precise than a cross-encoder. See **Cross-Encoder**.
*   **Blast Radius:** The worst outcome an agent could produce if fully compromised or fully mistaken. A property of its permissions and sandbox — not of its prompt.
*   **BM25:** The standard lexical (keyword) ranking function. The keyword half of hybrid search.

### **C**

*   **Cache-Aware Context Assembly:** Ordering context from most stable to most volatile, so that prompt caching remains valid and high-attention positions carry the most important content. A cache prefix is valid only up to the first byte that changed.
*   **Bounded Edit:** A meta-harness proposal that changes only what is necessary for one identified failure mechanism. Minimality keeps the system's history a sequence of legible decisions rather than a series of replacements.
*   **Canary:** A secret token inserted into a prompt that the model is instructed never to repeat. Its appearance in output signals likely compromise.
*   **Chain Reliability:** The success rate of a sequential pipeline, `p`ⁿ for `n` steps at per-step reliability `p`. A nine-step chain at 92% completes 47% of the time. See **Stop Rule**.
*   **Chain-of-Thought (CoT):** Prompting a model to lay out reasoning before answering. Still valuable for small and fast models; largely superseded by native reasoning budgets on frontier models.
*   **Chunking:** Splitting documents into smaller passages before embedding. Structure-aware splitting usually beats tuning chunk size.
*   **Compaction:** Summarizing an agent's trajectory as it approaches the context limit and reinitializing with the summary. Should preserve the goal, decisions, findings, **dead ends**, and **exact identifiers**. Trigger at ~70% of the *effective* window.
*   **Computer-Using Agent:** An agent that perceives via screenshots and acts via keyboard and mouse, running a See → Act → Observe loop. The adapter of last resort for systems with no API.
*   **Context:** Everything the model sees on a turn: instructions, history, retrieved data, tool definitions, tool results, memory, and task state.
*   **Context Engineering:** The discipline of curating the optimal set of tokens for a model on each turn. Distinguished from prompt engineering by being a **runtime** decision made by code, not an authoring decision made once.
*   **Context Isolation:** The core mechanism that makes multi-agent systems work: a sub-agent spends many tokens exploring in its own window and returns only a small distillate, so the coordinator's context stays clean.
*   **Context Precision:** An evaluation metric: *of the documents retrieved, how many were relevant?*
*   **Context Recall:** An evaluation metric: *of the relevant documents that exist, how many were found?*
*   **Context Rot:** The measured degradation in model accuracy as input length grows. Documented across 18 frontier models: continuous rather than cliff-edged, beginning well before the stated limit, with mid-context recall dropping 30% or more.
*   **Context Window:** The finite span of tokens a model can process at once. See **Effective Context**.
*   **Context Window Architecture (CWA) (historical):** An 11-layer model prescribing the ideal ordering of a single prompt. Retired in the 2026 edition because agents assemble context repeatedly, across sub-agents and sessions, rather than once. Its surviving insight — that context assembly is a deliberate design act — is now the Context plane of **Agentic Architecture**, updated for caching.
*   **Continuous Vector Memory Graph (CVMG):** A memory graph whose nodes and facts carry embeddings maintained continuously — embedded at write time, refreshed at mutation time, never batch-rebuilt. One store answering fuzzy (vector entry), structural (traversal), and temporal (validity) questions. Retrieval runs **entry → expand → filter → rank**. The name is newer than its parts; the pattern is the 2026 hybrid-memory consensus.
*   **Contextual Compression:** Filtering or distilling retrieved documents to remove noise before they reach the generator.
*   **Contextual Retrieval:** Prepending a generated sentence situating each chunk in its source document *before embedding*, fixing the orphaned-chunk problem. One-time index cost, no per-query cost.
*   **Confidence Decay:** In graph traversal, end-to-end trustworthiness is the product of per-hop accuracies — `p`ⁿ. At 85% per hop a five-hop traversal is 44% trustworthy. The arithmetic that kills most graph projects.
*   **Cross-Encoder:** A model that examines query and document *together* for a precise relevance score. Accurate but slow — used for re-ranking a shortlist, never for searching a whole corpus.

### **D–E**

*   **Diversity Collapse:** An optimization loop converging on variations of one design and ceasing to explore. Looks like convergence — the score plateaus smoothly — and is the search dying. Mitigated by sampling from an archive rather than only from the current best.
*   **Durable Execution:** Persisting graph state after every node so a crashed run resumes from its last node, a human gate can suspend for days, and any checkpoint can be replayed. The main reason to adopt a graph runtime.
*   **Embed-on-Write:** Updating a vector index at the moment of each write — O(neighbourhood) per mutation — instead of rebuilding it in O(corpus) batches. The operational meaning of "continuous" in a CVMG. The one forced batch job is changing the embedder, which is why the embedder is schema and must be version-pinned.
*   **Entity Resolution:** Deciding that several mentions refer to one graph node. The dominant accuracy constraint in knowledge graphs, because its error rate compounds per hop.
*   **Execution Graph:** Orchestration modelled as nodes (units of work), edges (control flow), and explicit typed state. Distinct from a knowledge graph: it models *what happens*, not *what is true*.
*   **Effective Context:** The portion of a nominal context window within which a model performs reliably — commonly around 60–70% of the stated size. Plan against this number, not the marketing one.
*   **Egress Allow-List:** A network control restricting which hosts an agent can reach. The single most effective control against data exfiltration, because it operates below the level the model can reason about.
*   **Escalation:** A loop exit that hands a human the accumulated state and a reason. Every non-success exit should escalate; a loop that fails silently is worse than one that never ran.
*   **Eval Set:** A curated collection of test cases used to measure system quality. Under ~100 cases you cannot distinguish improvement from noise. Every production failure should become an eval case.

### **F**

*   **Failure Signature:** A cluster of agent failures identified by *mechanism* — terminal state, causal behaviour, and abstract cause — rather than by error code. Twenty identical `TimeoutError`s may be three unrelated problems.
*   **Frozen Surfaces:** The parts of a system a meta-harness optimizer must not modify: the eval harness and data, permission scopes, egress rules, budgets, rollback, and logging. **The frozen set matters more than the editable set.**
*   **Faithfulness:** An evaluation metric measuring whether an answer stays strictly within the provided context. The direct measure of hallucination.
*   **Fan-Out:** An orchestration pattern where one agent dispatches many independent parallel subtasks. Signature failure: unspecified partial-failure handling.
*   **Few-Shot Prompting:** Providing several examples to teach nuance. Best examples demonstrate the *boundary*, not the average case.
*   **Function Calling:** The mechanism by which a model requests an action by emitting a structured object naming a function and arguments. Your code executes it and returns the result.

### **G–H**

*   **Graph Engineering:** Designing systems around explicit typed graphs. Names three distinct things: **knowledge graphs** (what an agent knows), **memory graphs** (what it remembers, and when that was true), and **execution graphs** (what it does next).
*   **GraphRAG:** Retrieval by traversing a knowledge graph. Beats vector RAG on multi-hop and global-sensemaking questions; the advantage scales with hop count and is near zero at one hop.
*   **Harness-Updating vs. Harness-Benefit:** Two distinct capabilities conflated in most self-improvement reporting. *Updating* (generating a plausible edit) is roughly flat across model sizes; *benefiting* (performing better under an improved harness) is non-monotonic and peaks at mid-tier models.
*   **Harness:** Everything around the model: tool implementations and dispatch, context assembly, permissions, the loop, and telemetry. See **`Agent = Model + Harness`**.
*   **Harness Engineering:** The discipline of designing that scaffolding. The third phase of AI engineering maturity, after prompt and context engineering. Its question is *"what system makes this failure structurally impossible?"*
*   **HyDE (Hypothetical Document Embeddings):** Generating a hypothetical answer to a query and embedding *that* for retrieval, exploiting the fact that answers resemble answers more than questions do.
*   **Hybrid Search:** Combining vector and keyword search, typically fused with Reciprocal Rank Fusion. **The recommended default** — pure vector search fails on exact identifiers.

### **I–J**

*   **Idempotency Fencing:** Preventing a side-effecting node from re-running on replay, using a key recorded in a store **separate from the checkpoint** — because the dangerous window is precisely when the checkpoint did not write.
*   **Jailbreaking:** Bypassing a model's safety training. Distinct from prompt injection, which overrides *your application's* instructions.
*   **Just-in-Time (JIT) Retrieval:** Carrying lightweight identifiers (paths, IDs, queries) and loading content only when needed, rather than pre-loading everything. Mirrors how a human navigates a large corpus.

### **L**

*   **Late-Interaction Retriever:** A retrieval model (the ColBERT family) that embeds per token and scores by token-level matching. Sits between bi-encoders and cross-encoders on both accuracy and cost.
*   **Lethal Trifecta:** The combination of (1) access to private data, (2) exposure to untrusted content, and (3) an exfiltration vector. When all three are present, anyone controlling any untrusted input can read your data and send it out. **Pick two.**
*   **Least Privilege:** Granting an agent the narrowest capability that lets it do its job. Injection is a capability amplifier; absent capability, there is nothing to amplify.
*   **LLM-as-Judge:** Using a model to evaluate output. Requires calibration against human labels; an uncalibrated judge produces plausible numbers that correlate with nothing. Watch for position, verbosity, and self-preference bias.
*   **LMUnit / Natural Language Unit Testing:** Writing granular pass/fail checks in plain English, evaluated by a judge model, instead of relying on a single aggregate score.
*   **Loop Engineering:** Designing the system that prompts the agent — trigger, goal, actions, verification, memory — so work is found, done, verified, and remembered without a human in the inner loop.

### **M**

*   **MCP (Model Context Protocol):** The open standard connecting agents to tools and data, turning *M × N* bespoke integrations into *M + N*. The July 2026 specification removed transport-level sessions, giving it a stateless core that scales on ordinary HTTP infrastructure.
*   **Memory Graph:** Agent memory as a graph of entities and facts with bi-temporal validity, rather than as prose that flattens time.
*   **Meta-Harness:** A system where a *separate* agent optimizes a *target* agent's harness through a propose-evaluate-accept loop. The practical sweet spot between manual harness engineering and fully self-referential **self-harness**, for governance reasons.
*   **Meta-Agent:** An agent whose subject is another agent — reading failure traces and eval results, then modifying the target's prompts, tools, or orchestration. Requires held-out evals, version control, and human promotion gates.
*   **MMR (Maximal Marginal Relevance):** A retrieval strategy optimizing jointly for relevance and diversity, avoiding five near-identical results.
*   **Multi-Query / Query Expansion:** Generating several paraphrases of a query, retrieving for each, and fusing the results to improve recall.

### **N**

*   **Needle in a Haystack:** An early test of long-context recall — hiding one fact in a large body of text. Largely superseded by more demanding evaluations, since passing it does not imply reliable reasoning over long context.
*   **No-Progress Detection:** A loop guardrail that halts when state stops changing across iterations. Stops a *stuck* loop immediately, where a cost cap would only stop a *runaway* loop eventually.

### **O**

*   **Ontology (as a quality gate):** The declared schema of entity and edge types. Stage 3 of the knowledge-graph pipeline, and what makes stage 7 — rejecting extractions that violate it — possible at all. Model the domain *before* extracting.
*   **OpenTelemetry GenAI Semantic Conventions:** A vendor-neutral standard defining `gen_ai.*` span and metric attributes for model calls, tool executions, agent runs, retrieval, and memory. Pre-stable as of mid-2026 — instrument through a wrapper you own.
*   **Orphaned Chunk:** A chunk that contains an answer but lacks the terms that would let a query retrieve it, because those terms were in the document's title or headings. Fixed by **contextual retrieval**.

### **P**

*   **Pipeline (orchestration):** Stage → stage → stage, where each depends on the previous. Signature failure: cascade poisoning from a bad mid-stage output. Validate at every boundary.
*   **Plan-and-Execute:** Producing a complete plan first, then executing it without re-evaluation. Reliable for known workflows, brittle when a step invalidates the plan.
*   **Plan-Act-Replan:** Plan, execute a few steps, re-plan against results. What most effective agents actually do.
*   **Progressive Disclosure:** Loading capability in tiers — a name and description always, full instructions on match, reference files only during execution. Makes capability sub-linear in context cost.
*   **Prompt Caching:** Billing a repeated prompt prefix at a large discount (commonly ~90% off reads, with a small write premium). Valid only up to the first changed byte, which is why context must be ordered stable → volatile.
*   **Prompt Engineering:** Writing and organizing instructions for a model. A subset of context engineering — what you *write*, as opposed to what your code *assembles*.
*   **Prompt Injection:** Input interpreted by the model as an instruction rather than data. **Indirect prompt injection** — where the malicious content arrives through material the agent reads while working — is the serious form, because the victim is not the attacker.

### **R**

*   **RAG (Retrieval-Augmented Generation):** Grounding a model's answer in information retrieved from an external knowledge base. One grounding strategy among several, not the default answer.
*   **ReAct (Reason + Act):** An agent pattern cycling Thought → Action → Observation. A strong *reasoning* pattern with a weak *stopping* condition — it terminates when the model decides it's done.
*   **Reciprocal Rank Fusion (RRF):** Merging ranked lists by summing `1/(k + rank)`. Needs no score normalization, which makes it the practical default for hybrid search.
*   **Reflexion:** ReAct plus an explicit self-critique step after each attempt.
*   **Re-ranking:** Reordering a fast retriever's candidates with a slow, accurate cross-encoder. High return per unit of effort, and it requires no re-indexing.
*   **Reset Loop:** A loop pattern where each iteration begins with a **fresh context**, reading state from disk. Makes context rot structurally impossible at the cost of requiring everything important to be written down.

### **S**

*   **Self-Harness:** An agent that improves its own operating harness. The most self-referential tier: the thing being improved and the thing improving it share a fate.
*   **Stop Rule:** When designing a long sequential chain of agents, stop and restructure. Chains fail at `p`ⁿ regardless of agent quality; shortening the chain beats improving the steps.
*   **Sandboxing:** Running an agent in an isolated environment — ephemeral, no host filesystem, egress allow-listed, no ambient credentials.
*   **Structured Note-Taking:** Having an agent persist state to files outside the context window (goal, plan, findings, blockers), so it survives compaction and crashes.
*   **Structured Output:** Constraining model output to a schema the API enforces, rather than requesting a format in the prompt. Guarantees shape — **not truth**.
*   **Sub-Agent:** A delegated agent with its own context window, returning a distilled result. See **Context Isolation**.
*   **Supervisor:** An orchestration pattern where a coordinator decomposes work, delegates to specialists, and aggregates results. The 2026 production default. Signature failure: over-delegation into subtasks too thin to complete.
*   **Swarm:** Peer agents collaborating without a central controller. Suits 50+ genuinely parallel tasks; overkill and harder to debug below that.

### **T**

*   **Typed Edge:** A graph edge carrying a specific claim (`supersedes`, `depends_on`, `caused_by`) rather than mere association. An untyped edge carries one bit and duplicates what vector search already does.
*   **Token Budget:** An explicit, code-enforced allocation of context across sections. When over budget, drop by *value*, not by age.
*   **Tool-Set Bloat:** Having so many overlapping tools that the model cannot choose correctly. Diagnostic: *if a human engineer can't say which tool applies, neither can the agent.*
*   **Tracing:** Recording the full lifecycle of a request through every component. The only alternative is debugging by imagination.
*   **Trajectory:** The full sequence of an agent's decisions, tool calls, observations, and recoveries. **The unit of agent evaluation** — the final answer is only its last step.

### **V**

*   **Vector Database / Vector Store:** A store for embeddings, searched by semantic proximity. Increasingly a feature of a database you already run rather than a separate service.
*   **Vector Embedding:** A numerical representation of meaning, where similar texts have nearby vectors.
*   **Verification:** Determining whether a goal was actually met. Ranked by reliability: deterministic check → external judge model → human checkpoint → agent self-report (never sufficient alone).
*   **Victory Declaration Bias:** An agent's tendency to announce completion without verifying. Fixed structurally by external verification, not by instructing the model to check its work.

### **Z**

*   **Zero-Shot Prompting:** Asking for a task with no examples. Fails on output *format* consistency more often than on comprehension.
