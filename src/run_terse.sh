#!/bin/bash
# Robustness add-on: terse rewrites of the validated requests, then the key runs again.
set -u
cd "$(dirname "$0")"
PY="nice -n 15 ../.venv/bin/python"
L=../docs/log
unload() { for m in $(ollama ps | awk 'NR>1{print $1}'); do ollama stop $m; done; }
step() { unload; echo "[$(date '+%F %T')] $*" | tee -a $L/run_terse.log; }
step "terse rewrites";            $PY gen_terse.py > $L/run_gen_terse.log 2>&1
export QSET=terse
step "terse embeddings";          $PY embed_all.py queries minilm bgebase qwen3emb > $L/run_embed_terse.log 2>&1
step "terse retrieval";           $PY retrieval_eval.py > $L/run_retrieval_terse.log 2>&1
for M in qwen3.5:latest qwen3:1.7b; do
  step "terse intents $M";        $PY intent.py $M > $L/run_intent_terse.log 2>&1
  for V in plain sibling; do
    step "terse select $V $M";    $PY select_eval.py $V 0 qwen3emb $M > $L/run_sel_terse_${V}.log 2>&1
  done
done
step "terse guard on retrieval";  $PY guard_retrieval.py qwen3.5:latest > $L/run_guard_retr_terse.log 2>&1
unset QSET
step "references";                $PY analyze.py --missing > $L/run_missing.log 2>&1 && $PY ref_profile.py fill >> $L/run_ref_fill.log 2>&1
step "guard on retrieval";        $PY guard_retrieval.py qwen3.5:latest > $L/run_guard_retr.log 2>&1
step "analyze";                   $PY analyze.py > $L/run_analyze.log 2>&1
step "done"
