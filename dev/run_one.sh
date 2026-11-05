#!/bin/bash
cd /workspace/work/shoe-cg
test -x ~/.npm-global/bin/codex || bash dev/setup_env.sh > /workspace/work/setup_env.log 2>&1
echo 0 > dev/codex_pause_until; bash dev/run_task.sh "$1" > /workspace/work/codex_$(basename $1 .md).log 2>&1
echo 9999999999 > dev/codex_pause_until; echo "chunk $1 done"; tail -c 900 /workspace/work/codex_$(basename $1 .md).log
