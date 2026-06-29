#!/usr/bin/env bash
# setup-memory.sh — Bootstrap LLM long-term memory on a new macOS machine
#
# Run once per machine under the ijosh-ch GitHub account:
#   bash lab-automation/setup-memory.sh
#
# The lab long-term memory is a per-user PostgreSQL store managed by the
# llm-skill-ltm repo (https://github.com/bmw-ece-ntust/llm-skill-ltm). That repo
# installs the `memory` skill into ~/.claude/skills and wires the SessionStart
# activity hook, so it works in both Claude Code and Cowork. This script only
# writes the global Claude/Copilot instruction files and base settings, then
# delegates the actual LTM install to llm-skill-ltm.

set -euo pipefail

LTM_REPO_URL="https://github.com/bmw-ece-ntust/llm-skill-ltm.git"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Preferences source. The canonical lab prefs live in bmw-ece-ntust/llm-prefs; when
# that repo is available locally (LAB_PREFS_FILE points at its CLAUDE.md), use it.
# Otherwise fall back to the mirror committed in this repo.
LAB_PREFS_FILE="${LAB_PREFS_FILE:-$REPO_DIR/lab-automation/global-claude.md}"

# When the one-touch orchestrator (deploy-lab-llm.sh) has already run the LTM setup,
# set LAB_DEPLOY_SKIP_LTM=1 so this script does only the prefs + base settings.
LAB_DEPLOY_SKIP_LTM="${LAB_DEPLOY_SKIP_LTM:-0}"

echo "=== BMW Lab LLM Memory Setup (PostgreSQL) ==="
echo

# ── 1. ~/.claude/settings.json (permissions + attribution; no MCP needed) ──────
mkdir -p "$HOME/.claude"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
[ -f "$CLAUDE_SETTINGS" ] || echo '{}' > "$CLAUDE_SETTINGS"
python3 - "$CLAUDE_SETTINGS" <<'PYEOF'
import json, sys
path = sys.argv[1]
with open(path) as f:
    cfg = json.load(f)
cfg["permissions"] = {"defaultMode": "bypassPermissions"}
cfg["skipDangerousModePermissionPrompt"] = True
cfg["attribution"] = {"commit": "", "pr": ""}
# Remove any retired MySQL memory MCP entry.
cfg.get("mcpServers", {}).pop("mysql-memory", None)
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
print("✓ ~/.claude/settings.json updated")
PYEOF

# ── 2. Global Claude + Copilot instruction files ──────────────────────────────
# Claude Code and Cowork read user-global memory from ~/.claude/CLAUDE.md
# (NOT ~/CLAUDE.md at the home root, which is never loaded). These are the lab AI
# preferences, sourced from bmw-ece-ntust/llm-prefs when available.
if [ ! -f "$LAB_PREFS_FILE" ]; then
  echo "⚠ prefs source not found: $LAB_PREFS_FILE — using repo mirror"
  LAB_PREFS_FILE="$REPO_DIR/lab-automation/global-claude.md"
fi
# Write both the user-memory file (cwd-independent, Cowork-safe) and the home-root
# copy (picked up by Claude Code's directory-tree walk for projects under $HOME).
cp "$LAB_PREFS_FILE" "$HOME/.claude/CLAUDE.md"
cp "$LAB_PREFS_FILE" "$HOME/CLAUDE.md"
echo "✓ wrote ~/.claude/CLAUDE.md (user memory) + ~/CLAUDE.md (home-tree fallback) from ${LAB_PREFS_FILE#$HOME/}"
mkdir -p "$HOME/.copilot"
cp "$REPO_DIR/lab-automation/global-copilot.md" "$HOME/.copilot/instructions.md"
echo "✓ ~/.copilot/instructions.md written"

# ── 3. Install the PostgreSQL LTM (llm-skill-ltm) ─────────────────────────────
if [ "$LAB_DEPLOY_SKIP_LTM" = "1" ]; then
  echo
  echo "── Skipping LTM install (LAB_DEPLOY_SKIP_LTM=1; orchestrator already ran it) ──"
else
  echo
  echo "── Installing the PostgreSQL LTM via llm-skill-ltm ──"
  LTM_DIR="${LTM_HOME:-$HOME/Documents/GitHub/llm-skill-ltm}"
  if [ ! -d "$LTM_DIR/.git" ]; then
    echo "Cloning $LTM_REPO_URL -> $LTM_DIR"
    git clone "$LTM_REPO_URL" "$LTM_DIR"
  fi
  if [ -f "$LTM_DIR/.env" ]; then
    echo "Running llm-skill-ltm setup (installs the memory skill + SessionStart hook)…"
    ( cd "$LTM_DIR" && bash setup.sh )
  else
    echo "⚠ $LTM_DIR/.env not found."
    echo "  Next: cp $LTM_DIR/.env.example $LTM_DIR/.env, fill in your Vaultwarden item + SSH user,"
    echo "        then run:  ( cd \"$LTM_DIR\" && bash setup.sh )"
  fi
fi

echo
echo "Done. The memory skill records per-repo activity automatically (Claude Code + Cowork)."
