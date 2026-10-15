"""Round 3: every reference-flagged escalation in the reported (non-terse) runs, for a full human pass.

Same flagged set as escalation_precision.py over the top-5 runs (k10/k15 baselines excluded).
Writes data/labels/second_rater/round3_items.json
(shuffled; the page shows request/right/picked only) and round3_first.json (first-rater verdicts).
Items the author already answered blind in round 1 carry that answer in "human_r1" and are not asked again.
"""
import glob, hashlib, os, random
from common import PROC, RES, ROOT, jload, jdump
from analyze import LABELS
from adjudication import review

OUT = ROOT / "data" / "labels" / "second_rater"

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    ref = jload(PROC / "ref_sev.json")
    qs = {q["qid"]: q for q in jload(PROC / "queries.json")}
    flagged = {}

    def add(qid, p):
        g = qs[qid]["gold_idx"]
        gs, ps = ref.get(str(g)), ref.get(str(p))
        if p is None or p == g or gs is None or ps is None or ps <= gs:
            return
        flagged.setdefault((qs[qid]["query"], cat[p]["name"]), (qid, g, p))

    for f in sorted(glob.glob(str(RES / "sel_*.json"))):
        if os.path.basename(f).endswith("_k5.json"):
            for r in jload(f):
                add(r["qid"], r["pred_idx"])
    for key, rows in sorted(jload(RES / "retrieval.json")["per_query"].items()):
        if key.startswith("qwen3emb_"):
            for r in rows:
                add(r["qid"], r["top"])
    key = jload(OUT / "item_key.json")["picks"]
    r1 = review(OUT / "export" / "ratings" / "rater_account.json")
    r1 = {(k["request"], k["picked"]): r1.get(p) for p, k in key.items() if k["src"] == "flagged"}
    items, first = [], {}
    for (query, pname), (qid, g, p) in sorted(flagged.items()):
        i = "f" + hashlib.md5(f"{query}|{pname}".encode()).hexdigest()[:10]
        items.append({"id": i, "qid": qid, "gold_idx": g, "pred_idx": p, "request": query,
                      "right": cat[g]["name"], "right_desc": cat[g]["description"][:300],
                      "picked": pname, "picked_desc": cat[p]["description"][:300], "human_r1": r1.get((query, pname))})
        v = LABELS.get((query, pname))
        first[i] = None if v is None else ("yes" if v == 1 else "no")
    random.Random(2027).shuffle(items)
    jdump(items, OUT / "round3_items.json")
    jdump(first, OUT / "round3_first.json")
    print(len(items), "items; first-rater yes", sum(v == "yes" for v in first.values()),
          "unlabeled", sum(v is None for v in first.values()),
          "reused from round 1", sum(it["human_r1"] is not None for it in items))
