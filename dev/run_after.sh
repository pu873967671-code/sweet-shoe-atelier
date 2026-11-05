#!/bin/bash
cd /workspace/work/shoe-cg
while pgrep -f "codex exec" >/dev/null || pgrep -f "run_task.sh" >/dev/null; do sleep 20; done
bash dev/run_one.sh "$1"
