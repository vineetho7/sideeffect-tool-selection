"""Normalise harvested MCP tools into one catalog with operation profiles and sibling groups."""
import hashlib, json, random, sys
from collections import Counter, defaultdict
from common import RAW, PROC, jload, jdump
from profile_tools import profile, split_name

PUB_CAP = 25


def params_of(schema):
    props = (schema or {}).get("properties") or {}
    req = set((schema or {}).get("required") or [])
    out = []
    for k, v in list(props.items())[:30]:
        v = v if isinstance(v, dict) else {}
        out.append({"name": k, "type": v.get("type"), "required": k in req,
                    "description": (v.get("description") or "")[:160]})
    return out


def load_sources():
    servers = []
    for r in jload(RAW / "remote_tools.json"):
        if r.get("ok") and r.get("tools"):
            servers.append({"server": r["server"], "source": "registry-remote", "tools": r["tools"]})
    extra = RAW / "extra_servers.json"
    if extra.exists():
        servers += jload(extra)
    return servers


if __name__ == "__main__":
    servers = load_sources()
    random.Random(7).shuffle(servers)
    seen, cat, dup, capped, per_pub = set(), [], 0, 0, Counter()
    for s in servers:
        pub = s["server"].split("/")[0]
        if per_pub[pub] >= PUB_CAP:          # mass-generated families would dominate the corpus
            capped += 1
            continue
        tools = [t for t in s["tools"] if isinstance(t, dict) and t.get("name")]
        sig = hashlib.sha1(json.dumps(sorted((t["name"], (t.get("description") or "")[:200])
                                             for t in tools)).encode()).hexdigest()
        if sig in seen:                      # same server published under several names
            dup += 1
            continue
        seen.add(sig)
        per_pub[pub] += 1
        stoks = set(split_name(s["server"].split("/")[-1])) - {"mcp", "server"}
        for t in tools:
            p = profile(t, stoks)
            cat.append({"id": f"{s['server']}::{t['name']}", "server": s["server"], "source": s["source"],
                        "publisher": s["server"].split("/")[0],
                        "name": t["name"], "description": (t.get("description") or "").strip()[:1500],
                        "params": params_of(t.get("inputSchema")), "annotations": t.get("annotations") or {},
                        **p})
    # sibling groups: same server + same resource, >=2 tools, >=2 distinct severities
    groups = defaultdict(list)
    for i, t in enumerate(cat):
        if t["resource"] and t["sev"] is not None:
            groups[(t["server"], t["resource"])].append(i)
    sib = {}
    for k, idx in groups.items():
        sevs = {cat[i]["sev"] for i in idx}
        if len(idx) >= 2 and len(sevs) >= 2:
            gid = f"{k[0]}::{k[1]}"
            sib[gid] = idx
            for i in idx:
                cat[i]["group"] = gid
    jdump(cat, PROC / "catalog.json")
    jdump(sib, PROC / "sibling_groups.json")

    n = len(cat)
    st = {
        "servers_unique": len(seen), "servers_duplicate_skipped": dup,
        "servers_publisher_capped": capped, "publisher_cap": PUB_CAP, "tools": n,
        "tools_with_description": sum(bool(t["description"]) for t in cat),
        "op_from_name": sum(t["src"] == "name" for t in cat),
        "op_from_description": sum(t["src"] == "description" for t in cat),
        "op_unknown": sum(t["src"] == "none" for t in cat),
        "op_dist": Counter(t["op"] for t in cat),
        "annotated_any": sum(bool(t["annotations"]) for t in cat),
        "annotated_readonly_hint": sum("readOnlyHint" in t["annotations"] for t in cat),
        "annotated_destructive_hint": sum("destructiveHint" in t["annotations"] for t in cat),
        "sibling_groups": len(sib),
        "tools_in_sibling_groups": sum(len(v) for v in sib.values()),
        "servers_with_sibling_groups": len({g.split("::")[0] for g in sib}),
        "escalation_capable_groups": sum(1 for v in sib.values()
                                         if any(cat[i]["sev"] == 0 for i in v)
                                         and any(cat[i]["sev"] >= 2 for i in v)),
        "group_size_dist": Counter(min(len(v), 8) for v in sib.values()),
        "publishers": len({t["publisher"] for t in cat}),
        "top_publishers_by_tools": Counter(t["publisher"] for t in cat).most_common(10),
        "sibling_groups_by_publisher_top": Counter(cat[v[0]]["publisher"] for v in sib.values()).most_common(10),
        "top_resources": Counter(g.split("::")[-1] for g in sib).most_common(30),
    }
    st = json.loads(json.dumps(st, default=str))
    jdump(st, PROC / "catalog_stats.json")
    print(json.dumps(st, indent=1))
