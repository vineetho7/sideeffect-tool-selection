"""Agreement of independent reviewers (labeling page export) with the first rater and each other.

Export first:  ArtifactData list ratings -> out_dir data/labels/second_rater/export
Usage: rater_agreement.py
"""
import glob, itertools, json
from collections import Counter
from common import ROOT, RES, jload, jdump
from audit_score import kappa
from analyze import LABELS

D = ROOT / "data" / "labels" / "second_rater"


def first_rater():
    tools = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "labels" / "profile_labels_part*.txt"))):
        for line in open(f):
            if line.strip() and not line.startswith("#"):
                i, op = line.split()
                tools["t" + i] = op
    key = jload(D / "item_key.json")
    picks = {}
    for pid, k in key["picks"].items():
        v = LABELS.get((k["request"], k["picked"]))
        picks[pid] = "yes" if v == 1 else "no"        # unflagged picks: first rater's implicit "no"
    return tools, picks, key


def agree(a, b, ids):
    ids = [i for i in ids if a.get(i) not in (None, "unsure") and b.get(i) not in (None, "unsure")]
    if not ids:
        return None
    x, y = [a[i] for i in ids], [b[i] for i in ids]
    return {"n": len(ids), "agreement": sum(p == q for p, q in zip(x, y)) / len(ids), "kappa": kappa(x, y)}


if __name__ == "__main__":
    tools1, picks1, key = first_rater()
    snap = D / "round1_first_picks.json"
    if snap.exists():                       # first-rater verdicts as they were before adjudication
        picks1 = jload(snap)
    raters = {}
    for f in glob.glob(str(D / "export" / "**" / "*.json"), recursive=True):
        d = json.load(open(f))
        body = d.get("data", d)
        reviews = body.get("reviews") or {f.split("/")[-1][:-5]: body}   # one account can hold several reviews
        for rid, r in reviews.items():
            if r.get("answers"):
                raters[f"{r.get('rater') or 'anon'} ({rid[-4:]})"] = r["answers"]
    out = {"raters": {}, "pairs": {}}
    first = {**tools1, **picks1}
    tids, pids = list(tools1.keys() & set(f"t{x}" for x in key["tools"].values())), list(picks1)
    unflagged = [p for p in pids if key["picks"][p]["src"] == "unflagged"]
    for name, ans in raters.items():
        out["raters"][name] = {
            "answered": len(ans), "unsure": sum(v == "unsure" for v in ans.values()),
            "tools_vs_first": agree(first, ans, tids), "picks_vs_first": agree(first, ans, pids),
            "missed_escalation_rate": (sum(ans.get(p) == "yes" for p in unflagged) /
                                       max(1, sum(ans.get(p) in ("yes", "no") for p in unflagged)))}
    for a, b in itertools.combinations(raters, 2):
        out["pairs"][f"{a} | {b}"] = {"tools": agree(raters[a], raters[b], tids), "picks": agree(raters[a], raters[b], pids)}
    jdump(out, RES / "rater_agreement.json")
    print(json.dumps(out, indent=1))
