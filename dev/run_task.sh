#!/bin/bash
# usage: dev/run_task.sh dev/tasks/<file>.md   (one 17-min chunk for a specific task file)
cd /workspace/work/shoe-cg
TASK="$1"; LEDGER=dev/codex_ledger.csv
PROMPT="You are the lead developer of the browser game in this folder (Sweet Shoe Atelier). Implement the task in ${TASK} exactly, staying inside its scope and hard constraints. Read dev/PROGRESS.md first; if it has a section for this task, continue from it. You have about 15 minutes in this session: work in coherent steps, run the acceptance tests, and BEFORE time runs out update dev/PROGRESS.md (section '## $(basename $TASK .md)') with done / in-progress / next / known bugs. Never leave the game broken. No external CDNs."
S=$(date +%s)
timeout 1020 ~/.npm-global/bin/codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "$PROMPT" > dev/logs/codex_$S.log 2>&1
RC=$?
git add -A >/dev/null 2>&1; git -c user.email=a@b -c user.name=codex commit -qm "codex chunk $S: $(basename $TASK)" >/dev/null 2>&1
E=$(date +%s); echo "$S,$E,$(( (E-S+59)/60 )),$RC,\"$(basename $TASK)\"" >> $LEDGER
TOK=$(grep -i -A1 "tokens used" dev/logs/codex_$S.log | tail -1 | tr -d ", "); echo "$S,${TOK:-0}" >> dev/codex_tokens.csv
echo "exit=$RC tokens=${TOK:-0} minutes=$(( (E-S)/60 ))"; tail -c 2500 dev/logs/codex_$S.log
