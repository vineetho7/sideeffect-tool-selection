"""Where selection errors come from: target not shortlisted, NONE, sibling, same function on another
server (similar name), or other tool."""
import glob, os, re
from collections import Counter
from common import PROC, RES, jload, jdump


def norm(n):
    return re.sub(r"[^a-z]", "", n.lower())


if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    out = {}
    for f in sorted(glob.glob(str(RES / "sel_*_n0_*.json")) + glob.glob(str(RES / "sel_*_n1000_*.json"))):
        tag = os.path.basename(f)[4:-5]
        c = Counter()
        for r in jload(f):
            if r["correct"]:
                continue
            g, p = r["gold_idx"], r["pred_idx"]
            if not r["in_cand"]:
                c["target_not_shortlisted"] += 1
            elif p is None:
                c["none_or_unparsed"] += 1
            elif cat[p].get("group") and cat[p].get("group") == cat[g].get("group"):
                c["sibling"] += 1
            elif cat[p]["server"] != cat[g]["server"] and (norm(cat[p]["name"]) == norm(cat[g]["name"]) or cat[p]["op"] == cat[g]["op"]):
                c["same_operation_other_server"] += 1
            else:
                c["other"] += 1
        n = sum(c.values())
        out[tag] = {"errors": n, **{k: v / n for k, v in c.items()}}
        print(tag[:45], n, {k: round(100 * v / n, 1) for k, v in c.items()})
    jdump(out, RES / "error_breakdown.json")
