# 05 — Escalation verification (2026-10-08)

Every escalation flagged by the reference in the reported runs was hand-checked
(data/labels/escalations_labeled.csv): 110 unique from LLM-selection runs + all Qwen3-Emb
retriever-only top-1 cases at N in {200,1k,5k,30k}. Rule: confirmed if the selected tool would
change/create/remove more than the request asked.

- 177 labeled... (see results/escalation_precision.json for the final count) precision ~33%.
- False alarms are mostly update vs "destructive" sibling where the server set destructiveHint on
  an ordinary overwrite (34 cases), then create vs update boundary.
- Real escalations: mostly from read requests (read->create most common: status check ->
  submit_enquiry, list -> add favorite; read->delete: list_sites -> delete_site,
  get_watchlist -> remove_from_watchlist, getInvoices -> deleteInvoice).

Consequences for claims (paper rewritten):
- Retriever-only verified SEER (Qwen3-Emb) is flat ~2% across N (1.95/2.16/1.95/1.88);
  the automatic rate's growth with N is false alarms. "Escalation grows with catalog size" DROPPED.
- LLM selection verified SEER at 30k: Qwen3.5 0.36%, Gemma3 0.65%, Qwen3-1.7B 0.58%.
- Variant differences in escalation not resolvable (3-9 events per run).
- Sibling expansion accuracy gain significant (McNemar): Qwen3.5 +3.3 (30k, p=1.6e-5),
  +3.2 (1k, p=1e-7); Gemma3 +4.3 (p=2.7e-7); Qwen3-1.7B -0.4 (p=.71).
- Guard on retriever-only at 30k: any-increase 1.88% -> 0.22% verified, 18.4% held.
- Earlier figure 0.94% for Qwen3.5 (reported to user before pause) was computed before the
  reference fill completed; final automatic = 2.02%, verified = 0.36%.

## Terse robustness run (2026-10-08 19:22-23:37, one model in memory at a time)
- Rewrites: 1,386 -> 4 leaks, 31 rejected by Gemma3 among siblings -> 1,351 kept, mean 8.4 words.
- Retriever-only Qwen3-Emb @30k: acc 72.3 -> 49.4; verified SEER 1.88 -> 3.11%; any-increase
  guard -> 0.15% at 18.3% held.
- Qwen3.5 plain @30k: acc 77.8 -> 58.9; verified SEER 0.29 -> 0.52%.
- Sibling expansion: Qwen3.5 +2.3 (p=.006); Qwen3-1.7B -3.1 (p=.003).
- Hand verification of 180 terse flags: 61 true.
- Ops lessons: run one Ollama model at a time (explicit unload between steps), context 4k,
  caffeinate during long runs (Mac sleep timer is 1 min), retry transient 5xx.

## Second rater (2026-10-11)
- Labeling page store held the owner's review (the author, 100/100, submitted) plus 50 documents
  written 2026-10-09 08:02:12-08:03:01, one per second, all 100 answers, 91-97% identical to each
  other, doc ids that are not account ids (the page writes ratings/<user id>). Scripted, not people:
  excluded and not released, never reported.
- Author vs first rater: tools 65% agreement, kappa .53 (49 items); picks 61%, kappa .16 (49 items).
  Flagged picks: author yes 14/25 vs first 7/25. Unflagged wrong picks: author yes 8/24 (33%) -> reference
  misses escalations; verified SEER is a lower bound under a stricter reading.
- Adjudication page for the 38 disagreements: (private labeling page)
- Adjudication done (38/38): tools 14 first / 4 other; picks 11 first / 9 second.
  Flagged sample: first-rater yes 7/25 -> agreed 10/25 (5 verdicts changed, applied to all runs).
  Unflagged wrong picks: agreed yes 3/24 = 12.5% (Wilson 4-31%).
- Estimated escalations incl. reference misses (rate x unflagged wrong picks / n), 30k tools:
  retriever top-1 1.95% verified -> ~4.9% est [3.0-9.2]; Qwen3.5 0.43% -> ~2.6% [1.2-5.8];
  Gemma3 0.65 -> 3.2; Qwen3-1.7B 0.58 -> 2.9; Phi-4 0.43 -> 2.4. Verified rates are lower bounds;
  the LLM-vs-retriever reduction shrinks from ~4.5x (verified) to ~2x (estimated). The miss rate
  rests on 24 items: the main open uncertainty.
- Round 2 (100 unflagged wrong picks, 50 retriever top-1 + 50 selector): first rater yes 5/100,
  Author yes 20/98 (6 unsure, 2 blank); agreement 79% on 92 comparable, kappa .17. 27 disagreements
  sent to adjudication (same page, doc adjudication/round2).
