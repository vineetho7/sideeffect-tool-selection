"""Harvest tool schemas from registry servers that expose a public streamable-HTTP endpoint.

Only `initialize` and `tools/list` are sent; no tool is ever invoked. Servers whose
registry entry declares a required header (API key) are skipped.
"""
import json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from common import RAW, jload

UA = "sideeffect-tool-study/0.1 (research; tools/list only)"
PROTO = "2025-06-18"


def _rpc(url, payload, session=None, timeout=12):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
         "User-Agent": UA, "MCP-Protocol-Version": PROTO}
    if session:
        h["Mcp-Session-Id"] = session
    req = urllib.request.Request(url, json.dumps(payload).encode(), h)
    with urllib.request.urlopen(req, timeout=timeout) as f:
        sid = f.headers.get("Mcp-Session-Id") or session
        body = f.read(8_000_000).decode("utf-8", "replace")
        ctype = f.headers.get("Content-Type", "")
    if not body.strip():
        return None, sid
    if "text/event-stream" in ctype:
        # take the last JSON-RPC message carrying our id
        msg = None
        for line in body.splitlines():
            if line.startswith("data:"):
                try:
                    d = json.loads(line[5:].strip())
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("id") == payload.get("id"):
                    msg = d
        return msg, sid
    return json.loads(body), sid


def harvest(url):
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTO, "capabilities": {},
                       "clientInfo": {"name": "sideeffect-tool-study", "version": "0.1"}}}
    r, sid = _rpc(url, init)
    if not r or "result" not in r:
        raise RuntimeError(f"init: {str(r)[:200]}")
    info = r["result"].get("serverInfo", {})
    try:
        _rpc(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    except Exception:
        pass
    tools, cursor = [], None
    for i in range(20):
        p = {"jsonrpc": "2.0", "id": 2 + i, "method": "tools/list", "params": {"cursor": cursor} if cursor else {}}
        r, sid = _rpc(url, p, sid)
        if not r or "result" not in r:
            raise RuntimeError(f"tools/list: {str(r)[:200]}")
        tools += r["result"].get("tools", [])
        cursor = r["result"].get("nextCursor")
        if not cursor:
            break
    return info, tools


def candidates(reg):
    out = []
    for e in reg:
        s = e["server"]
        for rm in s.get("remotes", []) or []:
            if rm.get("type") != "streamable-http" or "{" in rm.get("url", ""):
                continue
            if any(h.get("isRequired") for h in rm.get("headers", []) or []):
                continue
            out.append((s["name"], rm["url"], s.get("description", "")))
            break
    return out


def run(item):
    name, url, desc = item
    try:
        info, tools = harvest(url)
        return {"server": name, "url": url, "description": desc, "serverInfo": info,
                "ok": True, "tools": tools}
    except Exception as e:
        return {"server": name, "url": url, "ok": False, "error": f"{type(e).__name__}: {e}"[:300]}


if __name__ == "__main__":
    reg = jload(RAW / "registry.json")
    cand = candidates(reg)
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if lim:
        cand = cand[:lim]
    import random
    random.Random(7).shuffle(cand)           # spread load across hosts
    print("candidates", len(cand), flush=True)
    res = []
    with ThreadPoolExecutor(128) as ex:
        futs = [ex.submit(run, c) for c in cand]
        for i, f in enumerate(as_completed(futs)):
            res.append(f.result())
            if (i + 1) % 200 == 0:
                ok = sum(r["ok"] for r in res)
                print(f"{i+1}/{len(cand)} ok={ok} tools={sum(len(r.get('tools', [])) for r in res)}", flush=True)
            if (i + 1) % 2000 == 0:
                json.dump(res, open(RAW / "remote_tools.partial.json", "w"))
    json.dump(res, open(RAW / "remote_tools.json", "w"))
    ok = [r for r in res if r["ok"]]
    print("done ok", len(ok), "of", len(res), "tools", sum(len(r["tools"]) for r in ok))
