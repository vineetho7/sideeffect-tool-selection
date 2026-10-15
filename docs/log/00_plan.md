# 00 — Plan and framing (2026-10-05)

## Target
ICSE 2027 SEIP, deadline 2026-10-23. Single author, independent researcher. No employer data,
no telecom/networking APIs (explicit user constraint).

## How we got here (idea evolution)
1. Started as "HNSW + tool-aware reranker for big tool catalogs". Rejected: flat search over
   10k vectors is ~1 ms, so HNSW buys nothing at tool-catalog scale; tool retrieval/reranking
   already crowded (ToolRerank LREC-COLING'24, ToolRet ACL'25 Findings, Gorilla, RAG-MCP, MCP-Zero,
   ScaleMCP, LiveMCPBench, MCP-Bench, MCPVerse, MCP-Atlas, "Semantic Tool Discovery" 2603.20313).
2. "Tool-aware HNSW" (metadata inside graph traversal). Rejected: no speed problem to solve,
   breaks HNSW's metric assumption, filtered-ANN already exists (Filtered-DiskANN, ACORN).
3. MCP ecosystem mining. Mostly done already: description smells (2602.14878, 2602.18914),
   ecosystem census (2607.25635), registry random draw (2609.10962).
4. **Chosen:** CRUD siblings (get/list/create/update/delete on one resource) collapse in
   embedding space; retrieval/selection errors among them can *escalate side effects*
   (asked to read, agent picks update/delete). Measured with SEER. Fix: severity-aware selection.

## Novelty check (2026-10-05)
No paper found whose central question is side-effect escalation among sibling operations.
MCP has `readOnlyHint`/`destructiveHint`, but 2609.10962 reports 58.8% of tools omit
annotations in a random registry sample -> our RQ3 compares native annotations vs inferred profiles.

## Relation to prior own work
`../ccnc-tool-routing` (CCNC WiP, TM Forum telecom APIs) studied confusable tools generally.
This paper differs: MCP ecosystem, side-effect severity as the outcome, escalation guard as the
intervention, annotation reliability. Cite it; do not reuse its data.

## RQs
- RQ1 How tightly do CRUD siblings cluster in embedding space (vs unrelated tools)?
- RQ2 How often do retrievers / LLM selectors pick a sibling with stronger side effects (SEER)?
- RQ3 Do inferred operation profiles + escalation guard reduce SEER better than native MCP
  annotations, and at what accuracy / latency cost?
- Control: flat vs HNSW; ANN error is not the dominant error source.

## Metrics
Severity: 0 read, 1 create, 2 update, 3 destructive (study-specific taxonomy, manually validated).
- top-1 accuracy (allowing acceptable-set gold)
- SEER = P(sev(selected) > sev(gold))
- mean escalation = E[max(0, sev(sel) - sev(gold))]
- Exposure@k = for read requests, P(any sev>=2 tool in top-k)
- same-resource confusion share among errors
- de-escalation rate (write request -> lower-severity tool): counted as an error, not escalation

## Go / no-go
Sibling groups in harvested MCP corpus: <50 pivot, 50-200 add OpenAPI-derived catalog, 200+ good.

## Local compute
Ollama on M4 Pro 24 GB: qwen3.5 (selector), qwen3:1.7b (small selector / intent),
embedders nomic-embed-text, qwen3-embedding:0.6b, bge-m3.

## Log 2026-10-05 evening
- Registry snapshot: 39,853 latest server entries; 25,009 with remotes; 21,699 public streamable-HTTP
  candidates (no required header). Harvest (initialize + tools/list only): 12,997 responded,
  212,972 raw tools. Failures: 401 x4,666, 429 x1,539, 404 x588 (docs/log/harvest_stats.txt).
- Catalog after dedupe (identical tool sets) + publisher cap 25 servers: 8,554 servers, 107,870 tools,
  6,363 sibling groups, 3,489 escalation-capable (read + update/delete) across 2,495 servers. GO.
- Two mass publishers (pipeworx-io, sadri-dridi) produced ~12k tools of near-identical wrappers ->
  reason for publisher cap.
- Hand audit of 300 tools (stratified by rule class): rule profiler exact 79.6% (kappa .72), read/write 84.9%,
  errs conservative (over 16.5%, under 3.9%). Annotations 95.8% read/write accurate where present,
  present on 64%; 24/57 truly destructive tools have no annotation.
- Embedding throughput is GPU-bound and shared with the LLM; plan a 20k-tool study pool.

## PAUSED 2026-10-06 (user's laptop was hanging)
Main chain (src/run_all.sh) finished 22:32: all qwen3.5, gemma3 and qwen3:1.7b selection runs,
reference fill, final retrieval eval, analyze -> results/summary.json.
NOT run yet: src/run_terse.sh (terse-request robustness add-on). All jobs killed, models unloaded.
Resume checklist:
1. `src/run_terse.sh` (~3h GPU; run when the laptop is otherwise idle).
2. `python src/guard_retrieval.py qwen3.5:latest`, `python src/list_escalations.py`, hand-label
   results/escalations.csv (true_escalation column).
3. `python src/make_numbers.py && python src/make_figs.py`; fill \SELECTORTEXT, \READGUARDSHARE,
   \SIBGAIN in paper/sec_results.tex and sec_abstract.tex; `paper/build.sh`.
4. Reviewer subagent pass over code + paper before calling it done.

## PAUSED 2026-10-09 ~06:10 (user away)
Done since last pause: Wilson CIs, retitle ("Doing More Than Asked"), exploratory wording, release bundle,
pinned deps, MODELS.md, tests + CI, retrieval-vs-selection split, labeling page for reviewers
((private labeling page)), ablation runs (expand 80.7, expandtags 81.1 vs plain
77.8 / sibling 81.0 at 30k, Qwen3.5), Phi-4 14B intents + plain (75.6%).
NOT done: Phi-4 sibling run (stopped at ~300/1386; select_eval saves only at the end, so rerun:
`caffeinate -i src/run_phi4.sh` minus the finished steps, i.e. sibling, references, analyze).
Then: hand-check new escalations (expand, expandtags, phi4), add ablation + Phi-4 to paper, rebuild.
