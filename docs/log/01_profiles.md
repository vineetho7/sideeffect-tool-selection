# 01 — Operation profiles (2026-10-05)

Hand-labeled 300 tools (seeded sample stratified by rule class: 90 read, 60 create, 75 update,
60 destructive, 15 unknown). Labels in data/labels/profile_labels_part*.txt. Labeling convention:
- read: returns information only, incl. computing/converting/generating text returned to caller
- create: adds persistent state or sends something (record, message, booking, job, provisioned infra)
- update: mutates existing state; also run/execute code, pay/buy, login, start/stop, transfer
- destructive: deletes/revokes/irreversible (soft delete counted as destructive); "remove X from Y"
  where X persists elsewhere = update
Single annotator (no second rater) -> report as limitation; kappa below is profiler-vs-annotator.

| profiler (all 300, unknown->read) | exact | kappa | read/write | under-sev |
|---|---|---|---|---|
| rules only (285 covered) | 79.6 | .72 | 84.9 | 3.9 |
| qwen3.5 LLM | 84.0 | .77 | 94.3 | 6.7 |
| annotation + rules (system "hybrid") | 83.7 | .77 | 92.0 | 3.3 |
| annotation + qwen LLM | 83.0 | .76 | 95.3 | 5.7 |

Annotations alone: present on 64% of the sample; 95.8% read/write accurate where present;
only 32/57 truly destructive tools carry destructiveHint, 24/57 carry no annotation.

Decision: system uses the hybrid profile (zero LLM calls, fewest dangerous under-estimates).
Scoring uses an independent reference (gemma3:12b + decisive annotations) so the guard is not
graded against its own profile (ref_profile.py).
