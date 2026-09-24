# Ports (single writer per port, always; see M9)
- 8089 : Ling-class fitness serves (SC117 / ling-abl builds)
- 8090 : Gemma E4B stock baseline serves
- 8091 : Spark fast bench + driver endpoint (32K ctx)
- 8092 : Gemma ablation serves (dose + sign-flip + future)
- 11434: Ollama (embeddings, misc models)
Rule: one server at a time during fitness evals. Evals log `cohabit`
(count of sibling servers up) so contention is visible in rows, not lore.
