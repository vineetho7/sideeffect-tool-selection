"""All profilers vs the 300 hand labels, on all 300 tools (rule 'unknown' counted as read)."""
import csv, glob
from common import PROC, RES, ROOT, jload, jdump
from audit_score import kappa, SEV
from profile_tools import hybrid_sev

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    lab = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "labels" / "profile_labels_part*.txt"))):
        for line in open(f):
            if line.strip() and not line.startswith("#"):
                i, op = line.split()
                lab[i] = SEV[op]
    rows = list(csv.DictReader(open(RES / "profile_audit.csv")))
    llm = jload(RES / "llm_profile_audit.json")
    refc = jload(PROC / "ref_llm_cache.json")
    from ref_profile import ref_of
    t = [lab[r["idx"]] for r in rows]
    prof = {
        "rules": [cat[int(r["idx"])]["sev"] or 0 for r in rows],
        "system": [hybrid_sev(cat[int(r["idx"])]) or 0 for r in rows],
        "qwen_llm": [SEV.get(llm[r["idx"]] or "read") for r in rows],
        "reference": [ref_of(cat[int(r["idx"])], refc) for r in rows],
    }
    out = {}
    for k, p in prof.items():
        out[k] = {"exact": sum(a == b for a, b in zip(t, p)) / len(t), "kappa": kappa(t, p),
                  "read_write": sum((a == 0) == (b == 0) for a, b in zip(t, p)) / len(t),
                  "under": sum(b < a for a, b in zip(t, p)) / len(t), "over": sum(b > a for a, b in zip(t, p)) / len(t)}
        print(k, {a: round(b, 3) for a, b in out[k].items()})
    jdump(out, RES / "profile_compare.json")
