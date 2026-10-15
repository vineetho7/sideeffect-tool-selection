"""Draw seeded samples for manual validation.

profile_audit.csv : 300 tools stratified by inferred severity -> label true op class by hand
query_audit.csv   : 120 validated queries -> is the request unambiguous and does gold fit?
Labels are filled in by hand in the *_labeled.csv copies; audit_score.py computes agreement.
"""
import csv, random
from common import PROC, RES, jload

rng = random.Random(11)

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    by = {}
    for i, t in enumerate(cat):
        by.setdefault(t["sev"], []).append(i)
    pick = []
    for s, n in ((0, 90), (1, 60), (2, 75), (3, 60), (None, 15)):
        pick += rng.sample(by.get(s, []), min(n, len(by.get(s, []))))
    with open(RES / "profile_audit.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "server", "name", "description", "rule_op", "rule_sev", "ann_op", "true_op"])
        for i in pick:
            t = cat[i]
            w.writerow([i, t["server"], t["name"], t["description"][:300].replace("\n", " "),
                        t["op"], t["sev"], t["ann_op"], ""])
    if not (PROC / "queries.json").exists():
        raise SystemExit("profile sample written; queries not ready")
    qs = jload(PROC / "queries.json")
    with open(RES / "query_audit.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["qid", "query", "gold_name", "gold_desc", "siblings", "gold_fits", "unambiguous"])
        for q in rng.sample(qs, min(120, len(qs))):
            g = cat[q["gold_idx"]]
            sibs = [cat[i]["name"] for i in jload(PROC / "sibling_groups.json")[q["group"]] if i != q["gold_idx"]]
            w.writerow([q["qid"], q["query"], g["name"], g["description"][:200].replace("\n", " "),
                        "; ".join(sibs[:10]), "", ""])
    print("wrote", len(pick), "tools and query sample")
