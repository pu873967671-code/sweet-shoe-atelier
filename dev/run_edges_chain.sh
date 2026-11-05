#!/bin/bash
# runs the next pending edges-* chunk; records done ones in dev/edges_done
cd /workspace/work/shoe-cg; touch dev/edges_done
for n in a b c fix fix2 d p p2 p3; do grep -qx $n dev/edges_done && continue
  test -x ~/.npm-global/bin/codex || bash dev/setup_env.sh > /workspace/work/setup_env.log 2>&1
  echo 0 > dev/codex_pause_until; bash dev/run_task.sh dev/tasks/$( [ $n = p3 ] && echo edges-p3.md || echo edges-${n%2}.md) > /workspace/work/codex_edges_$n.log 2>&1
  echo 9999999999 > dev/codex_pause_until; echo $n >> dev/edges_done; echo "chunk $n done"; tail -c 600 /workspace/work/codex_edges_$n.log; exit 0; done
echo all done
