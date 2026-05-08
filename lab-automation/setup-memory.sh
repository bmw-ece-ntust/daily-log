#!/usr/bin/env bash
# setup-memory.sh — Bootstrap LLM long-term memory on a new macOS machine
#
# Run once per machine under the ijosh-ch GitHub account:
#   bash lab-automation/setup-memory.sh
#
# What this does:
#   1. Writes ~/.claude/settings.json  (Claude Code MCP + permissions)
#   2. Writes ~/CLAUDE.md              (global Claude memory instructions)
#   3. Creates ~/.copilot/instructions.md (global Copilot instructions)
#   4. Prints the VS Code settings.json snippet to add manually

set -euo pipefail

MYSQL_HOST="140.118.122.119"
MYSQL_PORT="3306"
MYSQL_USER="llmuser"
MYSQL_DB="llm_memory"

echo "=== BMW Lab LLM Memory Setup ==="
echo
read -rsp "MySQL password for ${MYSQL_USER}@${MYSQL_HOST}: " MYSQL_PASS
echo
echo

# ── verify connectivity ───────────────────────────────────────────────────────
nc -z -w 5 "$MYSQL_HOST" "$MYSQL_PORT" \
  && echo "✓ MySQL reachable at ${MYSQL_HOST}:${MYSQL_PORT}" \
  || { echo "⚠ Cannot reach ${MYSQL_HOST}:${MYSQL_PORT} — check network"; exit 1; }

# ── 1. ~/.claude/settings.json ────────────────────────────────────────────────
mkdir -p "$HOME/.claude"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

if [ -f "$CLAUDE_SETTINGS" ]; then
  python3 - <<PYEOF
import json
path = "$CLAUDE_SETTINGS"
with open(path) as f:
    cfg = json.load(f)
cfg["permissions"] = {"defaultMode": "bypassPermissions"}
cfg["skipDangerousModePermissionPrompt"] = True
cfg["attribution"] = {"commit": "", "pr": ""}
cfg.setdefault("mcpServers", {})["mysql-memory"] = {
    "command": "npx",
    "args": ["-y", "@benborla29/mcp-server-mysql"],
    "env": {
        "MYSQL_HOST": "$MYSQL_HOST",
        "MYSQL_PORT": "$MYSQL_PORT",
        "MYSQL_USER": "$MYSQL_USER",
        "MYSQL_PASS": "$MYSQL_PASS",
        "MYSQL_DB": "$MYSQL_DB"
    }
}
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
print("✓ ~/.claude/settings.json updated")
PYEOF
else
  cat > "$CLAUDE_SETTINGS" <<JSON_EOF
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "skipDangerousModePermissionPrompt": true,
  "attribution": {
    "commit": "",
    "pr": ""
  },
  "mcpServers": {
    "mysql-memory": {
      "command": "npx",
      "args": ["-y", "@benborla29/mcp-server-mysql"],
      "env": {
        "MYSQL_HOST": "$MYSQL_HOST",
        "MYSQL_PORT": "$MYSQL_PORT",
        "MYSQL_USER": "$MYSQL_USER",
        "MYSQL_PASS": "$MYSQL_PASS",
        "MYSQL_DB": "$MYSQL_DB"
      }
    }
  }
}
JSON_EOF
  echo "✓ ~/.claude/settings.json created"
fi

# ── 2. VS Code mcp.json (Copilot MCP — user-level) ───────────────────────────
VSCODE_USER_DIR="$HOME/Library/Application Support/Code/User"
MCP_JSON="$VSCODE_USER_DIR/mcp.json"
if [ -d "$VSCODE_USER_DIR" ]; then
  cat > "$MCP_JSON" <<MCP_EOF
{
  "servers": {
    "mysql-memory": {
      "command": "npx",
      "args": ["-y", "@benborla29/mcp-server-mysql"],
      "env": {
        "MYSQL_HOST": "$MYSQL_HOST",
        "MYSQL_PORT": "$MYSQL_PORT",
        "MYSQL_USER": "$MYSQL_USER",
        "MYSQL_PASS": "$MYSQL_PASS",
        "MYSQL_DB": "$MYSQL_DB"
      },
      "type": "stdio"
    }
  },
  "inputs": []
}
MCP_EOF
  echo "✓ VS Code mcp.json written"
else
  echo "⚠ VS Code not found at $VSCODE_USER_DIR — skip mcp.json"
fi

# ── 3. ~/CLAUDE.md ────────────────────────────────────────────────────────────
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cp "$REPO_DIR/lab-automation/global-claude.md" "$HOME/CLAUDE.md"
echo "✓ ~/CLAUDE.md written"

# ── 3. ~/.copilot/instructions.md ─────────────────────────────────────────────
mkdir -p "$HOME/.copilot"
cp "$REPO_DIR/lab-automation/global-copilot.md" "$HOME/.copilot/instructions.md"
echo "✓ ~/.copilot/instructions.md written"

# ── 4. VS Code settings snippet ───────────────────────────────────────────────
echo
echo "══════════════════════════════════════════════════════════════"
echo " Paste this block into VS Code user settings.json"
echo " Cmd+Shift+P → Preferences: Open User Settings (JSON)"
echo "══════════════════════════════════════════════════════════════"
cat <<VSCODE_EOF

  "mcp": {
    "servers": {
      "mysql-memory": {
        "command": "npx",
        "args": ["-y", "@benborla29/mcp-server-mysql"],
        "env": {
          "MYSQL_HOST": "$MYSQL_HOST",
          "MYSQL_PORT": "$MYSQL_PORT",
          "MYSQL_USER": "$MYSQL_USER",
          "MYSQL_PASS": "$MYSQL_PASS",
          "MYSQL_DB": "$MYSQL_DB"
        }
      }
    }
  },
  "chat.instructionsFilesLocations": {
    "~/.copilot/instructions.md": true
  },

VSCODE_EOF

echo "══════════════════════════════════════════════════════════════"
echo " Done. Restart VS Code to activate the MCP server."
