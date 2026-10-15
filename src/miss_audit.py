"""Why the author's raw labels and the adjudicated labels differ on unflagged wrong picks.

For every unflagged pick the author labeled (round 1 and round 2): AI-assisted first pass, author's
blind answer, adjudicated label, and the picked tool's effect type. Writes results/miss_audit.json.
"""
from collections import Counter
from common import RES, jload, jdump
from adjudication import L, review
from effect_types import effect

if __name__ == "__main__":
    key = jload(L / "item_key.json")["picks"]
    r1 = [(p, k["request"], k["picked"], "selector") for p, k in key.items() if k["src"] == "unflagged"]
    r2 = [(x["id"], x["request"], x["picked"], x["src"]) for x in jload(L / "round2_items.json")]
    first = {**jload(L / "round1_first_picks.json"), **jload(L / "round2_first.json")}
    raw = {**review(L / "export" / "ratings" / "rater_account.json"),
           **review(L / "export_round2" / "ratings" / "rater_account.json")}
    adj = {**jload(L / "adjudicated.json"), **jload(L / "round2_adjudicated.json")}
    rows = [{"id": i, "request": q, "picked": p, "stratum": s, "effect": effect(p),
             "first": first.get(i), "author": raw.get(i), "adjudicated": adj.get(i)} for i, q, p, s in r1 + r2]
    by = {}
    for r in rows:
        b = by.setdefault(r["effect"], Counter())
        b["n"] += 1
        b["author_yes"] += r["author"] == "yes"
        b["first_yes"] += r["first"] == "yes"
        b["adjudicated_yes"] += r["adjudicated"] == "yes"
        b["author_yes_adjudicated_no"] += r["author"] == "yes" and r["adjudicated"] == "no"
    flips = [r for r in rows if r["author"] == "yes" and r["adjudicated"] == "no"]
    jdump({"by_effect": {k: dict(v) for k, v in by.items()}, "flips": flips, "rows": rows}, RES / "miss_audit.json")
    print(f"{'effect':10s} {'n':>4s} {'AI yes':>7s} {'author yes':>11s} {'adj yes':>8s} {'author yes->adj no':>19s}")
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]["n"]):
        print(f"{k:10s} {v['n']:4d} {v['first_yes']:7d} {v['author_yes']:11d} {v['adjudicated_yes']:8d} {v['author_yes_adjudicated_no']:19d}")
    print(sum(r["author"] in ("yes", "no") for r in rows), "of", len(rows), "answered by the author;", len(flips), "author-yes overturned to no;", sum(r["author"] == "no" and r["adjudicated"] == "yes" for r in rows), "author-no turned yes")
