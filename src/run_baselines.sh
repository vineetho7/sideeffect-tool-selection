#!/bin/bash
# Candidate-budget baselines at 30k: plain prompt over Qwen3-Emb top-10, top-15 and matched-k
# (per-request k = the expanded list length; sibling lists average 11.6).
set -u
cd "$(dirname "$0")"
PY="nice -n 15 ../.venv/bin/python"
L=../docs/log
unload() { for m in $(ollama ps | awk 'NR>1{print $1}'); do ollama stop $m; done; }
step() { unload; echo "[$(date '+%F %T')] $*" | tee -a $L/run_baselines.log; }
# Memory guard: pause the selector client (not the model) below 15% free memory, resume above 25%.
guard() { while sleep 5; do f=$(memory_pressure | awk '/free percentage/{print $5+0}')
  p=$(pgrep -f select_eval.py); [ -z "$p" ] && continue
  if [ "$f" -lt 10 ]; then kill $p; unload; echo "[$(date '+%T')] stopped at $f% free (checkpoint kept)" >> $L/run_baselines.log; kill $$
  elif [ "$f" -lt 15 ]; then kill -STOP $p; echo "[$(date '+%T')] paused at $f% free" >> $L/run_baselines.log
  elif [ "$f" -gt 25 ]; then kill -CONT $p 2>/dev/null; fi; done; }
guard & GUARD=$!; trap 'kill $GUARD 2>/dev/null' EXIT
for k in 10 15; do
  step "select plain k$k qwen3.5"; K=$k $PY select_eval.py plain 0 qwen3emb qwen3.5:latest > $L/run_sel_plain_0_k$k.log 2>&1
done
test -f ../results/sel_expand_n0_qwen3emb_qwen3.5-latest_k5.json || { echo "missing expand run" >> $L/run_baselines.log; exit 1; }
step "select matched-k qwen3.5"; $PY select_eval.py matched 0 qwen3emb qwen3.5:latest > $L/run_sel_matched_0.log 2>&1
step "references";       $PY analyze.py --missing > $L/run_missing.log 2>&1 && $PY ref_profile.py fill >> $L/run_ref_fill.log 2>&1
step "analyze";          $PY analyze.py > $L/run_analyze.log 2>&1 && $PY cross_server.py > $L/run_cross_server.log 2>&1 && $PY escalation_precision.py > $L/run_esc_prec.log 2>&1
unload
step "done"
