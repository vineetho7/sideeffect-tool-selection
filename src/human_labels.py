"""Author's escalation labels for every flagged pair in the top-5 runs: round-1 blind answers (25)
plus round-3 answers (153); the two-rater consensus replaces them on the 25 independently checked items. Writes data/labels/human_escalations.csv (query, pred, true_escalation;
blank = unsure), the label source analyze.py uses.
"""
import csv, json
from common import ROOT, jload
from adjudication import L, review

ACCOUNT = "rater_account.json"

if __name__ == "__main__":
    items = jload(L / "round3_items.json")
    r3 = review(L / "export_round3" / "ratings" / ACCOUNT)
    cons = jload(L / "consensus_labels.json")          # from independent_agreement.py; run it first
    out = ROOT / "data" / "labels" / "human_escalations.csv"
    n = {"yes": 0, "no": 0, None: 0, "unsure": 0, "ambiguous": 0}
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["query", "pred", "true_escalation", "source"])
        for it in items:
            a = it["human_r1"] if it["human_r1"] in ("yes", "no") else r3.get(it["id"])
            src = "round1" if it["human_r1"] in ("yes", "no") else "round3"
            if it["id"] in cons:
                a, src = cons[it["id"]]["label"], "consensus"
            n[a] += 1
            w.writerow([it["request"], it["picked"], {"yes": 1, "no": 0}.get(a, ""), src])
        for items_f, exp, tag in (("baseline_items.json", "export_round4", "round4"),     # candidate-budget runs
                                  ("round5_items.json", "export_round5", "round5"),        # Phi-4 / Qwen3-1.7B count-matched
                                  ("round6_items.json", "export_round6", "round6")):       # Gemma3 count-matched
            rp = L / exp / "ratings" / ACCOUNT
            ans = review(rp) if rp.exists() else {}
            for it in jload(L / items_f):
                a = ans.get(it["id"])
                n[a] += 1
                w.writerow([it["request"], it["picked"], {"yes": 1, "no": 0}.get(a, ""), tag])
    print(n, "->", out)
