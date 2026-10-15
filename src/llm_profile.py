"""LLM operation profiler: classify a tool's side effect from its name + description (cached).

Usage: llm_profile.py audit     -> profile the 300 audited tools, write results/llm_profile_audit.json
"""
import csv, json, re, sys
from common import PROC, RES, chat, jload, jdump, BIG

SYS = ("Classify the side effect of a software tool from its name and description. Answer as JSON "
       "{\"op\": \"read|create|update|destructive\"}. read: only returns information, changes nothing "
       "(includes search, compute, convert, generate text returned to the caller). create: adds new "
       "persistent state or sends something (record, file, message, booking, job). update: changes "
       "existing state, runs or executes, pays, logs in, starts/stops. destructive: deletes, revokes, "
       "cancels, overwrites irreversibly.")
CACHE = PROC / "llm_profile_cache.json"


def classify(name, desc, cache, model=BIG):
    key = f"{name}::{desc[:300]}"
    if key in cache:
        return cache[key]
    d = re.sub(r"\s+", " ", desc)[:600]
    r = chat([{"role": "system", "content": SYS}, {"role": "user", "content": f"Tool: {name}\nDescription: {d}"}],
             model=model, num_predict=20, fmt="json")
    try:
        op = json.loads(r["text"])["op"].strip().lower()
    except Exception:
        op = None
    cache[key] = op if op in ("read", "create", "update", "destructive") else None
    return cache[key]


if __name__ == "__main__":
    cache = jload(CACHE) if CACHE.exists() else {}
    if sys.argv[1] == "audit":
        cat = jload(PROC / "catalog.json")
        rows = list(csv.DictReader(open(RES / "profile_audit.csv")))
        out = {}
        for r in rows:
            t = cat[int(r["idx"])]
            out[r["idx"]] = classify(t["name"], t["description"], cache)
        jdump(out, RES / "llm_profile_audit.json")
    jdump(cache, CACHE)
