"""Terse variant of every validated request: <=12 casual words, no ids or values.

qwen3.5 rewrites; gemma3 re-validates among the sibling group (kept only if still routed to the
target), so the terse set stays unambiguous among siblings. Writes data/processed/queries_terse.json
with the same qids, so embeddings/intents/catalogs line up.
"""
import json, re
from common import PROC, chat, jload, jdump, unload, BIG
from gen_queries import members_of, validate, leaks

SYS = ("Rewrite the user's request the way a busy person would type it to an assistant: at most 12 "
       "words, casual, no ids, no quoted values, no tool names. Keep the action and the object. "
       "Reply as JSON {\"query\": \"...\"}.")

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    groups = jload(PROC / "sibling_groups.json")
    qs = jload(PROC / "queries.json")
    cache_p = PROC / "queries_terse_cache.json"
    cache = jload(cache_p) if cache_p.exists() else {}
    for i, q in enumerate(qs):
        if q["qid"] in cache:
            continue
        r = chat([{"role": "system", "content": SYS}, {"role": "user", "content": q["query"]}],
                 model=BIG, num_predict=60, fmt="json")
        try:
            cache[q["qid"]] = json.loads(r["text"])["query"].strip()
        except Exception:
            cache[q["qid"]] = None
        if i % 100 == 0:
            jdump(cache, cache_p)
            print("rewrite", i, flush=True)
    jdump(cache, cache_p)
    unload(BIG)                               # free memory before the validator model loads
    out, st = [], {"rewritten": 0, "leak": 0, "valid": 0, "invalid": 0}
    for q in qs:
        t = cache.get(q["qid"])
        members = [cat[i] for i in members_of(q["group"], groups, cat)]
        if not t or leaks(t, members):
            st["leak"] += 1
            continue
        st["rewritten"] += 1
        ok = validate(t, members) == cat[q["gold_idx"]]["name"]
        st["valid" if ok else "invalid"] += 1
        if ok:
            out.append({**q, "query": t, "orig_query": q["query"]})
    jdump(out, PROC / "queries_terse.json")
    jdump(st, PROC / "terse_stats.json")
    print(st, "words", sum(len(q["query"].split()) for q in out) / max(1, len(out)))
