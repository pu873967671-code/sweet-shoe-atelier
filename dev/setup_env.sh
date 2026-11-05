#!/bin/bash
# Idempotent: sandbox home may be reset between sessions.
set -e
if [ ! -x ~/.npm-global/bin/codex ]; then mkdir -p ~/.npm-global && npm config set prefix ~/.npm-global >/dev/null && npm i -g @openai/codex >/tmp/codex-install.log 2>&1; fi
mkdir -p ~/.codex
cat > ~/.codex/config.toml <<'C'
model = "gpt-6.1-sol"
model_provider = "relay"
model_reasoning_effort = "high"
[model_providers.relay]
name = "afgp relay"
base_url = "https://afgp.cc.cd/v1"
env_key = "RELAY_API_KEY"
wire_api = "responses"
C
python3 -c "import playwright" 2>/dev/null || pip install -q playwright >/tmp/pip.log 2>&1
which chromium >/dev/null || (sudo apt-get update >/tmp/apt.log 2>&1 && sudo apt-get install -y chromium >>/tmp/apt.log 2>&1)
~/.npm-global/bin/codex --version
mkdir -p ~/.codex/skills && cp -r /workspace/work/shoe-cg/.agents/skills/impeccable ~/.codex/skills/ 2>/dev/null
