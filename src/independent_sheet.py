"""Sample for an independent second rater: 25 flagged escalations (round 3), 15 unflagged LLM-selection
and 15 unflagged retriever wrong picks (round 2), shuffled, at most one item per request text. The page shows request, right and picked tool
only: no source, model, variant or other rater's verdict. Writes data/labels/second_rater/independent_items.json.
"""
import random
from common import ROOT, jload, jdump

L = ROOT / "data" / "labels" / "second_rater"

if __name__ == "__main__":
    rng = random.Random(1027)
    seen = set()

    def draw(pool, k):
        out = []
        for x in rng.sample(pool, len(pool)):
            if x["request"] not in seen and len(out) < k:
                seen.add(x["request"]); out.append(x)
        return out

    r2 = jload(L / "round2_items.json")
    strata = {"flagged": draw(jload(L / "round3_items.json"), 25),
              "unflagged_selector": draw([x for x in r2 if x["src"] == "selector"], 15),
              "unflagged_retriever": draw([x for x in r2 if x["src"] == "retriever"], 15)}
    keep = ("id", "request", "right", "right_desc", "picked", "picked_desc")
    items = [{**{k: x[k] for k in keep}, "stratum": s} for s, xs in strata.items() for x in xs]
    rng.shuffle(items)
    jdump(items, L / "independent_items.json")
    print(len(items), "items")
