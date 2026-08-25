# **References**

Primary sources behind the 2026 material in this course. Grouped by the module they most support. Web sources were consulted in August 2026; where a specification or benchmark is versioned, the version is noted, because several of these are still moving.

---

## **Context Engineering (Modules 1, 4)**

*   Anthropic — [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents). The attention-budget framing, system-prompt altitude, and the four long-horizon techniques: compaction, structured note-taking, sub-agent architectures, just-in-time retrieval.
*   Anthropic — [Context engineering: memory, compaction, and tool clearing](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools). Worked implementations.
*   Chroma Research — *Context Rot: How Increasing Input Tokens Impacts LLM Performance*. The 18-model study behind the degradation figures. Summarized at [morphllm.com/context-rot](https://www.morphllm.com/context-rot).
*   [Diagnosing and Mitigating Context Rot in Long-horizon Search](https://arxiv.org/pdf/2606.29718) (arXiv 2606.29718).
*   [LCM: Lossless Context Management](https://arxiv.org/pdf/2605.04050) (arXiv 2605.04050).
*   Truefoundry — [Just-in-Time Context for AI Agents: A Runtime Discipline](https://www.truefoundry.com/blog/jit-context-just-in-time-context-agents).
*   Sourcegraph — [Context Engineering: A Practical Guide for AI Agents (2026)](https://sourcegraph.com/blog/context-engineering).

## **Retrieval (Module 3)**

*   [Is Grep All You Need? How Agent Harnesses Reshape Agentic Search](https://arxiv.org/abs/2605.15184) (arXiv 2605.15184). Grep vs. vector retrieval across four harnesses; the finding that harness design outweighed retrieval algorithm.
*   [The 2026 Shift: Moving Beyond Vector RAG to Agentic Retrieval Workflows](https://sesamedisk.com/direct-corpus-interaction-ai-retrieval/).
*   [RAG Is Not Always the Answer Anymore: How AI Agents Search Code in 2026](https://dev.to/nimay_04/rag-is-not-always-the-answer-anymore-how-ai-agents-search-code-in-2026-43m3).
*   Glasp — [Context Rot, RAG, and Long Context: How to Architect LLM Systems in 2026](https://glasp.co/articles/context-rot-rag-long-context-hybrid).

## **Tools, MCP, and Skills (Module 5)**

*   Model Context Protocol — [The 2026-07-28 Specification](https://blog.modelcontextprotocol.io/posts/2026-07-28/). The stateless protocol core, multi-round-trip requests, cacheable list results, extensions framework.
*   Model Context Protocol — [The 2026 MCP Roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/).
*   The Register — [Model Context Protocol prepares to break with its stateful past](https://www.theregister.com/devops/2026/07/23/model-context-protocol-prepares-to-break-with-its-stateful-past/5276722).
*   Firecrawl — [Agent Skills Explained: How SKILL.md Files Work](https://www.firecrawl.dev/blog/agent-skills).
*   SwirlAI — [Agent Skills: Progressive Disclosure as a System Design Pattern](https://www.newsletter.swirlai.com/p/agent-skills-progressive-disclosure).
*   Agentman — [The Agent Skills Ecosystem in 2026](https://agentman.ai/blog/agent-skills-ecosystem-report-2026).
*   Red Hat Developer — [Standardize project context with AGENTS.md and Agent Skills](https://developers.redhat.com/articles/2026/07/27/standardize-project-context-agentsmd-and-agent-skills).
*   Morph — [AGENTS.md Spec (2026): Recommended Sections](https://www.morphllm.com/agents-md-guide).

## **Evaluation and Observability (Module 6)**

*   Confident AI — [LLM Agent Evaluation Metrics in 2026: Tool Calling, Task Completion, Reasoning, and Trace-Based Evals](https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide).
*   Judgment Labs — [Agent Judge: Long-Horizon Evals for Production Agents](https://www.judgmentlabs.ai/blogs/agent-judge-solving-long-context-evaluations). Why LLM judges break down on long trajectories and stateful changes.
*   Zylos Research — [LLM-as-Judge Patterns for Agent Evaluation: Calibration, Bias, and Trajectory Assessment](https://zylos.ai/research/2026-05-26-llm-as-judge-agent-evaluation-patterns/).
*   Galileo — [How to Build an Agent Evaluation Framework With Metrics, Rubrics, and Benchmarks](https://galileo.ai/blog/agent-evaluation-framework-metrics-rubrics-benchmarks).
*   [OpenTelemetry GenAI Semantic Conventions Implementation Guide](https://hidekazu-konishi.com/entry/opentelemetry_genai_semantic_conventions_guide.html). Note: pre-stable as of the v1.42.0 release (June 2026).
*   Uptrace — [OpenTelemetry for AI Systems: LLM and Agent Observability (2026)](https://uptrace.dev/blog/opentelemetry-ai-systems).

## **Security (Module 6, Lesson 3)**

*   Airia — [AI Security in 2026: Prompt Injection, the Lethal Trifecta, and How to Defend](https://airia.com/blog/ai-security-in-2026-prompt-injection-the-lethal-trifecta-and-how-to-defend/).
*   Sophos — [Inside the lethal trifecta: Blast radius reduction in AI agent deployments](https://www.sophos.com/en-us/blog/inside-the-lethal-trifecta-blast-radius-reduction-in-ai-agent-deployments).
*   The Bright Byte — [The Lethal Trifecta: A 2026 Defence Architecture for AI Agents](https://thebrightbyte.com/playbook/expertise/lethal-trifecta-ai-agent-defense-architecture-2026).
*   Sysdig — [The Comprehensive Guide to Prompt Injection Attacks in 2026](https://www.sysdig.com/learn-cloud-native/prompt-injection).
*   MLCommons — AILuminate safety benchmark.

## **Harness and Loop Engineering (Module 8, Lessons 1–2)**

*   [Harness Engineering for Agentic AI Coding Tools: An Exploratory Study](https://arxiv.org/pdf/2602.14690) (arXiv 2602.14690).
*   [Code as Agent Harness](https://arxiv.org/pdf/2605.18747) (arXiv 2605.18747).
*   Faros AI — [Harness Engineering: Making AI Coding Agents Work in 2026](https://www.faros.ai/blog/harness-engineering). The `Agent = Model + Harness` formula, the five harness layers, and the three failure modes.
*   Augment Code — [Harness Engineering for AI Coding Agents: Constraints That Ship Reliable Code](https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents).
*   [awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering). Taxonomy of harness design primitives.
*   Data Science Dojo — [Agentic loops explained: From ReAct to loop engineering](https://datasciencedojo.com/blog/agentic-loops-explained-from-react-to-loop-engineering-2026-guide/).
*   explainX — [What Is Loop Engineering? Beyond Prompt Engineering in 2026](https://explainx.ai/blog/what-is-loop-engineering-ai-agents-2026). The five loop components; the Boris Cherny quote.
*   eesel AI — [Loop engineering explained: designing AI agent loops in 2026](https://www.eesel.ai/blog/loop-engineering).
*   [Building Effective AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned](https://arxiv.org/pdf/2603.05344) (arXiv 2603.05344).

## **Multi-Agent Systems and Team Structure (Module 8, Lesson 3)**

*   Digital Applied — [Multi-Agent Orchestration: 5 Patterns That Work in 2026](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work). The fan-out / pipeline / debate / supervisor / swarm taxonomy, with costs and failure modes.
*   Beam AI — [6 Multi-Agent Orchestration Patterns for Production (2026)](https://beam.ai/agentic-insights/multi-agent-orchestration-patterns-production).
*   Atlan — [How to Orchestrate Multi-Agent AI Systems at Scale in 2026](https://atlan.com/know/multi-agent-system-orchestration/).
*   Augment Code — [Agentic Engineering Operating Model: Teams + Agents](https://www.augmentcode.com/guides/agentic-engineering-operating-model).
*   Optimum Partners — [Engineering Management 2026: Structuring an AI-Native Team](https://optimumpartners.com/insight/engineering-management-2026-how-to-structure-an-ai-native-team/).
*   [Meta-Agent: From Task Descriptions to Verified Multi-Agent Systems](https://arxiv.org/pdf/2605.25233) (arXiv 2605.25233).

## **The Frontier (Module 7)**

*   Linux Foundation — [A2A Protocol Surpasses 150 Organizations, Lands in Major Cloud Platforms](https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year). v1.0 under Linux Foundation governance, April 2026.
*   Zylos Research — [Agent Interoperability Protocols 2026: MCP, A2A, ACP and the Path to Convergence](https://zylos.ai/research/2026-03-26-agent-interoperability-protocols-mcp-a2a-acp-convergence/).
*   Morph — [LLM Context Window Comparison (2026)](https://www.morphllm.com/llm-context-window-comparison). Context sizes and per-window pricing across the current field.
*   [Managing Agents that Manage Agents: Workshop on Responsible Use of Meta-Agents (NeurIPS 2026)](https://meta-agents-workshop.github.io/).
*   Galileo — [The 2026 Caching Playbook for Agents](https://galileo.ai/blog/the-2026-caching-playbook-for-agents-bigger-prompts-smaller-bills).
*   Digital Applied — [Prompt Caching Economics: Cache-First Agent Design](https://www.digitalapplied.com/blog/prompt-caching-economics-cache-first-agent-architecture-2026).
*   Mem0 — [AI Agent Memory 2026: Progress Benchmark Report](https://mem0.ai/blog/state-of-ai-agent-memory-2026).

## **Graph Engineering (Module 9, Lessons 1–3)**

*   The AI Operator — [What Is Graph Engineering? A Field Guide for Builders](https://theaioperator.io/p/what-is-graph-engineering-a-field). The three-graph distinction, typed edges, and the entity-resolution compounding argument.
*   Wavect — [Graph Engineering for AI Agents: When the Graph Earns Its Cost](https://wavect.io/blog/graph-engineering-ai-agents/). The five conditions justifying a graph, the hidden costs beyond the database licence, and the kill rule.
*   [graph-engineering](https://github.com/codejunkie99/graph-engineering). The nine-stage knowledge-graph pipeline and the task-graph patterns (delete fake edges, the diamond, the stop rule, the human gate).
*   Neo4j — [Agentic GraphRAG: Autonomous Knowledge Graph Construction and Adaptive Retrieval](https://neo4j.com/videos/nodes-ai-2026-agentic-graphrag-autonomous-knowledge-graph-construction-and-adaptive-retrieval-2/). Schema inference and routing between vector search and graph traversal.
*   TianPan — [GraphRAG vs. Vector RAG: The Architecture Decision Teams Make Too Late](https://tianpan.co/blog/2026-04-19-graphrag-vs-vector-rag-architecture-decision).
*   Atlan — [Knowledge Graph vs RAG: When Each One Wins (2026)](https://atlan.com/know/knowledge-graphs-vs-rag-for-ai/).
*   Sowmith Mandadi — [GraphRAG Looks Great Until Entity Resolution Breaks](https://www.sowmith.dev/blog/graphrag-entity-disambiguation). Source of the per-hop compounding figures.
*   [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/abs/2501.13956) (arXiv 2501.13956), and Neo4j's [Graphiti](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/). The bi-temporal model and its four timestamps; the episodes / facts / communities layering.
*   [Control-Plane Placement Shapes Forgetting: An Architectural Study of Agent Memory Across Thirteen System Configurations](https://arxiv.org/abs/2606.15903) (arXiv 2606.15903). Thirteen configurations over 385 adversarial cases; the mutation-time hook result.
*   [Calibrated Fusion for Heterogeneous Graph-Vector Retrieval in Multi-Hop QA](https://arxiv.org/pdf/2603.28886) (arXiv 2603.28886).
*   Mastra — [LangGraph: a guide to stateful AI agent orchestration](https://mastra.ai/articles/langgraph), and [AI Workflow Orchestration in Production](https://aiworkflowlab.dev/article/ai-workflow-orchestration-in-production-building-durable-agent-pipelines-with-langgraph-and-temporal). Checkpointing and durable execution.

## **Continuous Vector Memory Graphs (Module 9, Lesson 3)**

*   Mem0 — [AI Agent Memory 2026: Progress Benchmark Report](https://mem0.ai/blog/state-of-ai-agent-memory-2026) and [Graph-Based Memory Solutions for AI Context: Top 5 Compared](https://mem0.ai/blog/graph-memory-solutions-ai-agents). The hybrid-consensus framing and the LongMemEval comparisons (~64% temporal-graph memory vs ~49% flat vector memory — directional).
*   SandBase — [Agent Memory Architectures: Vector, Graph & Episodic](https://blog.sandbase.ai/agent-memory-architectures-compared-2026/), and Digital Applied — [AI Agent Memory 2026: Vector, Graph, Episodic](https://www.digitalapplied.com/blog/ai-agent-memory-vector-graph-episodic-2026). "Vector + graph + episodic buffer" as the production default; the ~200–400 ms graph-lookup latency figure.
*   [HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models](https://arxiv.org/abs/2405.14831) (NeurIPS 2024). Vector-seeded entry into an open knowledge graph, expanded via Personalized PageRank — the entry-then-traverse pattern formalized.
*   Zep/Graphiti (see the Graph Engineering section above) — the reference continuous, incremental temporal-graph memory with hybrid semantic + keyword + graph search.
*   FalkorDB — [Graph Database AI Agents: GraphRAG & Memory Guide](https://www.falkordb.com/blog/graph-database-ai-agents/), and Knowlee — [Persistent Memory for AI Agents: Graph vs Vector vs Hybrid](https://www.knowlee.ai/blog/persistent-memory-for-ai-agents). Entry-point traversal mechanics.
*   [GAAMA: Graph Augmented Associative Memory for Agents](https://arxiv.org/pdf/2603.27910) (arXiv 2603.27910) and [Memanto: Typed Semantic Memory with Information-Theoretic Retrieval](https://arxiv.org/pdf/2604.22085) (arXiv 2604.22085).

**A naming caution:** "continuous vector memory graph" is a descriptive label for this pattern, not yet a term with a canonical definition. The pattern — one store, embeddings on graph elements, incremental updates, vector entry + structural expansion + temporal filtering — is what the sources above converge on; cite the pattern, not the phrase.

## **Autonomous Meta-Harness Systems (Module 9, Lessons 4–5)**

*   Lilian Weng — [Harness Engineering for Self-Improvement](https://lilianweng.github.io/posts/2026-07-04-harness/). **The best single source on this topic.** The three-tier taxonomy, the optimization ladder, the seven challenges, and the failure patterns.
*   [Meta-Harness: End-to-End Optimization of Model Harnesses](https://www.emergentmind.com/papers/2603.28052) (arXiv 2603.28052). The agentic outer loop over harness code, filesystem access to prior candidates, Pareto optimization over accuracy and context cost, and the reported results.
*   [Self-Harness: Harnesses That Improve Themselves](https://arxiv.org/html/2606.09498v1) (arXiv 2606.09498). Weakness mining with verifier-grounded failure signatures, bounded edits, held-in/held-out acceptance, and the model-specific harness result.
*   **[Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents](https://arxiv.org/pdf/2605.30621)** (arXiv 2605.30621). The central critique of Lesson 5, and the updating-vs-benefit distinction.
*   [SEAGym: An Evaluation Environment for Self-Evolving LLM Agents](https://arxiv.org/pdf/2606.17546) (arXiv 2606.17546). Catastrophic forgetting, task interference, and why static benchmarks cannot evaluate an evolving agent.
*   [Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents](https://arxiv.org/abs/2505.22954) (ICLR 2026). The archive-based evolutionary approach, and the finding that discovered improvements transfer across foundation models.
*   [Safety in Self-Evolving LLM Agent Systems: Threats, Amplification, and Case Studies](https://arxiv.org/pdf/2606.23075) (arXiv 2606.23075).
*   [From Question Answering to Task Completion: A Survey on Agent System and Harness Design](https://arxiv.org/pdf/2606.20683) (arXiv 2606.20683).
*   [A Survey of Self-Evolving Agents: What, When, How, and Where to Evolve](https://arxiv.org/pdf/2507.21046) (arXiv 2507.21046).
*   Ben Dickson — [A primer on self-improving agent harnesses](https://bdtechtalks.substack.com/p/a-primer-on-self-improving-agent).

---

## **A Note on Reading These**

Much of the 2026 agent literature is vendor content, and vendor content is directionally useful and quantitatively unreliable. Where this course cites a specific number — the 18-model context-rot study, effective context at 60–70% of nominal, the ~90% cache read discount — it comes from primary research or published API documentation. Where it cites an adoption or failure statistic (*"40% of multi-agent pilots fail within six months"*), treat it as an indication of direction rather than a measurement, and be suspicious of anyone quoting it to three significant figures.

The durable content of these sources is the **mechanisms**, not the figures. Context rot has a cause in transformer attention and training distribution; that will outlast any particular measurement of it.

**Module 9's literature needs extra caution**, in two directions. The GraphRAG comparisons vary enormously by corpus and extraction quality — reported multi-hop gaps range from a few points to fifty, and the robust finding is the *pattern* (advantage scales with hop count, near zero at one hop), not any single number. And the self-improvement results are published by the people who built the systems, evaluated on benchmarks they chose. That is not a criticism of the work; it is exactly why *Harness Updating Is Not Harness Benefit* is on this list, and why Lesson 5 exists at all. Read the positive results and the critique together, in that order.
