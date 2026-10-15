"""Paired comparisons between selection variants on the same requests (exact McNemar + bootstrap CI)."""
import json
from math import comb
import numpy as np
from common import RES, jload, jdump


def mcnemar(a, b):
    b01 = sum(1 for x, y in zip(a, b) if x == 0 and y == 1)
    b10 = sum(1 for x, y in zip(a, b) if x == 1 and y == 0)
    n = b01 + b10
    k = min(b01, b10)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return b01, b10, p


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    out = []
    for model in ("qwen3.5-latest", "gemma3-12b", "qwen3-1.7b", "phi4-14b"):
        for n in ("n0", "n1000"):
            base = RES / f"sel_plain_{n}_qwen3emb_{model}_k5.json"
            if not base.exists():
                continue
            a = {r["qid"]: r["correct"] for r in jload(base)}
            for v in ("native", "tags", "sibling", "expand", "expandtags"):
                f = RES / f"sel_{v}_{n}_qwen3emb_{model}_k5.json"
                if not f.exists():
                    continue
                b = {r["qid"]: r["correct"] for r in jload(f)}
                q = sorted(set(a) & set(b))
                x, y = np.array([a[i] for i in q]), np.array([b[i] for i in q])
                d = y - x
                bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
                b01, b10, p = mcnemar(x, y)
                out.append({"model": model, "N": n, "variant": v, "delta_acc": float(d.mean()),
                            "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                            "gained": b01, "lost": b10, "p_mcnemar": p})
                print(f"{model:15s} {n:6s} {v:8s} dAcc={100*d.mean():+.1f} CI=[{100*np.percentile(bs,2.5):+.1f},{100*np.percentile(bs,97.5):+.1f}] +{b01}/-{b10} p={p:.2g}")
    jdump(out, RES / "paired_tests.json")
    # ablation: each added component against the previous one (Qwen3.5, 30k)
    load = lambda v: {r["qid"]: r["correct"] for r in jload(RES / f"sel_{v}_n0_qwen3emb_qwen3.5-latest_k5.json")}
    abl = []
    for a, b in (("expand", "expandtags"), ("expandtags", "sibling"), ("expand", "sibling")):
        A, B = load(a), load(b)
        q = sorted(A)
        x, y = np.array([A[i] for i in q]), np.array([B[i] for i in q])
        d = y - x
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        g, l, pv = mcnemar(x, y)
        abl.append({"from": a, "to": b, "delta": float(d.mean()),
                    "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "p": pv})
        print(f"ablation {a}->{b} {100*d.mean():+.1f} [{100*abl[-1]['ci'][0]:+.1f},{100*abl[-1]['ci'][1]:+.1f}] p={pv:.2f}")
    jdump(abl, RES / "ablation_pairs.json")
    # candidate budget: is the expansion gain more than seeing more tools? (Qwen3.5, 30k)
    lk = lambda v, k=5: {r["qid"]: r["correct"] for r in jload(RES / f"sel_{v}_n0_qwen3emb_qwen3.5-latest_k{k}.json")}
    bud = []
    for (a, ka), (b, kb) in ((("plain", 5), ("plain", 10)), (("plain", 5), ("plain", 15)), (("plain", 5), ("matched", 5)),
                             (("matched", 5), ("expand", 5)), (("matched", 5), ("sibling", 5)), (("plain", 10), ("expand", 5)),
                             (("plain", 15), ("expand", 5)), (("plain", 15), ("sibling", 5))):
        if not all((RES / f"sel_{v}_n0_qwen3emb_qwen3.5-latest_k{k}.json").exists() for v, k in ((a, ka), (b, kb))):
            print("budget: missing run for", a, ka, b, kb); continue
        A, B = lk(a, ka), lk(b, kb)
        q = sorted(A)
        x, y = np.array([A[i] for i in q]), np.array([B[i] for i in q])
        d = y - x
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        g, l, pv = mcnemar(x, y)
        nm = lambda v, k: "matched_per_request" if v == "matched" else f"{v}_k{k}"
        bud.append({"from": nm(a, ka), "to": nm(b, kb), "delta": float(d.mean()),
                    "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "gained": g, "lost": l, "p": pv})
        print(f"budget {a}_k{ka}->{b}_k{kb} {100*d.mean():+.1f} [{100*bud[-1]['ci'][0]:+.1f},{100*bud[-1]['ci'][1]:+.1f}] p={pv:.3g}")
    for m in ("phi4-14b", "qwen3-1.7b", "gemma3-12b"):      # count-matched for the other selectors, when run
        lm = lambda v: {r["qid"]: r["correct"] for r in jload(RES / f"sel_{v}_n0_qwen3emb_{m}_k5.json")}
        if not (RES / f"sel_matched_n0_qwen3emb_{m}_k5.json").exists():
            print("budget: no count-matched run for", m); continue
        for a, b in (("plain", "matched"), ("matched", "sibling")):
            A, B = lm(a), lm(b); q = sorted(A)
            x, y = np.array([A[i] for i in q]), np.array([B[i] for i in q]); d = y - x
            bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
            g, l, pv = mcnemar(x, y)
            bud.append({"model": m, "from": a, "to": b, "delta": float(d.mean()),
                        "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "gained": g, "lost": l, "p": pv})
            print(f"budget {m} {a}->{b} {100*d.mean():+.1f} p={pv:.3g}")
    jdump(bud, RES / "budget_pairs.json")
