"""Embed pool tool documents and queries with every embedder (cached .npy).
Usage: embed_all.py docs|queries [EMB ...]"""
import re, sys, time
import numpy as np
from common import PROC, EMBEDDERS, QFILE, SFX, embed, jload, jdump


def tool_doc(t):
    ps = ", ".join(p["name"] for p in t["params"][:10])
    d = re.sub(r"\s+", " ", t["description"])[:600]
    return f"{t['name']}: {d}" + (f" Parameters: {ps}" if ps else "")


if __name__ == "__main__":
    what = sys.argv[1]
    embs = sys.argv[2:] or list(EMBEDDERS)
    cat = jload(PROC / "catalog.json")
    pool = jload(PROC / "pool.json")
    for emb in embs:
        t0 = time.time()
        if what == "docs":
            docs = [tool_doc(cat[i]) for i in pool]
            out = []
            for s in range(0, len(docs), 2048):
                out.append(embed(docs[s:s + 2048], emb, "doc"))
                print(emb, s + 2048, f"{time.time()-t0:.0f}s", flush=True)
            np.save(PROC / f"pool_emb_{emb}.npy", np.concatenate(out))
        else:
            qs = jload(PROC / QFILE)
            np.save(PROC / f"query_emb_{emb}{SFX}.npy", embed([q["query"] for q in qs], emb, "query"))
        print("done", emb, what, f"{time.time()-t0:.0f}s", flush=True)
