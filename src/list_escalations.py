"""Dump every escalation flagged by the reference across selection runs and retriever-only top-1
(N=0 pool) into results/escalations.csv for hand verification. One row per unique (query, pred)."""
import csv, glob, os
from common import PROC, RES, jload

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    ref = jload(PROC / "ref_sev.json")
    qsets = {"": {q["qid"]: q for q in jload(PROC / "queries.json")}}
    if (PROC / "queries_terse.json").exists():
        qsets["_terse"] = {q["qid"]: q for q in jload(PROC / "queries_terse.json")}
    seen = {}
    for f in sorted(glob.glob(str(RES / "sel_*.json"))):
        tag = os.path.basename(f)[4:-5]
        qs = qsets["_terse" if tag.endswith("_terse") else ""]
        for r in jload(f):
            p, g = r["pred_idx"], r["gold_idx"]
            if p is None or p == g or ref.get(str(p)) is None or ref[str(p)] <= ref[str(g)]:
                continue
            k = (qs[r["qid"]]["query"], p)
            seen.setdefault(k, {"qid": r["qid"], "query": k[0], "gold": cat[g]["name"],
                                "gold_desc": cat[g]["description"][:160], "gold_ref": ref[str(g)],
                                "pred": cat[p]["name"], "pred_desc": cat[p]["description"][:160],
                                "pred_ref": ref[str(p)], "runs": []})["runs"].append(tag)
    for name in ("retrieval.json", "retrieval_terse.json"):
        if not (RES / name).exists():
            continue
        qs = qsets["_terse" if "terse" in name else ""]
        for key, rows in jload(RES / name)["per_query"].items():
            if not key.endswith("_0"):
                continue
            for r in rows:
                if r["esc"]:
                    q = qs[r["qid"]]
                    k = (q["query"], r["top"])
                    seen.setdefault(k, {"qid": r["qid"], "query": k[0], "gold": cat[q["gold_idx"]]["name"],
                                        "gold_desc": cat[q["gold_idx"]]["description"][:160],
                                        "gold_ref": ref.get(str(q["gold_idx"])), "pred": cat[r["top"]]["name"],
                                        "pred_desc": cat[r["top"]]["description"][:160],
                                        "pred_ref": r["pred_sev"], "runs": []})["runs"].append("top1:" + key)
    rows = list(seen.values())
    with open(RES / "escalations.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ["true_escalation"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "runs": ";".join(r["runs"]), "true_escalation": ""})
    print("unique escalations", len(rows), "from selection runs",
          sum(1 for r in rows if any(not x.startswith("top1:") for x in r["runs"])))
