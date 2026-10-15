"""Second-rater and adjudication results from the raw page exports (both rounds).

Inputs (data/labels/second_rater/): item_key.json, round2_items.json, round2_first.json, first-rater
labels, export/ (round-1 reviews + adjudication/final), export_round2/ (round-2 reviews + adjudication/round2).
Writes results/adjudication_summary.json, results/rater_round2.json, results/missed_rates.json and
data/labels/second_rater/{adjudicated,round2_adjudicated}.json.
Round 1 unflagged items are selector picks from the n0 selection runs; round 2 holds 50 retriever
top-1 and 50 selector picks. The main miss shares are the two-rater consensus on the independent sample's unflagged items
(15 per stratum); the author's blind answers (*_author) and the shares adjudicated against the
AI-assisted pass (*_ai_adjudicated) are kept as sensitivity.
"""
import json
from common import PROC, RES, jdump, jload
from analyze import wilson
from audit_score import kappa
from rater_agreement import first_rater

L = PROC.parent / "labels" / "second_rater"


def review(path):
    d = json.load(open(path))
    d = d.get("data", d)
    return max(d["reviews"].values(), key=lambda r: len(r["answers"]))["answers"]


def share(labels, ids):
    ids = [i for i in ids if labels.get(i) in ("yes", "no")]
    k = sum(labels[i] == "yes" for i in ids)
    return {"yes": k, "n": len(ids), "rate": k / max(1, len(ids)), "ci": wilson(k, len(ids))}


if __name__ == "__main__":
    # ---- round 1 ----
    tools1, _, key = first_rater()
    picks1 = jload(L / "round1_first_picks.json")      # first-rater verdicts before adjudication
    ans1 = review(L / "export" / "ratings" / "rater_account.json")
    adj1 = json.load(open(L / "export" / "adjudication" / "final.json"))
    adj1 = adj1.get("data", adj1)["final"]
    final1 = {i: adj1.get(i, (tools1 if i.startswith("t") else picks1).get(i))
              for i in list(key["tools"]) + list(key["picks"])}
    jdump(final1, L / "adjudicated.json")
    fl = [p for p, k in key["picks"].items() if k["src"] == "flagged"]
    un = [p for p, k in key["picks"].items() if k["src"] == "unflagged"]
    s1 = {"flagged_n": len(fl), "flagged_first_yes": sum(picks1[p] == "yes" for p in fl),
          "flagged_adj_yes": sum(final1[p] == "yes" for p in fl),
          "unflagged": share(final1, un), "unflagged_raw_second": share(ans1, un),
          "changed_flagged": [p for p in fl if final1[p] != picks1[p]],
          "unflagged_dropped_unsure": [p for p in un if final1[p] not in ("yes", "no")]}
    s1.update({"unflagged_adj_yes": s1["unflagged"]["yes"], "unflagged_n": s1["unflagged"]["n"],
               "unflagged_rate": s1["unflagged"]["rate"], "unflagged_rate_ci": s1["unflagged"]["ci"]})
    jdump(s1, RES / "adjudication_summary.json")
    # ---- round 2 ----
    items = jload(L / "round2_items.json")
    first2 = jload(L / "round2_first.json")
    ans2 = review(L / "export_round2" / "ratings" / "rater_account.json")
    adj2 = json.load(open(L / "export_round2" / "adjudication" / "round2.json"))
    adj2 = adj2.get("data", adj2)["final"]
    final2 = {it["id"]: adj2.get(it["id"], first2[it["id"]]) for it in items}
    jdump(final2, L / "round2_adjudicated.json")
    both = [i for i in final2 if ans2.get(i) in ("yes", "no")]
    jdump({"n": len(both), "agreement": sum(first2[i] == ans2[i] for i in both) / len(both),
           "kappa": kappa([first2[i] for i in both], [ans2[i] for i in both]),
           "first_yes": sum(v == "yes" for v in first2.values()), "first_n": len(first2),
           "second_yes": sum(v == "yes" for v in ans2.values()), "second_answered": len(ans2),
           "second_unsure": sum(v == "unsure" for v in ans2.values()),
           "disagreements": sum(ans2.get(i) != first2[i] for i in final2)}, RES / "rater_round2.json")
    sel2 = [it["id"] for it in items if it["src"] == "selector"]
    ret2 = [it["id"] for it in items if it["src"] == "retriever"]
    pooled = {**{p: final1[p] for p in un}, **{i: final2[i] for i in sel2}}
    raw = {**{p: ans1.get(p) for p in un}, **{i: ans2.get(i) for i in sel2}}
    out = {"selector": share(raw, list(raw)), "retriever": share(ans2, ret2),
           "selector_ai_adjudicated": share(pooled, list(pooled)), "retriever_ai_adjudicated": share(final2, ret2)}
    cons = jload(L / "consensus_labels.json")          # from independent_agreement.py; run it first
    for s, k in (("unflagged_selector", "selector"), ("unflagged_retriever", "retriever")):
        out[f"{k}_author"] = out[k]
        out[k] = share({i: v["label"] for i, v in cons.items()}, [i for i, v in cons.items() if v["stratum"] == s])
    jdump(out, RES / "missed_rates.json")
    for k, v in out.items():
        print(f"{k:22s} {v['yes']}/{v['n']} = {100*v['rate']:.1f}% [{100*v['ci'][0]:.1f}-{100*v['ci'][1]:.1f}]")
    print("round1 flagged first yes", s1["flagged_first_yes"], "-> adjudicated", s1["flagged_adj_yes"],
          "| unflagged dropped (unsure)", len(s1["unflagged_dropped_unsure"]))
