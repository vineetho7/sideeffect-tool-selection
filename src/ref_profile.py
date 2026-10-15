"""Reference severities used for scoring, from a profiler independent of the system profile.

Reference = cross-family LLM (gemma3:12b) reading name + description, with the server's own
annotation overriding it when the annotation is decisive (readOnlyHint=true or destructiveHint=true
with readOnlyHint=false), since annotations were 95.8% accurate where present in the hand audit.
Usage: ref_profile.py audit   -> accuracy of the reference on the 300 hand-labeled tools
       ref_profile.py fill    -> profile every index in ref_needed.json + all eval-group members
"""
import csv, glob, json, sys
from common import PROC, RES, ROOT, jload, jdump
from llm_profile import classify

MODEL = "gemma3:12b"
SEV = {"read": 0, "create": 1, "update": 2, "destructive": 3}
CACHE = PROC / "ref_llm_cache.json"


def ref_of(t, cache):
    a = t.get("ann_op")
    if a == "read":
        return 0
    if a == "destructive":
        return 3
    op = classify(t["name"], t["description"], cache, model=MODEL)
    s = SEV.get(op, None)
    if a == "write" and s == 0:
        s = 2
    return s if s is not None else 0


if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    cache = jload(CACHE) if CACHE.exists() else {}
    if sys.argv[1] == "audit":
        from audit_score import kappa
        lab = {}
        for f in sorted(glob.glob(str(ROOT / "data" / "labels" / "profile_labels_part*.txt"))):
            for line in open(f):
                if line.strip() and not line.startswith("#"):
                    i, op = line.split()
                    lab[i] = SEV[op]
        rows = list(csv.DictReader(open(RES / "profile_audit.csv")))
        t = [lab[r["idx"]] for r in rows]
        p = [ref_of(cat[int(r["idx"])], cache) for r in rows]
        llm_only = [SEV.get(classify(cat[int(r["idx"])]["name"], cat[int(r["idx"])]["description"], cache, model=MODEL), 0) for r in rows]
        out = {"ref_exact": sum(a == b for a, b in zip(t, p)) / len(t), "ref_kappa": kappa(t, p),
               "ref_read_vs_write": sum((a == 0) == (b == 0) for a, b in zip(t, p)) / len(t),
               "ref_under": sum(b < a for a, b in zip(t, p)) / len(t), "ref_over": sum(b > a for a, b in zip(t, p)) / len(t),
               "gemma_only_exact": sum(a == b for a, b in zip(t, llm_only)) / len(t),
               "gemma_only_kappa": kappa(t, llm_only)}
        jdump(out, RES / "ref_profile_audit.json")
        print(json.dumps(out, indent=1))
    else:
        groups = jload(PROC / "sibling_groups.json")
        qs = jload(PROC / "queries.json")
        need = set(jload(PROC / "ref_needed.json")) if (PROC / "ref_needed.json").exists() else set()
        for q in qs:
            need.update(groups[q["group"]])
        ref = jload(PROC / "ref_sev.json") if (PROC / "ref_sev.json").exists() else {}
        for n, i in enumerate(sorted(need)):
            if str(i) not in ref:
                ref[str(i)] = ref_of(cat[i], cache)
            if n % 200 == 0:
                jdump(cache, CACHE)
                jdump(ref, PROC / "ref_sev.json")
        jdump(cache, CACHE)
        jdump(ref, PROC / "ref_sev.json")
        print("reference severities", len(ref))
