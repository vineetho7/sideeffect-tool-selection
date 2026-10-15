"""Agreement between the author and the independent rater on the 55-item check, per stratum.

Author labels: round-1/round-3 answers for flagged items, blind round-2 answers for unflagged ones.
Reports raw agreement, Cohen's kappa and positive agreement (2a / (2a + b + c)); 'unsure' on either
side drops the item. Writes results/independent_agreement.json and the disagreement list.
"""
from common import RES, jload, jdump
from adjudication import L, review
from audit_score import kappa

ACCOUNT = "rater_account.json"


def stats(pairs):
    pairs = [(a, b) for a, b in pairs if a in ("yes", "no") and b in ("yes", "no")]
    a = sum(x == y == "yes" for x, y in pairs)
    d = sum(x == y == "no" for x, y in pairs)
    return {"n": len(pairs), "agree": (a + d) / len(pairs), "kappa": kappa([x for x, _ in pairs], [y for _, y in pairs]),
            "pos_agree": 2 * a / max(1, 2 * a + len(pairs) - a - d), "both_yes": a,
            "author_yes": sum(x == "yes" for x, _ in pairs), "independent_yes": sum(y == "yes" for _, y in pairs)}


if __name__ == "__main__":
    items = jload(L / "independent_items.json")
    r3 = {it["id"]: it["human_r1"] for it in jload(L / "round3_items.json")}
    author = {**review(L / "export_round2" / "ratings" / ACCOUNT), **review(L / "export_round3" / "ratings" / ACCOUNT),
              **{i: v for i, v in r3.items() if v}}
    ind = review(L / "export_independent" / "ratings" / ACCOUNT)
    out = {s: stats([(author.get(x["id"]), ind.get(x["id"])) for x in items if s == "all" or x["stratum"] == s])
           for s in ("all", "flagged", "unflagged_selector", "unflagged_retriever")}
    out["disagreements"] = [{**x, "author": author.get(x["id"]), "independent": ind.get(x["id"])}
                            for x in items if author.get(x["id"]) != ind.get(x["id"])]
    jdump(out, RES / "independent_agreement.json")
    cp = L / "export_consensus" / "consensus" / "independent.json"
    if cp.exists():
        c = jload(cp); c = c.get("data", c)["final"]
        final = {x["id"]: c.get(x["id"], author.get(x["id"])) for x in items}
        jdump({x["id"]: {"stratum": x["stratum"], "label": final[x["id"]]} for x in items}, L / "consensus_labels.json")
        for s in ("flagged", "unflagged_selector", "unflagged_retriever"):
            v = [final[x["id"]] for x in items if x["stratum"] == s]
            print(f"consensus {s:20s} yes={v.count('yes')} no={v.count('no')} ambiguous={v.count('ambiguous')}")
    for s, v in out.items():
        if s != "disagreements":
            print(f"{s:20s} n={v['n']:2d} agree={100*v['agree']:.1f}% kappa={v['kappa']:.2f} pos_agree={v['pos_agree']:.2f} "
                  f"author_yes={v['author_yes']} independent_yes={v['independent_yes']} both={v['both_yes']}")
    print(len(out["disagreements"]), "disagreements (incl. unsure/missing)")
