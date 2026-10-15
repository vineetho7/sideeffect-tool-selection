"""Escalation rate including cases the reference misses.

total = verified + miss_rate x (unflagged wrong picks) / requests, where miss_rate is the
two-rater consensus share (Jeffreys) of real escalations among sampled unflagged wrong picks (results/missed_rates.json,
separately for selector picks and retriever top-1). "boot_range" is a 95% percentile bootstrap that
resamples gold servers (clusters) for the run and the miss sample within its stratum; "est_range" (both
Wilson bounds added) is kept for comparison.
"""
import numpy as np
from common import PROC, RES, jload, jdump

RUNS = ["plain_n0_qwen3emb_qwen3.5-latest_k5", "plain_n0_qwen3emb_gemma3-12b_k5",
        "plain_n0_qwen3emb_phi4-14b_k5", "plain_n0_qwen3emb_qwen3-1.7b_k5",
        "sibling_n0_qwen3emb_qwen3.5-latest_k5", "expand_n0_qwen3emb_qwen3.5-latest_k5",
        "sibling_n0_qwen3emb_phi4-14b_k5", "sibling_n0_qwen3emb_gemma3-12b_k5"]

if __name__ == "__main__":
    ref = jload(PROC / "ref_sev.json")
    rates = jload(RES / "missed_rates.json")
    S = {(x["run"], x["guard"]): x for x in jload(RES / "summary.json")}
    unflagged = lambda p, g: p is not None and p != g and ref.get(str(p), 0) <= ref.get(str(g), 0)
    out = {}

    from analyze import wilson, score, QTEXT
    QTEXT.update({q["qid"]: q["query"] for q in jload(PROC / "queries.json")})

    cat = jload(PROC / "catalog.json")
    rng = np.random.default_rng(2027)

    def boot(rows, r, B=4000):
        """rows: (gold server, confirmed escalation, unflagged wrong) per request."""
        srv = sorted({x[0] for x in rows})
        idx = {s: i for i, s in enumerate(srv)}
        c = np.zeros((len(srv), 3))
        for s_, conf, unf in rows:
            c[idx[s_]] += (1, conf, unf)
        k = rng.integers(0, len(srv), (B, len(srv)))
        tot = c[k].sum(1)
        p = rng.beta(r["yes"] + 0.5, r["n"] - r["yes"] + 0.5, B)   # Jeffreys: defined at 0 of n
        e = (tot[:, 1] + p * tot[:, 2]) / tot[:, 0]
        return [float(np.percentile(e, 2.5)), float(np.percentile(e, 97.5))]

    pm = lambda r: (r["yes"] + 0.5) / (r["n"] + 1)     # Jeffreys posterior mean, as in boot()

    def est(name, verified, m, n, r, sens, rows):
        lo, hi = r["ci"]
        vlo, vhi = wilson(round(verified * n), n)       # both terms' 95% bounds, added (conservative)
        out[name] = {"verified": verified, "verified_ci": [vlo, vhi], "unflagged_wrong": m, "n": n,
                     "miss_rate": r["rate"], "est_total": verified + pm(r) * m / n,
                     "est_range": [vlo + lo * m / n, vhi + hi * m / n], "boot_range": boot(rows, r),
                     "sensitivity": {k: verified + pm(v) * m / n for k, v in sens.items()}}
        x = out[name]
        print(f"{name[:40]:40s} verified {100*verified:.2f}%  est {100*x['est_total']:.2f}% "
              f"[{100*x['est_range'][0]:.2f}-{100*x['est_range'][1]:.2f}] boot [{100*x['boot_range'][0]:.2f}-{100*x['boot_range'][1]:.2f}]  sens " +
              " ".join(f"{k}={100*v:.2f}%" for k, v in x["sensitivity"].items()))

    for run in RUNS:
        rows = jload(RES / f"sel_{run}.json")
        m = sum(unflagged(r["pred_idx"], r["gold_idx"]) for r in rows)
        sc = score(rows, cat, ref, {})
        per = [(cat[r["gold_idx"]]["server"], x["esc_conf"], int(unflagged(r["pred_idx"], r["gold_idx"]))) for r, x in zip(rows, sc)]
        est(run, S[(run, "any_up")]["seer_conf"], m, len(rows), rates["selector"],
            {"author": rates["selector_author"], "ai_adjudicated": rates["selector_ai_adjudicated"]}, per)
    pq = jload(RES / "retrieval.json")["per_query"]["qwen3emb_0"]
    qg = {q["qid"]: q["gold_idx"] for q in jload(PROC / "queries.json")}
    gr = [x for x in jload(RES / "guard_retrieval_qwen3.5-latest.json")
          if x["retriever"] == "qwen3emb" and x["N"] == 0 and x["guard"] == "none"][0]
    m = sum(unflagged(r["top"], qg[r["qid"]]) for r in pq)
    rr = [{"qid": r["qid"], "gold_idx": qg[r["qid"]], "pred_idx": r["top"], "correct": int(r["top"] == qg[r["qid"]]),
           "in_cand": 1, "cand": [], "p_tok": 0} for r in pq]
    per = [(cat[r["gold_idx"]]["server"], x["esc_conf"], int(unflagged(r["pred_idx"], r["gold_idx"]))) for r, x in zip(rr, score(rr, cat, ref, {}))]
    est("retriever_top1_qwen3emb_30k", gr["seer_conf"], m, len(pq), rates["retriever"],
        {"author": rates["retriever_author"], "ai_adjudicated": rates["retriever_ai_adjudicated"]}, per)
    jdump(out, RES / "estimated_missed.json")
