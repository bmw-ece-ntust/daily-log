#!/usr/bin/env bash
# Install the daily-log skills into ~/.claude, wire the daily-log prompt hook, and
# set up the Python tool venv. Idempotent. This repo IS the tool + the skills home.
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"

echo "==> skills -> ~/.claude/skills"
mkdir -p ~/.claude/skills
for d in "$REPO"/skills/*/; do
  name="$(basename "$d")"; [ -f "$d/SKILL.md" ] || continue
  mkdir -p ~/.claude/skills/"$name"; cp -R "$d"/. ~/.claude/skills/"$name"/
  echo "    $name"
done

echo "==> prompt scripts -> ~/.claude/prompts"
mkdir -p ~/.claude/prompts
cp "$REPO"/scripts/* ~/.claude/prompts/ 2>/dev/null || true
chmod +x ~/.claude/prompts/*.sh 2>/dev/null || true

echo "==> set DAILY_LOG_HOME + wire UserPromptSubmit daily-log hook in ~/.claude/settings.json"
S="$HOME/.claude/settings.json"
if [ -f "$S" ] && command -v jq >/dev/null; then
  tmp=$(mktemp)
  jq --arg home "$REPO" '
    .env = (.env // {}) | .env.DAILY_LOG_HOME = $home
    | .hooks = (.hooks // {})
    | .hooks.UserPromptSubmit = (.hooks.UserPromptSubmit // [{"hooks":[]}])
    | .hooks.UserPromptSubmit[0].hooks =
        (((.hooks.UserPromptSubmit[0].hooks // []) | map(select(.command|test("fetch-auto-daily-log")|not)))
         + [{"type":"command","command":"bash ~/.claude/prompts/fetch-auto-daily-log.sh","statusMessage":"Loading daily-log prompt..."}])
  ' "$S" > "$tmp" && mv "$tmp" "$S" && chmod 600 "$S"
  echo "    DAILY_LOG_HOME=$REPO"
fi

echo "==> python tool venv"
[ -d "$REPO/.venv" ] || python3 -m venv "$REPO/.venv"
"$REPO/.venv/bin/pip" install -q -r "$REPO/requirements.txt" 2>&1 | tail -1 || true
[ -f "$REPO/env.yaml" ] || cp "$REPO/env.example.yaml" "$REPO/env.yaml"

echo "==> done. Skills: daily-plan, daily-log, daily-log-commit, daily-log-audit."
echo "    Needs gh auth, and (for audit) the LTM skills from bmw-ece-ntust/llm-skill-ltm."
