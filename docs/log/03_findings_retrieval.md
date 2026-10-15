# 03 — Retrieval-level findings (2026-10-06 01:20)

1,386 requests, study pool 30,000 tools, catalogs N in {200, 1k, 5k, 30k}; target's whole server
always installed. Reference severities scored.

## RQ1 geometry
- Raw mean cosine does NOT show siblings closer than other same-server pairs
  (qwen3emb: sibling .561, same-server non-sibling .666, cross-server .552). Mean comparison is
  confounded by which servers contribute samples -> replaced by a nearest-neighbour test.
- Nearest same-server neighbour of a grouped tool is one of its siblings:
  MiniLM 62.8%, BGE 62.0%, Qwen3-Emb 66.1% vs chance 13.2% (12,399 tools; results/rq1_nearest_neighbour.json).
- A sibling outscores the target for the request itself in 8.7% (Qwen3) / 7.1% (BGE) / 15.9% (MiniLM) of requests.

## RQ2 retrieval only (top-1 = what a retriever-only router would execute)
| retriever | N | acc@1 | recall@5 | SEER@1 | read exposed@5 | sibling share of errors |
|---|---|---|---|---|---|---|
| BM25 | 200 / 30k | 81.7 / 68.9 | 96.2 / 83.8 | 5.8 / 5.9 | 58.8 / 49.2 | 40.6 / 15.1 |
| MiniLM | 200 / 30k | 71.9 / 52.8 | 91.9 / 72.7 | 5.3 / 6.3 | 54.0 / 37.9 | 36.2 / 12.2 |
| BGE-base | 200 / 30k | 86.9 / 72.9 | 97.8 / 88.0 | 2.7 / 5.1 | 54.3 / 40.6 | 40.7 / 14.1 |
| Qwen3-Emb | 200 / 30k | 86.4 / 72.3 | 97.8 / 90.0 | 3.2 / 4.8 | 53.1 / 40.7 | 49.2 / 17.2 |
- Escalation persists and grows with catalog size for dense retrievers (3% -> 5%).
- Exposure: 40-59% of read requests carry an update/destructive tool in the top-5 shortlist,
  so the selector must discriminate side effects on roughly every other read request.
- Sibling share of errors falls as N grows: in small catalogs errors are mostly siblings, in large
  ones cross-server distractors dominate. Escalation, though, does not fall.

## Control: HNSW vs exact (30k)
Exact flat search 0.4-0.9 ms/query. HNSW reaches exact top-1 only at ef>=100 (0.4-0.8 ms);
ef=10 is 3-6x faster but loses up to 8 points of top-1. ANN is not where tool selection fails.
