#!/bin/bash
# usage: dev/run_codex.sh "<extra focus text>"   (run from anywhere; chunk hard-capped at 17 min)
cd /workspace/work/shoe-cg
/workspace/work/shoe-cg/dev/setup_env.sh >/dev/null 2>&1
LEDGER=dev/codex_ledger.csv; [ -f $LEDGER ] || echo "start_epoch,end_epoch,minutes,exit,focus" > $LEDGER
# USER 2026-10-27 15:53: keep the 16:34 CST quota reset. Windows 16:34/21:34/02:34 run; no Codex 2026-10-28 07:34-11:34 CST so the 11:34 window resets at 16:34.
NOW=$(date +%s); G0=$(date -d "2026-10-28 07:34 +0800" +%s); G1=$(date -d "2026-10-28 11:34 +0800" +%s)
if [ $NOW -ge $G0 ] && [ $NOW -lt $G1 ]; then echo $G1 > dev/codex_pause_until; echo "PAUSED_UNTIL $(date -d @$G1) (quota anchor gap)"; exit 4; fi
# pause file: both Plus accounts hit 5h limit 2026-10-24 23:24
if [ -f dev/codex_pause_until ] && [ $(date +%s) -lt $(cat dev/codex_pause_until) ]; then echo "PAUSED_UNTIL $(date -d @$(cat dev/codex_pause_until))"; exit 4; fi
# window follows the account reset: no minute cap; a usage-limit error pauses until window start + 5h
USED=$(awk -F, -v now=$(date +%s) 'NR>1 && $2>now-18000 {s+=$3} END{printf "%d", s}' $LEDGER)
if [ "$USED" -ge 100000 ]; then echo "WINDOW_FULL used=${USED}min"; exit 3; fi
FOCUS="$1"
PROMPT="You are the lead developer of the browser game in this folder (Sweet Shoe Atelier, for CrazyGames). Read dev/GDD.md, dev/ROADMAP.md, dev/REVIEW.md (fix those first) and dev/PROGRESS.md, then continue the work. You have about 15 minutes in this session: pick a coherent slice, implement it to a high, polished standard (reference quality: Travel Town / Merge Mansion), test it (node --check every JS file; node smoke-test.js; run python3 qa/screenshot.py when UI changed and look at the screenshots), and BEFORE time runs out update dev/PROGRESS.md with done / in-progress / next steps / known bugs. Never leave the game broken. Assets are in assets/ (see assets/MANIFEST.md). Do not use external CDNs. Focus for this session: ${FOCUS:-continue the roadmap in order}"
S=$(date +%s)
WS=$(cat dev/codex_window_start 2>/dev/null || echo 0); if [ $S -gt $((WS+18000)) ]; then echo $S > dev/codex_window_start; WS=$S; fi
timeout 1020 ~/.npm-global/bin/codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "$PROMPT" > dev/logs/codex_$S.log 2>&1
RC=$?
git add -A >/dev/null 2>&1; git -c user.email=a@b -c user.name=codex commit -qm "codex chunk $S: ${FOCUS:0:50}" >/dev/null 2>&1
E=$(date +%s)
echo "$S,$E,$(( (E-S+59)/60 )),$RC,\"${FOCUS:0:60}\"" >> $LEDGER
TOK=$(grep -i -A1 "tokens used" dev/logs/codex_$S.log | tail -1 | tr -d ", "); [ -f dev/codex_tokens.csv ] || echo "start_epoch,tokens" > dev/codex_tokens.csv; echo "$S,${TOK:-0}" >> dev/codex_tokens.csv
echo "exit=$RC tokens=${TOK:-0} minutes=$(( (E-S)/60 )) used_window=$((USED + (E-S)/60))"
tail -c 1500 dev/logs/codex_$S.log
if grep -qiE "(error|stream|hit your).{0,80}(usage limit|429|too many requests|insufficient_quota)" dev/logs/codex_$S.log; then
  # Codex prints "try again at 9:54 PM" in the SANDBOX clock (UTC), not CST.
  T=$(grep -oiE "try again at [0-9]{1,2}:[0-9]{2} ?[AP]M" dev/logs/codex_$S.log | tail -1 | sed -E 's/try again at //I')
  if [ -n "$T" ]; then P=$(TZ=UTC date -d "$T" +%s); [ $P -le $E ] && P=$((P+86400)); P=$((P+120)); else P=$((WS+18000+120)); fi
  echo $P > dev/codex_pause_until; echo "LIMIT_HIT paused until $(TZ=Asia/Shanghai date -d @$P) CST"; fi
