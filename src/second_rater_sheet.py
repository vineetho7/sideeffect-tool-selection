"""Blind sheets for an independent second rater (first-rater verdicts hidden).

tools.csv        50 of the 300 audited tools        -> fill true_op (read|create|update|destructive)
escalations.csv  25 flagged escalations (main runs)  -> fill does_more_than_asked (1|0)
unflagged.csv    25 wrong picks the reference did NOT flag -> fill does_more_than_asked (1|0)
                 (estimates escalations the automatic reference misses)
"""
import csv, glob, random
from common import PROC, RES, ROOT, jload
from analyze import LABELS

OUT = ROOT / "data" / "labels" / "second_rater"
rng = random.Random(2027)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    cat = jload(PROC / "catalog.json")
    ref = jload(PROC / "ref_sev.json")
    qs = {q["qid"]: q for q in jload(PROC / "queries.json")}
    tools = rng.sample(list(csv.DictReader(open(RES / "profile_audit.csv"))), 50)
    with open(OUT / "tools.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["idx", "name", "description", "true_op"])
        for t in tools:
            w.writerow([t["idx"], t["name"], t["description"], ""])
    flagged, unflagged = {}, {}
    for f in sorted(glob.glob(str(RES / "sel_*_n0_*_k5.json"))):
        for r in jload(f):
            p, g = r["pred_idx"], r["gold_idx"]
            if p is None or p == g:
                continue
            q = qs[r["qid"]]
            row = (q["query"], cat[g]["name"], cat[g]["description"][:300], cat[p]["name"], cat[p]["description"][:300])
            k = (q["query"], cat[p]["name"])
            if ref.get(str(p), 0) > ref.get(str(g), 0) and k in LABELS:
                flagged[k] = row
            elif ref.get(str(p), 0) <= ref.get(str(g), 0):
                unflagged[k] = row
    for name, pool in (("escalations", flagged), ("unflagged", unflagged)):
        pick = rng.sample(sorted(pool), 25)
        with open(OUT / f"{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["request", "right_tool", "right_tool_description", "picked_tool", "picked_tool_description", "does_more_than_asked"])
            for k in pick:
                w.writerow(list(pool[k]) + [""])
    print("wrote", OUT, "flagged pool", len(flagged), "unflagged pool", len(unflagged))
