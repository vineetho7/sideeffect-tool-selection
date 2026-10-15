"""Sample of 30 coarse-equivalent picks (other server, same verb, resource and reference severity)
from the 30k top-5 selection runs, one per request, for a human audit of whether the picked tool
would serve the request as well. Writes data/labels/second_rater/equiv_items.json.
"""
import glob, hashlib, random
from common import PROC, RES, ROOT, jload, jdump

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    ref = jload(PROC / "ref_sev.json")
    qs = {q["qid"]: q for q in jload(PROC / "queries.json")}
    sev = lambda i: ref.get(str(i))
    pool = {}
    for f in sorted(glob.glob(str(RES / "sel_*_n0_qwen3emb_*_k5.json"))):
        for r in jload(f):
            p, g = r["pred_idx"], r["gold_idx"]
            if p is None or p == g:
                continue
            if (cat[p]["server"] != cat[g]["server"] and cat[p]["verb"] == cat[g]["verb"] and cat[p]["resource"]
                    and cat[p]["resource"] == cat[g]["resource"] and sev(p) is not None and sev(p) == sev(g)):
                pool.setdefault(r["qid"], (g, p))
    items = []
    for qid in random.Random(2027).sample(sorted(pool), 30):
        g, p = pool[qid]
        items.append({"id": "q" + hashlib.md5(f"{qid}|{p}".encode()).hexdigest()[:10], "qid": qid, "request": qs[qid]["query"],
                      "right": cat[g]["name"], "right_desc": cat[g]["description"][:300],
                      "picked": cat[p]["name"], "picked_desc": cat[p]["description"][:300]})
    jdump(items, ROOT / "data" / "labels" / "second_rater" / "equiv_items.json")
    print(len(pool), "requests with an equivalent pick;", len(items), "sampled")
