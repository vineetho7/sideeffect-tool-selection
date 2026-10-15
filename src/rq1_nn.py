"""RQ1: for every tool of a sibling group whose members are all in the study pool (on servers with at
least three non-sibling tools), is its most similar other tool on the same server a sibling?
Chance = (group size - 1) / (server tools - 1). Writes results/rq1_nearest_neighbour.json.
"""
from collections import defaultdict
import numpy as np
from common import PROC, RES, jload, jdump

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    pool = jload(PROC / "pool.json")
    pos = {t: i for i, t in enumerate(pool)}
    groups = jload(PROC / "sibling_groups.json")
    by = defaultdict(list)
    for t in pool:
        by[cat[t]["server"]].append(t)
    out = {}
    for emb in ("minilm", "bgebase", "qwen3emb"):
        E = np.load(PROC / f"pool_emb_{emb}.npy")
        hit, chance = [], []
        for g, idx in groups.items():
            if any(i not in pos for i in idx):
                continue
            srv = by[g.split("::")[0]]
            if len(srv) < len(idx) + 3:
                continue
            S = E[[pos[i] for i in srv]]
            for i in idx:
                order = [srv[j] for j in np.argsort(-(S @ E[pos[i]])) if srv[j] != i]
                hit.append(cat[order[0]].get("group") == g)
                chance.append((len(idx) - 1) / (len(srv) - 1))
        out[emb] = {"n": len(hit), "nn_is_sibling": float(np.mean(hit)), "chance": float(np.mean(chance))}
        print(emb, out[emb])
    jdump(out, RES / "rq1_nearest_neighbour.json")
