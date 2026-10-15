"""Re-resolve predicted tool names in selection runs: when several candidates share the predicted
name (same tool name on different servers), take the highest-ranked one, as a host that lists tools
in that order would. Rewrites pred_idx/correct in place and records 'name_ambiguous'."""
import glob, re
from common import PROC, RES, jload, jdump

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    tot = changed = amb = 0
    for f in sorted(glob.glob(str(RES / "sel_*.json"))):
        rows = jload(f)
        for r in rows:
            raw = r["pred_raw"].strip().lower()
            hits = [i for i in r["cand"] if cat[i]["name"].lower() == raw]
            r["name_ambiguous"] = int(len(hits) > 1)
            amb += r["name_ambiguous"]
            new = hits[0] if hits else None
            if new != r["pred_idx"]:
                changed += 1
            r["pred_idx"] = new
            r["correct"] = int(new == r["gold_idx"])
            tot += 1
        jdump(rows, f)
    print("rows", tot, "ambiguous names", amb, "pred changed", changed)
