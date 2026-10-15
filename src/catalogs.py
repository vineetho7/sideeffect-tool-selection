"""Per-query tool catalogs that mimic an agent with several MCP servers connected.

The gold tool's whole server is always installed (so its siblings are present, as in real use);
other pool servers are added in a seeded random order until the catalog reaches N tools.
"""
import random
from collections import defaultdict

SIZES = [200, 1000, 5000, 0]          # 0 = whole study pool


class Catalogs:
    def __init__(self, cat, pool):
        self.by_server = defaultdict(list)
        for i in pool:
            self.by_server[cat[i]["server"]].append(i)
        self.servers = sorted(self.by_server)
        self.pool = list(pool)
        self.cat = cat

    def subset(self, qid, gold_idx, n):
        if n == 0 or n >= len(self.pool):
            return self.pool
        own = self.cat[gold_idx]["server"]
        idx = list(self.by_server[own])
        others = [s for s in self.servers if s != own]
        random.Random(f"7:{qid}").shuffle(others)
        for s in others:
            if len(idx) >= n:
                break
            idx += self.by_server[s][: n - len(idx)]
        return idx
