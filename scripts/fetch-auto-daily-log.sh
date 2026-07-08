#!/bin/bash
# Global hook script — injected when user mentions git push/commit.
# Reads the user prompt from stdin (JSON) and exits silently if no git trigger phrase found.
# Resolves {{VSCODE_TARGET_SESSION_LOG}} with the live transcript path so the session
# start time can be derived from the earliest user message after the last commit.
# Falls back to local auto-daily-log.md if GitHub is unreachable.
# Canonical source: https://github.com/bmw-ece-ntust/SOP/blob/master/daily-log.md#auto-daily-log

FALLBACK="$(dirname "$0")/auto-daily-log.md"

# --- Read stdin JSON once; extract prompt and transcript_path ---
INPUT=$(cat)
prompt=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('prompt', ''))
except Exception:
    print('')
" 2>/dev/null)
transcript=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('transcript_path', ''))
except Exception:
    print('')
" 2>/dev/null)

# --- Check for git trigger phrase (case-insensitive) ---
if ! echo "$prompt" | grep -qiE '(git (push|commit)|(commit|push).{0,10}(push|commit)|push (the|my|all) (changes|code|updates|this)|let.?s (commit|push)|please (commit|push)|go ahead.*(commit|push)|time to (commit|push))'; then
    exit 0
fi

# --- Inject session timing context ---
echo "=== SESSION TIMING (auto-injected) ==="
echo "Last commit: $(git log -1 --format='%H %ai' 2>/dev/null || echo '(no commits yet)')"
echo "Session end (now): $(date '+%Y/%m/%d %H:%M')"
echo "Session transcript: ${transcript:-(unavailable — ask the user for start time)}"
echo "Session START = first user message timestamp in the transcript that falls AFTER the last commit above."
echo "======================================="
echo ""

# --- Fetch latest SOP prompt, fall back to local copy ---
content=""
if command -v gh &>/dev/null; then
    fetched=$(gh api repos/bmw-ece-ntust/SOP/contents/daily-log.md --jq '.content' 2>/dev/null | base64 -d 2>/dev/null)
    if [ -n "$fetched" ]; then
        content=$(echo "$fetched" | python3 -c "
import sys
c = sys.stdin.read()
s = c.find('Reconcile all 4 project memory files')
e = c.find('\n\`\`\`', s)
if s != -1 and e != -1:
    print(c[s:e])
" 2>/dev/null)
    fi
fi

if [ -z "$content" ]; then
    content=$(cat "$FALLBACK")
fi

# --- Resolve the session-log placeholder with the real transcript path ---
content="${content//\{\{VSCODE_TARGET_SESSION_LOG\}\}/${transcript:-the VS Code session transcript}}"

printf '%s\n' "$content"

# --- Step 2: after the commit+push, post the day's daily-log to GitHub ---
# The block above is Step 1 (it writes the repo). Step 2 posts the daily-log to
# the lab progress issue via the fully-featured /daily-log skill (catch-up,
# evidence links, edit-in-place). Appended here so it fires whether Step 1 came
# from the SOP or the local fallback. The skill self-restricts to the lab orgs,
# so it no-ops on non-lab repos.
# Canonical: SOP daily-log.md#step-2--post-the-daily-log-to-github
cat <<'STEP2'

---

### Step 2 — Post the daily-log to GitHub

The block above was **Step 1** — it wrote the repo (reconcile, commit, push).
Now run **Step 2**: invoke the **`/daily-log`** skill to post today's entry to the
lab progress issue (`bmw-ece-ntust/progress-plan#366`). The skill seeds from the
LTM + commit history, edits the day's existing daily-plan/daily-log comment in
place (creating one only if none exists), catches up any missing weekdays, and
attaches evidence links. It self-restricts to the lab orgs (`bmw-ece-ntust`,
`bmw-ntust-internship`, `raycg`), so it is a no-op on non-lab repos. Do this only
after Step 1's push has succeeded.
STEP2
