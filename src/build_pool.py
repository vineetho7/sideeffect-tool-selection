"""Study pool: every tool of the servers behind evaluated sibling groups, plus seeded random
servers until the pool reaches POOL tools. Catalog-size experiments sample from this pool."""
import random
from collections import defaultdict
from common import PROC, jload, jdump

POOL = 30000


def chosen_groups(cat, limit):
    """Same seeded group selection as gen_queries.py (fresh module rng)."""
    import importlib, gen_queries as G
    importlib.reload(G)
    groups = jload(PROC / "sibling_groups.json")
    esc = {g: v for g, v in groups.items()
           if any(cat[i]["sev"] == 0 for i in v) and any(cat[i]["sev"] >= 2 for i in v)
           and all(cat[i]["description"] for i in v)}
    by_server = defaultdict(list)
    for g in sorted(esc):
        by_server[g.split("::")[0]].append(g)
    chosen, per_pub = [], defaultdict(int)
    servers = sorted(by_server)
    G.rng.shuffle(servers)
    for s in servers:
        gs = by_server[s]
        G.rng.shuffle(gs)
        pub = s.split("/")[0]
        take = gs[:min(G.PER_SERVER, G.PER_PUBLISHER - per_pub[pub])]
        per_pub[pub] += len(take)
        chosen += take
    G.rng.shuffle(chosen)
    return chosen[:limit]

if __name__ == "__main__":
    cat = jload(PROC / "catalog.json")
    by_srv = defaultdict(list)
    for i, t in enumerate(cat):
        by_srv[t["server"]].append(i)
    gold_srv = sorted({g.split("::")[0] for g in chosen_groups(cat, 700)})
    pool = [i for s in gold_srv for i in by_srv[s]]
    others = sorted(set(by_srv) - set(gold_srv))
    random.Random(7).shuffle(others)
    for s in others:
        if len(pool) >= POOL:
            break
        pool += by_srv[s]
    jdump(sorted(pool), PROC / "pool.json")
    print("gold servers", len(gold_srv), "gold-server tools", sum(len(by_srv[s]) for s in gold_srv), "pool", len(pool))
