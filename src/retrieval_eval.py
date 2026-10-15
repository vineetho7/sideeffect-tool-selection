"""LLM-free retrieval study (RQ1 geometry + RQ2 retriever-level escalation).

For each retriever and catalog size: top-1 accuracy, SEER@1, mean escalation, recall@k,
Exposure@k (read golds with a sev>=2 tool in top-k), sibling share of top-1 errors.
"""
import re, json
import numpy as np
from rank_bm25 import BM25Okapi
from common import PROC, RES, EMBEDDERS, QFILE, SFX, jload, jdump
from catalogs import Catalogs, SIZES

K = 5
SEVF = None   # set in main: reference severity, system profile as fallback


def tok(s):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+", s)]


def metrics(rows):
    a = lambda k: float(np.mean([r[k] for r in rows])) if rows else float("nan")
    reads = [r for r in rows if r["gold_sev"] == 0]
    errs = [r for r in rows if not r["top1"]]
    return {"n": len(rows), "acc1": a("top1"), "recall_k": a("in_k"), "seer1": a("esc"),
            "mean_esc": a("esc_mag"), "deesc1": a("deesc"),
            "exposure_k_read": float(np.mean([r["exposed"] for r in reads])) if reads else float("nan"),
            "sibling_share_of_errors": float(np.mean([r["top1_sib"] for r in errs])) if errs else float("nan")}


def evaluate(scores_fn, cat, qs, C, n, pos):
    rows = []
    for qi, q in enumerate(qs):
        sub = np.array(C.subset(q["qid"], q["gold_idx"], n))
        sc = scores_fn(qi)[[pos[i] for i in sub]]
        order = sub[np.argsort(-sc, kind="stable")[:K]]
        top = cat[order[0]]
        g = q["gold_idx"]
        ps, gs = SEVF(order[0]), SEVF(g)
        rows.append({"qid": q["qid"], "top": int(order[0]), "top1": int(order[0] == g), "in_k": int(g in order),
                     "gold_sev": gs, "pred_sev": ps,
                     "esc": int(order[0] != g and ps > gs), "esc_mag": max(0, ps - gs) if order[0] != g else 0,
                     "deesc": int(order[0] != g and ps < gs),
                     "exposed": int(any(SEVF(i) >= 2 for i in order)),
                     "top1_sib": int(top.get("group") == q["group"])})
    return rows


def geometry(cat, E, qs, QE, pool, pos, emb=""):
    groups = jload(PROC / "sibling_groups.json")
    rng = np.random.default_rng(7)
    sib, same_srv, cross = [], [], []
    by_srv = {}
    for i in pool:
        by_srv.setdefault(cat[i]["server"], []).append(pos[i])
    for g, idx in groups.items():
        if any(i not in pos for i in idx):
            continue
        idx = np.array([pos[i] for i in idx])
        S = E[idx] @ E[idx].T
        sib += list(S[np.triu_indices(len(idx), 1)])
        srv = [j for j in by_srv[g.split("::")[0]] if cat[pool[j]].get("group") != g]
        if srv:
            same_srv += list((E[idx] @ E[rng.choice(srv, min(5, len(srv)))].T).ravel())
        cross += list((E[idx] @ E[rng.integers(0, len(pool), 5)].T).ravel())
    # query margin: sim(q, gold) - max sim(q, sibling)
    margins = []
    for qi, q in enumerate(qs):
        s = E[[pos[i] for i in groups[q["group"]]]] @ QE[qi]
        gi = groups[q["group"]].index(q["gold_idx"])
        margins.append(float(s[gi] - np.max(np.delete(s, gi))))
    np.savez_compressed(RES / f"geometry_{emb}{SFX}.npz", sib=np.array(sib), same=np.array(same_srv),
                        cross=np.array(cross), margin=np.array(margins))
    pct = lambda x: {"mean": float(np.mean(x)), "p10": float(np.percentile(x, 10)),
                     "p50": float(np.percentile(x, 50)), "p90": float(np.percentile(x, 90))}
    return {"sibling_pairs": pct(sib), "same_server_nonsibling": pct(same_srv),
            "cross_server": pct(cross), "query_margin_gold_minus_best_sibling": pct(margins),
            "frac_queries_sibling_outscores_gold": float(np.mean(np.array(margins) < 0))}


if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    qs = jload(PROC / QFILE)
    pool = jload(PROC / "pool.json")
    pos = {i: p for p, i in enumerate(pool)}
    from embed_all import tool_doc
    docs = [tool_doc(cat[i]) for i in pool]
    C = Catalogs(cat, pool)
    from profile_tools import hybrid_sev
    ref = jload(PROC / "ref_sev.json") if (PROC / "ref_sev.json").exists() else {}
    SEVF = lambda i: ref.get(str(int(i)), hybrid_sev(cat[int(i)]) or 0)
    out = {"geometry": {}, "retrieval": [], "per_query": {}}
    bm = BM25Okapi([tok(d) for d in docs])
    bm_scores = {}
    retrievers = {"bm25": lambda qi: bm_scores.setdefault(qi, np.asarray(bm.get_scores(tok(qs[qi]["query"])), dtype=np.float32))}
    for emb in EMBEDDERS:
        try:
            E = np.load(PROC / f"pool_emb_{emb}.npy")
            QE = np.load(PROC / f"query_emb_{emb}{SFX}.npy")
        except FileNotFoundError:
            continue
        out["geometry"][emb] = geometry(cat, E, qs, QE, pool, pos, emb)
        S = QE @ E.T
        retrievers[emb] = (lambda S: lambda qi: S[qi])(S)
    for name, fn in retrievers.items():
        for n in SIZES:
            rows = evaluate(fn, cat, qs, C, n, pos)
            m = {"retriever": name, "N": n or len(pool), **metrics(rows)}
            for s in (0, 1, 2, 3):
                m[f"acc1_gold_sev{s}"] = metrics([r for r in rows if r["gold_sev"] == s])["acc1"]
            out["retrieval"].append(m)
            out["per_query"][f"{name}_{n}"] = rows
            print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}), flush=True)
    jdump(out, RES / f"retrieval{SFX}.json")
    print(json.dumps(out["geometry"], indent=1))
