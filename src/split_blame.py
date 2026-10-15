"""Separate retrieval from selection: for each end-to-end run, share of requests whose target is in
the shortlist, selector accuracy given it is, and verified escalations with the target present vs
missing (missing = the retriever's fault, though the selector could still have answered NONE)."""
from common import PROC, RES, jload, jdump
from analyze import LABELS

RUNS = [("qwen3.5-latest", ""), ("gemma3-12b", ""), ("qwen3-1.7b", ""),
        ("qwen3.5-latest", "_terse"), ("qwen3-1.7b", "_terse")]

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    ref = jload(PROC / "ref_sev.json")
    out = []
    for model, sfx in RUNS:
        qs = {q["qid"]: q for q in jload(PROC / ("queries_terse.json" if sfx else "queries.json"))}
        rows = jload(RES / f"sel_plain_n0_qwen3emb_{model}_k5{sfx}.json")

        def esc(r):
            p, g = r["pred_idx"], r["gold_idx"]
            if p is None or p == g or ref.get(str(p), 0) <= ref.get(str(g), 0):
                return 0
            return int(LABELS.get((qs[r["qid"]]["query"], cat[p]["name"])) == 1)

        inc = [r for r in rows if r["in_cand"]]
        miss = [r for r in rows if not r["in_cand"]]
        x = {"model": model, "terse": bool(sfx), "n": len(rows), "in_shortlist": len(inc) / len(rows),
             "acc_given_shortlisted": sum(r["correct"] for r in inc) / max(1, len(inc)),
             "acc_end_to_end": sum(r["correct"] for r in rows) / len(rows),
             "esc_target_present": sum(esc(r) for r in inc), "esc_target_missing": sum(esc(r) for r in miss),
             "none_when_missing": sum(r["pred_idx"] is None for r in miss) / max(1, len(miss))}
        out.append(x)
        print(x)
    jdump(out, RES / "escalation_split.json")
