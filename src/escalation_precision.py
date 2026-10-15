"""Precision of reference-flagged escalations against hand verdicts, over every flagged
(request, tool) pair in the reported runs: all selection runs + Qwen3-Emb retriever-only top-1."""
import glob, os
from collections import Counter
from common import PROC, RES, jload, jdump
from analyze import LABELS

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
        flagged[(qs[qid]["query"], cat[p]["name"])] = (gs, ps)

    for f in glob.glob(str(RES / "sel_*.json")):
        if os.path.basename(f).endswith("_terse.json"):
            continue
        for r in jload(f):
            add(r["qid"], r["pred_idx"])
    for key, rows in jload(RES / "retrieval.json")["per_query"].items():
        if key.startswith("qwen3emb_"):
            for r in rows:
                add(r["qid"], r["top"])
    lab = {k: LABELS.get(k) for k in flagged}
    done = {k: v for k, v in lab.items() if v is not None}
    true = [k for k, v in done.items() if v == 1]
    false = [k for k, v in done.items() if v == 0]
    pairs = lambda ks: dict(Counter(f"{flagged[k][0]}->{flagged[k][1]}" for k in ks))
    out = {"flagged": len(flagged), "labeled": len(done), "unlabeled": len(flagged) - len(done),
           "true": len(true), "precision": len(true) / len(done),
           "true_pairs": pairs(true), "false_pairs": pairs(false)}
    # terse runs: same check over the terse request set
    qt = {q["qid"]: q for q in jload(PROC / "queries_terse.json")}
    tf = {}
    for f in glob.glob(str(RES / "sel_*_terse.json")):
        for r in jload(f):
            p, g = r["pred_idx"], r["gold_idx"]
            if p is not None and p != g and ref.get(str(p), 0) > ref.get(str(g), 0):
                tf[(qt[r["qid"]]["query"], cat[p]["name"])] = 1
    for key_, rows in jload(RES / "retrieval_terse.json")["per_query"].items():
        if key_ == "qwen3emb_0":
            for r in rows:
                if r["esc"]:
                    tf[(qt[r["qid"]]["query"], cat[r["top"]]["name"])] = 1
    tl = {k: LABELS.get(k) for k in tf}
    out["terse"] = {"flagged": len(tf), "labeled": sum(v is not None for v in tl.values()),
                    "true": sum(v == 1 for v in tl.values())}
    jdump(out, RES / "escalation_precision.json")
    print(out)
    jdump([{"query": k[0], "pred": k[1]} for k, v in lab.items() if v is None], PROC / "esc_todo.json")
