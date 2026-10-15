"""Retriever-only routing (execute the top-1 tool) with each guard policy, intents from an LLM.
Usage: guard_retrieval.py [INTENT_MODEL]"""
import sys
import numpy as np
from common import PROC, RES, SFX, jload, jdump
from profile_tools import hybrid_sev
from analyze import POLICIES, boot, LABELS, wilson
from common import QFILE
import intent as intent_mod

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen3.5:latest"
    cat = jload(PROC / "catalog.json")
    ref = jload(PROC / "ref_sev.json")
    intents = intent_mod.load(model)
    pq = jload(RES / f"retrieval{SFX}.json")["per_query"]
    qtext = {q["qid"]: q["query"] for q in jload(PROC / QFILE)}
    out = []
    for key, rows in pq.items():
        name, n = key.rsplit("_", 1)
        for pol in ["none"] + list(POLICIES):
            esc, ex, held, needless, auto, conf, cex, unl = [], [], [], [], [], [], [], []
            for r in rows:
                p = r["top"]
                isev = intents[r["qid"]]["sev"]
                h = pol != "none" and isev is not None and POLICIES[pol](isev, hybrid_sev(cat[p]) or 0)
                e = r["esc"]
                lab = LABELS.get((qtext[r["qid"]], cat[p]["name"])) if e else 0
                c = int(e and lab == 1)
                conf.append(c); cex.append(int(c and not h)); unl.append(int(e and lab is None))
                esc.append(e); ex.append(int(e and not h)); held.append(int(h))
                needless.append(int(h and r["top1"])); auto.append(int(r["top1"] and not h))
            out.append({"retriever": name, "N": int(n), "guard": pol, "seer": float(np.mean(esc)),
                        "seer_exec": float(np.mean(ex)), "seer_conf": float(np.mean(conf)),
                        "seer_conf_exec": float(np.mean(cex)),
                        "seer_conf_wilson": wilson(sum(conf), len(conf)), "seer_conf_exec_wilson": wilson(sum(cex), len(cex)), "esc_unlabeled": float(np.mean(unl)), "seer_exec_ci": boot(ex), "held": float(np.mean(held)),
                        "needless": float(np.mean(needless)), "auto_correct": float(np.mean(auto))})
    jdump(out, RES / f"guard_retrieval_{model.replace(':', '-')}{SFX}.json")
    for x in out:
        if x["N"] in (0, 1000) or x["N"] > 5000:
            print(f"{x['retriever']:9s} N={x['N']:6d} {x['guard']:20s} seer={100*x['seer']:.2f} exec={100*x['seer_exec']:.2f} "
                  f"conf={100*x['seer_conf']:.2f} confExec={100*x['seer_conf_exec']:.2f} unlab={100*x['esc_unlabeled']:.2f} held={100*x['held']:.1f} needless={100*x['needless']:.1f} auto={100*x['auto_correct']:.1f}")
