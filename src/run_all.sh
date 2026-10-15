#!/bin/bash
# Full experiment chain after gen_queries.py has written data/processed/queries.json.
# Each step logs to docs/log/run_*.log; steps are idempotent where outputs are cached.
set -u
cd "$(dirname "$0")"
PY=../.venv/bin/python
L=../docs/log
unload() { for m in $(ollama ps | awk 'NR>1{print $1}'); do ollama stop $m; done; }
step() { unload; echo "[$(date '+%F %T')] $*" | tee -a $L/run_all.log; }

step "reference profiler audit (gemma3)";   $PY ref_profile.py audit        > $L/run_ref_audit.log 2>&1
step "audit samples";                        $PY audit_sample.py             > $L/run_audit_sample.log 2>&1
step "query embeddings";                     $PY embed_all.py queries minilm bgebase qwen3emb > $L/run_embed_q.log 2>&1
step "reference severities for eval groups"; $PY ref_profile.py fill         > $L/run_ref_fill.log 2>&1
step "retrieval eval (RQ1/RQ2)";             $PY retrieval_eval.py           > $L/run_retrieval.log 2>&1
step "hnsw control";                         $PY hnsw_control.py             > $L/run_hnsw.log 2>&1
step "intents qwen3.5";                      $PY intent.py qwen3.5:latest    > $L/run_intent_qwen.log 2>&1
for N in 1000 0; do
  for V in plain tags sibling native; do
    step "select $V N=$N qwen3.5";           $PY select_eval.py $V $N qwen3emb qwen3.5:latest > $L/run_sel_${V}_${N}_qwen.log 2>&1
  done
done
step "intents gemma3";                       $PY intent.py gemma3:12b        > $L/run_intent_gemma.log 2>&1
for V in plain sibling tags; do
  step "select $V N=0 gemma3";               $PY select_eval.py $V 0 qwen3emb gemma3:12b > $L/run_sel_${V}_0_gemma.log 2>&1
done
step "intents qwen3:1.7b";                  $PY intent.py qwen3:1.7b        > $L/run_intent_small.log 2>&1
for V in plain sibling tags; do
  step "select $V N=0 qwen3:1.7b";           $PY select_eval.py $V 0 qwen3emb qwen3:1.7b > $L/run_sel_${V}_0_small.log 2>&1
done
step "reference severities for predictions"; $PY analyze.py --missing > $L/run_missing.log 2>&1 && $PY ref_profile.py fill >> $L/run_ref_fill.log 2>&1
step "retrieval eval with full references";  $PY retrieval_eval.py           > $L/run_retrieval.log 2>&1
step "analyze";                              $PY analyze.py                  > $L/run_analyze.log 2>&1
step "done"
