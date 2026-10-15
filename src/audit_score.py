"""Agreement of rule profiles and native annotations with hand labels (profile_audit.csv)."""
import csv, json
from collections import Counter
from common import ROOT, RES, jdump

SEV = {"read": 0, "create": 1, "update": 2, "destructive": 3}


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(a) | set(b)) / n / n
    return (po - pe) / (1 - pe)


if __name__ == "__main__":
    lab = {}
    for f in sorted((ROOT / "data" / "labels").glob("profile_labels_part*.txt")):
        for line in open(f):
            if line.strip() and not line.startswith("#"):
                i, op = line.split()
                lab[i] = op
    rows = [r for r in csv.DictReader(open(RES / "profile_audit.csv")) if r["idx"] in lab]
    known = [r for r in rows if r["rule_op"]]
    truth = [lab[r["idx"]] for r in known]
    rule = [r["rule_op"] for r in known]
    out = {"labeled": len(rows), "rule_covered": len(known),
           "rule_exact_acc": sum(a == b for a, b in zip(truth, rule)) / len(known),
           "rule_kappa": kappa(truth, rule),
           "rule_read_vs_write_acc": sum((a == "read") == (b == "read") for a, b in zip(truth, rule)) / len(known),
           "rule_underestimates_severity": sum(SEV[b] < SEV[a] for a, b in zip(truth, rule)) / len(known),
           "rule_overestimates_severity": sum(SEV[b] > SEV[a] for a, b in zip(truth, rule)) / len(known),
           "per_class_precision": {}, "confusion": Counter(f"{a}->{b}" for a, b in zip(truth, rule) if a != b)}
    for c in SEV:
        pred = [a for a, b in zip(truth, rule) if b == c]
        out["per_class_precision"][c] = {"n": len(pred), "precision": sum(x == c for x in pred) / max(1, len(pred))}
    # native annotations: readOnlyHint as a read/write classifier where present
    ann = [r for r in rows if r["ann_op"]]
    out["annotation_present"] = len(ann) / len(rows)
    out["annotation_read_vs_write_acc"] = sum((lab[r["idx"]] == "read") == (r["ann_op"] == "read") for r in ann) / max(1, len(ann))
    out["rule_read_vs_write_acc_on_same_annotated"] = sum((lab[r["idx"]] == "read") == (r["rule_op"] == "read") for r in ann if r["rule_op"]) / max(1, sum(1 for r in ann if r["rule_op"]))
    dest = [r for r in rows if lab[r["idx"]] == "destructive"]
    out["true_destructive"] = len(dest)
    out["true_destructive_flagged_by_annotation"] = sum(r["ann_op"] == "destructive" for r in dest)
    out["true_destructive_without_any_annotation"] = sum(not r["ann_op"] for r in dest)
    out["true_destructive_flagged_by_rule"] = sum(r["rule_op"] == "destructive" for r in dest)
    jdump(json.loads(json.dumps(out)), RES / "profile_audit_score.json")
    print(json.dumps(out, indent=1))
