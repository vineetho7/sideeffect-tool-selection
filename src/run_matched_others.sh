#!/bin/bash
# Count-matched baseline for Qwen3-1.7B, Gemma3-12B and Phi-4 at 30k, one model at a time;
# a model starts only if enough memory is free.
set -u
cd "$(dirname "$0")"
PY="nice -n 15 ../.venv/bin/python"
L=../docs/log
unload() { for m in $(ollama ps | awk 'NR>1{print $1}'); do ollama stop $m; done; }
step() { unload; echo "[$(date '+%F %T')] $*" | tee -a $L/run_matched_others.log; }
# Memory guard: pause the selector client (not the model) below 15% free memory, resume above 25%.
guard() { while sleep 5; do f=$(memory_pressure | awk '/free percentage/{print $5+0}')
  p=$(pgrep -f select_eval.py); [ -z "$p" ] && continue
  if [ "$f" -lt 10 ]; then kill $p; unload; echo "[$(date '+%T')] stopped at $f% free (checkpoint kept)" >> $L/run_matched_others.log; kill $$
  elif [ "$f" -lt 15 ]; then kill -STOP $p; echo "[$(date '+%T')] paused at $f% free" >> $L/run_matched_others.log
  elif [ "$f" -gt 25 ]; then kill -CONT $p 2>/dev/null; fi; done; }
guard & GUARD=$!; trap 'kill $GUARD 2>/dev/null' EXIT
free() { memory_pressure | awk '/free percentage/{print $5+0}'; }
for M in qwen3:1.7b:30 gemma3:12b:50 phi4:14b:50; do      # model:minimum free % to start
  need=${M##*:}; M=${M%:*}
  [ -f ../results/sel_matched_n0_qwen3emb_${M/:/-}_k5.json ] && continue
  unload
  if [ "$(free)" -lt "$need" ]; then echo "[$(date '+%F %T')] skip $M: $(free)% free < $need%" >> $L/run_matched_others.log; continue; fi
  step "select matched-k $M"; $PY select_eval.py matched 0 qwen3emb $M > $L/run_sel_matched_0_${M%%:*}.log 2>&1
done
step "references";       $PY analyze.py --missing > $L/run_missing.log 2>&1 && $PY ref_profile.py fill >> $L/run_ref_fill.log 2>&1
unload
step "done"
