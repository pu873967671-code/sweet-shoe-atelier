#!/bin/bash
# Re-publish the latest committed build to the playable preview (needs shell credentials github).
set -e
cd /workspace/work/shoe-cg
rm -rf /tmp/pv /tmp/pvdist; git worktree prune; mkdir -p /tmp/pv /tmp/pv/dist; git archive ${REV:-HEAD} index.html style.css game.js js assets vendor smoke-test.js dev/package.py | tar -x -C /tmp/pv
(cd /tmp/pv && python3 dev/package.py)
mkdir /tmp/pvdist && cd /tmp/pvdist && unzip -q /tmp/pv/dist/sweet-shoe-atelier-crazygames.zip
python3 /workspace/work/shoe-cg/dev/publish_preview.py
