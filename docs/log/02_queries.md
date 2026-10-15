# 02 — Requests (2026-10-05/06)

- 700 escalation-capable groups drawn (<=3 per server, <=6 per publisher), 582 servers.
- Per group: target the read tool + up to two of {destructive, update, create} (strongest first).
- Generator qwen3.5 (temp 0.7, JSON) sees target + siblings, writes a request only the target fulfils.
- Leak filter: drop requests naming any group tool or containing a snake_case identifier.
- Validator gemma3:12b routes among shuffled group members (<=12, reads first); keep if it picks target.
- Result: generated 1,771; leak/parse 355; validator disagreed 30; kept 1,386.
- Bug fixed mid-run: groups >12 members could lose their read tool in the first 12 -> members_of()
  sorts reads first. Resumed from cache; groups already generated kept their requests.
- Low validator disagreement (2%) says requests are very explicit about the operation:
  escalation rates measured on them are lower bounds for real, vaguer requests.

## Hand audit (120 seeded requests, data/labels/query_audit_labeled.csv)
gold fits 99.2%, unambiguous among siblings 98.3%.
Notable: a request for a cancellation *preview* whose correct tool is the cancel tool in
confirm=false mode: read intent, destructive-class tool -> a guard holds it (needless hold).
This "mode-switch" tool design is a real source of guard cost.

## Reference severity (gemma3 + decisive annotations) on the 300 audited tools
exact 82.3%, kappa .75, read/write 93.0%, under 3.0%, over 14.7%.
Not more accurate than the system hybrid (83.7%) -> plan: hand-check every escalation flagged
in the headline runs.
