"""Query-intent profiler: requested operation class per query, cached per model.
Usage: intent.py [MODEL]"""
import json, sys
from common import PROC, QFILE, SFX, chat, jload, jdump, BIG

SYS = ("Classify the operation a user request asks an assistant to perform. Answer as JSON "
       "{\"op\": \"read|create|update|delete\"}. read = look up, list, search, show, check, compute, "
       "download; create = make or add something new, send, post, submit, register; update = change, "
       "edit, move, close, merge, run, start, stop, pay, buy; delete = delete, remove, destroy, revoke, "
       "cancel.")
SEV = {"read": 0, "create": 1, "update": 2, "delete": 3}


def path(model):
    return PROC / f"intent_{model.replace(':', '-')}{SFX}.json"


def load(model):
    return jload(path(model))


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else BIG
    qs = jload(PROC / QFILE)
    out = jload(path(model)) if path(model).exists() else {}
    for q in qs:
        if q["qid"] in out:
            continue
        r = chat([{"role": "system", "content": SYS}, {"role": "user", "content": q["query"]}],
                 model=model, num_predict=20, fmt="json")
        try:
            op = json.loads(r["text"])["op"].strip().lower()
        except Exception:
            op = None
        out[q["qid"]] = {"sev": SEV.get(op), "p_tok": r["p_tok"], "wall": r["wall"]}
    jdump(out, path(model))
    print("intents", len(out))
