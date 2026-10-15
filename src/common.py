"""Shared paths and local-model helpers (ollama on 127.0.0.1:11434)."""
import json, time, urllib.error, urllib.request
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
RES = ROOT / "results"
FIGS = ROOT / "figs"
for p in (RAW, PROC, RES, FIGS):
    p.mkdir(parents=True, exist_ok=True)

# Request set: QSET=terse switches every script to queries_terse.json and suffixed outputs.
import os
QSET = os.environ.get("QSET", "")
QFILE = f"queries_{QSET}.json" if QSET else "queries.json"
SFX = f"_{QSET}" if QSET else ""

OLLAMA = "http://127.0.0.1:11434"
BIG = "qwen3.5:latest"
SMALL = "qwen3:1.7b"


def _post(path, body, timeout=900, tries=5):
    """POST to ollama; retries transient 5xx (e.g. a model failing to load under memory pressure)."""
    for k in range(tries):
        req = urllib.request.Request(OLLAMA + path, json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as f:
                return json.load(f)
        except urllib.error.HTTPError as e:
            if e.code < 500 or k == tries - 1:
                raise
            time.sleep(10 * (k + 1))


def unload(model):
    """Free a model's memory; harmless if it is not loaded."""
    try:
        _post("/api/generate", {"model": model, "keep_alive": 0}, tries=1)
    except urllib.error.URLError:
        pass


def chat(messages, model=BIG, num_predict=64, num_ctx=4096, temperature=0.0, fmt=None):
    body = {"model": model, "messages": messages, "stream": False, "think": False,
            "options": {"num_predict": num_predict, "temperature": temperature,
                        "num_ctx": num_ctx, "top_p": 1.0, "seed": 7}}
    if fmt:
        body["format"] = fmt
    t0 = time.time()
    d = _post("/api/chat", body)
    return {"text": d["message"]["content"], "p_tok": d.get("prompt_eval_count", 0),
            "g_tok": d.get("eval_count", 0), "wall": time.time() - t0}


# HF model id, query prefix, document prefix (each model's documented retrieval prompts).
EMBEDDERS = {
    "qwen3emb": ("Qwen/Qwen3-Embedding-0.6B",
                 "Instruct: Given a user request, retrieve the software tool that fulfils it\nQuery: ", ""),
    "bgebase": ("BAAI/bge-base-en-v1.5", "Represent this sentence for searching relevant passages: ", ""),
    "minilm": ("sentence-transformers/all-MiniLM-L6-v2", "", ""),
}
_ST = {}


def embed(texts, embedder, kind, batch=64):
    """kind: 'query' | 'doc'. sentence-transformers on Apple MPS; L2-normalised float32."""
    from sentence_transformers import SentenceTransformer
    name, qp, dp = EMBEDDERS[embedder]
    if embedder not in _ST:
        m = SentenceTransformer(name, device="mps", trust_remote_code=True)
        m.max_seq_length = 256
        _ST[embedder] = m
    pre = qp if kind == "query" else dp
    a = _ST[embedder].encode([pre + t for t in texts], batch_size=batch, normalize_embeddings=True,
                             show_progress_bar=False, convert_to_numpy=True)
    return a.astype(np.float32)


def jload(p):
    return json.load(open(p))


def jdump(o, p):
    json.dump(o, open(p, "w"), indent=1)
