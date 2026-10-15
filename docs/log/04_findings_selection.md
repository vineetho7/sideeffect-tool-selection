# 04 — End-to-end selection findings (2026-10-06 06:40), Qwen3.5-9B selector, Qwen3-Emb top-5

| variant | N | acc | SEER | exec SEER (read_or_destructive guard) | held | in shortlist |
|---|---|---|---|---|---|---|
| plain | 1k | 89.8 | 0.22 | 0.07 | 10.5 | 96.8 |
| native | 1k | 90.3 | 0.22 | 0.07 | 10.3 | 96.8 |
| tags | 1k | 90.8 | 0.22 | 0.07 | 10.3 | 96.8 |
| sibling | 1k | 93.0 | 0.07 | 0.00 | 10.6 | 98.8 |
| plain | 30k | 72.2 | 0.94 | 0.43 | 10.4 | 90.0 |
| native | 30k | 72.8 | 0.94 | 0.43 | 10.1 | 90.0 |
| tags | 30k | 72.6 | 0.94 | 0.43 | 10.7 | 90.0 |
| sibling | 30k | 75.5 | 0.65 | 0.29 | 10.8 | 92.5 |

Observations
- A 9B selector removes most retrieval-level escalation (Qwen3-Emb top-1 SEER 3.5% at 1k, 4.8% at 30k
  -> 0.22% / 0.94% after selection) but not all, and escalation grows ~4x with catalog size.
- Native annotations and inferred tags change nothing measurable: the selector already reads
  the verb in the name. The side-effect info is not what it lacks.
- Sibling expansion is the one selection change that helps: +3 points accuracy, -30% SEER,
  because it puts the right sibling into the shortlist (in-shortlist 90.0 -> 92.5 at 30k).
- At 30k most errors are not siblings (1.5-2.6% of errors): they are the same function on another
  server (many near-identical public tools). "Accuracy" by server identity understates usefulness.
- Guard cost is dominated by intent/profile boundary disagreements (create vs update, update vs
  destructiveHint-on-overwrite, preview-mode cancel tools), not by real escalations.
