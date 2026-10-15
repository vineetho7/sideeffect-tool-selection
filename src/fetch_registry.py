"""Snapshot the official MCP registry (server metadata only; it holds no tool schemas)."""
import json, time, urllib.parse, urllib.request
from common import RAW

URL = "https://registry.modelcontextprotocol.io/v0/servers"


def page(cursor):
    q = {"limit": 100, "version": "latest"}
    if cursor:
        q["cursor"] = cursor
    with urllib.request.urlopen(f"{URL}?{urllib.parse.urlencode(q)}", timeout=60) as f:
        return json.load(f)


if __name__ == "__main__":
    out, cursor = [], None
    while True:
        for attempt in range(5):
            try:
                d = page(cursor)
                break
            except Exception as e:
                print("retry", attempt, e, flush=True)
                time.sleep(2 ** attempt)
        out += d["servers"]
        cursor = d.get("metadata", {}).get("nextCursor")
        if len(out) % 2000 < 100:
            print(len(out), flush=True)
        if not cursor:
            break
    json.dump(out, open(RAW / "registry.json", "w"))
    print("entries", len(out))
