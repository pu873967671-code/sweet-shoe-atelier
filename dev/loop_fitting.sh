#!/bin/bash
# Run up to 3 Codex chunks until dev/fitting_accept.json accepted=true
cd /workspace/work/shoe-cg
for i in 1 2 3; do
  if python3 -c "import json,sys;sys.exit(0 if json.load(open('dev/fitting_accept.json')).get('accepted') and json.load(open('dev/shoe_accept.json')).get('accepted') else 1)" 2>/dev/null; then echo "ACCEPTED after $((i-1))"; exit 0; fi
  bash dev/run_codex.sh "LOOP $i/3 — 按 dev/REVIEW.md Supervisor 00:14 + 00:20：用渲染→亲自看截图→批评写入 dev/FITTING_LOOP.md→修复 的内循环修 3D 试穿脚部，并同样闭环精修 shoe3d 鞋模（Supervisor 00:22，严格更新 dev/shoe_accept.json）；可改用 dev/asset_candidates 的 VRoid CC0 模型（裁剪为腿部，包体<20MiB）；严格更新 dev/fitting_accept.json；不行就降级为仅鞋展示。结束前跑 node --check、smoke、打包。"
  git add -A >/dev/null; git commit -qm "fitting loop $i" || true
done
cat dev/fitting_accept.json 2>/dev/null
