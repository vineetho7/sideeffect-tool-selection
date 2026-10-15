"""Agreement of the second rater with the first (data/labels/second_rater/*.csv after filling)."""
import csv, glob, json
from common import RES, ROOT, jdump
from audit_score import kappa
from analyze import LABELS

D = ROOT / "data" / "labels" / "second_rater"

if __name__ == "__main__":
    first = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "labels" / "profile_labels_part*.txt"))):
        for line in open(f):
            if line.strip() and not line.startswith("#"):
                i, op = line.split(); first[i] = op
    out = {}
    t = [r for r in csv.DictReader(open(D / "tools.csv")) if r["true_op"].strip()]
    if t:
        a, b = [first[r["idx"]] for r in t], [r["true_op"].strip().lower() for r in t]
        out["tools"] = {"n": len(t), "agreement": sum(x == y for x, y in zip(a, b)) / len(t), "kappa": kappa(a, b)}
    e = [r for r in csv.DictReader(open(D / "escalations.csv")) if r["does_more_than_asked"].strip()]
    if e:
        a = [LABELS[(r["request"], r["picked_tool"])] for r in e]; b = [int(r["does_more_than_asked"]) for r in e]
        out["escalations"] = {"n": len(e), "agreement": sum(x == y for x, y in zip(a, b)) / len(e), "kappa": kappa(a, b)}
    u = [r for r in csv.DictReader(open(D / "unflagged.csv")) if r["does_more_than_asked"].strip()]
    if u:
        out["unflagged_missed_escalation_rate"] = {"n": len(u), "rate": sum(int(r["does_more_than_asked"]) for r in u) / len(u)}
    jdump(out, RES / "second_rater.json"); print(json.dumps(out, indent=1))
