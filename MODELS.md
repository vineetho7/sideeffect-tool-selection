# Model versions used

| role | model | version |
|---|---|---|
| request generator, main selector, intent profiler | `qwen3.5:latest` (Ollama, 9.7B, Q4_K_M) | digest `6488c96fa5fa` |
| validator, reference severity, second selector | `gemma3:12b` (Ollama, 12.2B, Q4_K_M) | digest `f4031aab637d` |
| small selector | `qwen3:1.7b` (Ollama) | digest `8f68893c685c` |
| embedder | `Qwen/Qwen3-Embedding-0.6B` (Hugging Face) | revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` |
| embedder | `BAAI/bge-base-en-v1.5` | revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a` |
| embedder | `sentence-transformers/all-MiniLM-L6-v2` | revision `c9745ed1d9f207416be6d2e6f8de32d1f16199bf` |

Runtime: Ollama 0.33.3, Python 3.12.13, packages in `requirements.txt`, Apple M4 Pro (24 GB).
All LLM calls: temperature 0 (generator 0.7), seed 7, context 8192 for the main runs and 4096
for the terse run (prompts are under 2k tokens, so outputs do not depend on it).
Ollama tags are mutable: check `ollama list` shows the digests above before rerunning.
