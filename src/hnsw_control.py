"""Control: does approximate search (HNSW) explain any tool-selection error vs exact flat search?"""
import time
import hnswlib
import numpy as np
from common import PROC, RES, EMBEDDERS, jload, jdump

if __name__ == "__main__":
    qs = jload(PROC / "queries.json")
    pos = {i: p for p, i in enumerate(jload(PROC / "pool.json"))}
    gold = np.array([pos[q["gold_idx"]] for q in qs])
    out = []
    for emb in EMBEDDERS:
        try:
            E = np.load(PROC / f"pool_emb_{emb}.npy")
            Q = np.load(PROC / f"query_emb_{emb}.npy")
        except FileNotFoundError:
            continue
        t0 = time.perf_counter()
        S = Q @ E.T
        exact = np.argsort(-S, axis=1)[:, :10]
        flat_ms = (time.perf_counter() - t0) * 1000 / len(Q)
        lat = []
        for q in Q[:200]:                       # single-query latency, as an agent would issue it
            t0 = time.perf_counter()
            np.argpartition(-(E @ q), 10)[:10]
            lat.append(time.perf_counter() - t0)
        flat_single_ms = 1000 * float(np.median(lat))
        t0 = time.perf_counter()
        ix = hnswlib.Index(space="ip", dim=E.shape[1])
        ix.init_index(max_elements=len(E), ef_construction=200, M=16)
        ix.add_items(E, np.arange(len(E)))
        build_s = time.perf_counter() - t0
        for ef in (10, 20, 50, 100, 200):
            ix.set_ef(ef)
            lat = []
            labels = []
            for q in Q:
                t0 = time.perf_counter()
                l, _ = ix.knn_query(q, k=10)
                lat.append(time.perf_counter() - t0)
                labels.append(l[0])
            labels = np.array(labels)
            rec = np.mean([len(set(a) & set(b)) / 10 for a, b in zip(labels, exact)])
            out.append({"embedder": emb, "N": len(E), "ef": ef, "recall10_vs_exact": float(rec),
                        "top1_acc_hnsw": float(np.mean(labels[:, 0] == gold)),
                        "top1_acc_exact": float(np.mean(exact[:, 0] == gold)),
                        "top1_agree": float(np.mean(labels[:, 0] == exact[:, 0])),
                        "hnsw_ms_median": 1000 * float(np.median(lat)),
                        "flat_ms_median": flat_single_ms, "build_s": build_s})
            print(out[-1], flush=True)
    jdump(out, RES / "hnsw_control.json")
