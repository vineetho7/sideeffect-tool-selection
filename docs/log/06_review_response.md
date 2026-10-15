# Response to external review (7.5/10, Oct 12)

Venue: staying with ICSE 2027 SEIP (paper Oct 23).

| Review item | Decision | Status |
|---|---|---|
| "Hand-verified" overstates the labels | Adopt: the author labels all 178 flagged escalations (round 3, `docs/round3_page.html`); disagreements with the AI-assisted first pass get adjudicated | page live, waiting on labels |
| Frame SEER as a stress-test rate | Adopt: requests target sibling groups by design, so rates are conditional on that benchmark | text after round 3 |
| Token-matched top-10/15 baselines | Adopt: `src/run_baselines.sh` (Qwen3.5 plain, K=10 and 15, 30k); sibling lists average 11.6 tools | run tonight when idle |
| Equivalent cross-server tools | Adopt: `src/cross_server.py`; strict equivalence adds 4.0-4.8 accuracy points, order unchanged except expand+tags vs sibling (0.2 pt) | in Table III |
| Separate read-to-write violations; "selection-time potential escalation" | Adopt | text after round 3 |
| Split Table III, clearer headers | Adopt: 30k table plus 1k table, grouped headers | done |
| Anonymized artifact | Reject for SEIP: single-blind; the release/ bundle and README already cover reproduction | n/a |

## Reviewer round 2 (Oct 12)

SEIP call checked: 10 pages + 2 references, IEEE template, not double-anonymous. Adopted: independent
second rater on 50 blind items (`docs/independent_page.html`), count-matched k baseline (`matched`
variant), coarse operation-equivalence naming plus a 30-item human audit, server-clustered bootstrap
(`boot_range` in `estimate_missed.py`), reporting by effect type with read-to-write as the headline,
SEIP framing around three agent-builder questions. Human-only labels raise the miss share (author raw
about 24% vs 8% adjudicated), so estimated rates rise; the revision reports the human-label numbers.

## Reviewer round 3 (Oct 12)

Independent check resampled to 55 (25 flagged, 15 unflagged LLM, 15 unflagged retriever; one item per
request, fixed seed). Disagreement procedure: consensus after review, else a third person or "ambiguous",
never an author override; SEER reported three ways for ambiguous cases. Read-to-write is the primary
outcome (denominators: 646 read-intent requests and all 1,386). `miss_audit.py` explains the 8% vs 24%
gap: of 28 author-yes answers on unflagged picks, 20 were overturned during adjudication with the AI
verdict shown; the largest group is same-type, stronger effect (soft vs permanent revoke or delete),
which the four-level scale cannot express. Oct 16 is the decision point for the paper's story.

## Independent rater (Oct 13)

The 55-item check was labeled by an independent rater, a different person from the author, working on the author's
signed-in account (the page keeps one review per person per account). Confirmed by the author.
