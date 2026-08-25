# **Module 9: Graph Engineering and Autonomous Meta-Harness Systems**

This module covers making structure **explicit** — as knowledge graphs, memory graphs, continuous vector memory graphs, and execution graphs — how to actually stand each one up, and then what happens when a system starts modifying that structure itself.

The two halves are connected by one idea: **a system can only safely rewrite what is explicit.** Graphs are how structure becomes inspectable; meta-harness systems are what inspects and edits it. The final lesson is the sceptical one, and the most important: most self-improvement claims do not survive contact with an evaluator the system did not optimize against.

### **Lessons**

*   [**Lesson 1: Graph Engineering — Making Structure Explicit**](./Lesson1_Graph_Engineering.md)
*   [**Lesson 2: Knowledge and Memory Graphs**](./Lesson2_Knowledge_and_Memory_Graphs.md)
*   [**Lesson 3: Continuous Vector Memory Graphs**](./Lesson3_Continuous_Vector_Memory_Graphs.md)
*   [**Lesson 4: Execution Graphs — Orchestration as Structure**](./Lesson4_Execution_Graphs.md)
*   [**Lesson 5: Standing Up the Four Graphs — A Practical Setup Guide**](./Lesson5_Standing_Up_the_Graphs.md)
*   [**Lesson 6: Autonomous Meta-Harness Systems**](./Lesson6_Autonomous_Meta_Harness.md)
*   [**Lesson 7: Governing Systems That Rewrite Themselves**](./Lesson7_Governing_Self_Modifying_Systems.md)

---

### **By the end of this module you will be able to:**

1. Distinguish knowledge, memory, continuous vector memory, and execution graphs — and decide when each earns its cost
2. Design a bi-temporal memory graph and route queries across three retrieval primitives
3. Build a continuous vector memory graph: entry → expand → filter → rank, with invalidation-aware vectors
4. Model an agent workflow as an execution graph with durable execution and human gates
5. Stand up each graph at the right storage rung, expose it as tools, and prove it with drills
6. Build a propose-evaluate-accept loop with a held-out acceptance gate
7. Govern a self-modifying system: frozen surfaces, sandbox, rollback, promotion gate

**Estimated time:** 7–8 hours, including the hands-on tasks.

---

### **Check yourself**

1. At 85% entity resolution, what fraction of a five-hop traversal is trustworthy?  <sub>(Module 9, Lesson 1 §4)</sub>
2. What do the four timestamps of a bi-temporal edge let you answer that a summary cannot?  <sub>(Module 9, Lesson 2 §3)</sub>
3. Why must a superseded fact's embedding be kept and filtered, rather than deleted?  <sub>(Module 9, Lesson 3 §4)</sub>
4. Why do long sequential agent chains fail regardless of agent quality?  <sub>(Module 9, Lesson 4 §3)</sub>
5. What is the one integration contract that joins all four graphs, and what breaks without it?  <sub>(Module 9, Lesson 5 §5)</sub>
6. Why must the acceptance gate use data the proposer never sees — and how big must a gain be to mean anything?  <sub>(Module 9, Lesson 6 §3)</sub>
7. Name three things that must be in the frozen set, and what each prevents.  <sub>(Module 9, Lesson 7 §3)</sub>
