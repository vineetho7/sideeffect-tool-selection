#!/bin/bash
# Phi-4 14B selector (plain + sibling), then references and analysis. One model at a time.
set -u
cd "$(dirname "$0")"
PY="nice -n 15 ../.venv/bin/python"
L=../docs/log
unload() { for m in $(ollama ps | awk 'NR>1{print $1}'); do ollama stop $m; done; }
step() { unload; echo "[$(date '+%F %T')] $*" | tee -a $L/run_extra.log; }
step "intents phi4";     $PY intent.py phi4:14b > $L/run_intent_phi4.log 2>&1
for V in plain sibling; do
  step "select $V phi4"; $PY select_eval.py $V 0 qwen3emb phi4:14b > $L/run_sel_${V}_0_phi4.log 2>&1
done
step "references";       $PY analyze.py --missing > $L/run_missing.log 2>&1 && $PY ref_profile.py fill >> $L/run_ref_fill.log 2>&1
step "analyze";          $PY analyze.py > $L/run_analyze.log 2>&1
unload
step "done"
