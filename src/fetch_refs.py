"""Verify arXiv references against the arXiv API and write paper/refs_arxiv.bib + a JSON record."""
import json, re, time, urllib.request
import xml.etree.ElementTree as ET
from common import ROOT, RES, jdump

IDS = {
    "toolret": "2503.01763", "toolrerank": "2403.06551", "gorilla": "2305.15334",
    "toolllm": "2307.16789", "ragmcp": "2505.03275", "mcpzero": "2506.01056",
    "scalemcp": "2505.06416", "livemcpbench": "2508.01780", "mcpbench": "2508.20453",
    "mcpverse": "2508.16260", "mcpatlas": "2602.00933", "smelly": "2602.14878",
    "docs2desc": "2602.18914", "randomdraw": "2609.10962", "mcpapps": "2607.25635",
    "rest2mcp": "2507.16044", "semdisc": "2603.20313", "toolmisuse": "2604.01508",
    "boundary": "2609.15397", "toollery": "2609.22218", "patool": "2510.07248",
    "hnsw": "1603.09320", "acorn": "2403.04871", "qwen3emb": "2506.05176",
    "toolemu": "2309.15817", "bge": "2309.07597", "sbert": "1908.10084",
}
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch(ids):
    url = "http://export.arxiv.org/api/query?id_list=" + ",".join(ids) + "&max_results=100"
    with urllib.request.urlopen(url, timeout=60) as f:
        root = ET.fromstring(f.read())
    out = {}
    for e in root.findall("a:entry", NS):
        aid = re.sub(r"v\d+$", "", e.find("a:id", NS).text.rsplit("/", 1)[-1])
        out[aid] = {"title": re.sub(r"\s+", " ", e.find("a:title", NS).text).strip(),
                    "authors": [a.find("a:name", NS).text for a in e.findall("a:author", NS)],
                    "year": e.find("a:published", NS).text[:4]}
    return out


if __name__ == "__main__":
    meta = fetch(list(IDS.values()))
    bib, rec = [], {}
    for key, aid in IDS.items():
        m = meta.get(aid)
        rec[key] = {"arxiv": aid, **(m or {"error": "not found"})}
        if not m:
            print("MISSING", key, aid)
            continue
        au = " and ".join(m["authors"][:6]) + (" and others" if len(m["authors"]) > 6 else "")
        bib.append(f"@article{{{key},\n  title={{{{{m['title']}}}}},\n  author={{{au}}},\n"
                   f"  journal={{arXiv preprint arXiv:{aid}}},\n  year={{{m['year']}}}\n}}\n")
        print(f"{key:12s} {aid} {m['year']} {m['title'][:90]}")
    (ROOT / "paper").mkdir(exist_ok=True)
    open(ROOT / "paper" / "refs_arxiv.bib", "w").write("\n".join(bib))
    jdump(rec, RES / "ref_verification.json")
