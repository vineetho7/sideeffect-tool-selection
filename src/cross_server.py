"""Cross-server equivalent picks: wrong picks on another server whose tool does the same thing.

Equivalent = other server, same (verb, resource) profile and same reference severity. Reports
server-agnostic accuracy (correct or equivalent) and how many escalation flags such picks carry.
"""
import glob, os
from common import PROC, RES, jload, jdump

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    ref = jload(PROC / "ref_sev.json")
    sev = lambda i: ref.get(str(i))
    equiv = lambda p, g: (cat[p]["server"] != cat[g]["server"] and cat[p]["verb"] == cat[g]["verb"]
                          and cat[p]["resource"] and cat[p]["resource"] == cat[g]["resource"] and sev(p) is not None and sev(p) == sev(g))
    out = {}
    for f in sorted(glob.glob(str(RES / "sel_*_n0_qwen3emb_*.json"))):
        if f.endswith("_terse.json"):
            continue
        rows = jload(f)
        wrong = [r for r in rows if r["pred_idx"] is not None and not r["correct"]]
        other = [r for r in wrong if cat[r["pred_idx"]]["server"] != cat[r["gold_idx"]]["server"]]
        eq = [r for r in wrong if equiv(r["pred_idx"], r["gold_idx"])]
        n = len(rows)
        acc = sum(r["correct"] for r in rows) / n
        out[os.path.basename(f)[4:-5]] = {"n": n, "acc": acc, "acc_server_agnostic": acc + len(eq) / n,
                                          "wrong": len(wrong), "wrong_other_server": len(other), "equivalent": len(eq)}
    for k, v in out.items():
        print(f"{k:45s} acc {100*v['acc']:.1f} -> {100*v['acc_server_agnostic']:.1f}  "
              f"wrong {v['wrong']} other-server {v['wrong_other_server']} equivalent {v['equivalent']}")
    jdump(out, RES / "cross_server.json")
