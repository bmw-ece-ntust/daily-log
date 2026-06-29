#!/usr/bin/env bash
# deploy-lab-llm.sh — One-touch deployment for the BMW Lab's LLM stack.
#
# Installs EVERYTHING for the lab's LLM preferences on a macOS machine, idempotently:
#   1. dependencies (git, gh, jq, libpq/psql, bitwarden-cli) via Homebrew
#   2. clone or fast-forward the three lab repos under ~/Documents/GitHub
#        - bmw-ece-ntust/llm-prefs       (global AI preferences)
#        - bmw-ece-ntust/llm-skill-ltm   (PostgreSQL long-term memory skills + hook)
#        - bmw-ece-ntust/daily-log       (daily-log skills + Python tool + push hook)
#   3. global prefs -> llm-prefs/install.sh (renders ~/.claude/CLAUDE.md + settings + skills)
#   4. LTM skills + SessionStart activity hook + live DB check (llm-skill-ltm/setup.sh)
#   5. daily-log skills + UserPromptSubmit push hook + Python venv (daily-log/install.sh)
#   6. (optional) --backfill: back up this machine's past sessions to the LTM
#
# Run once per machine:
#   bash ~/Documents/GitHub/daily-log/lab-automation/deploy-lab-llm.sh
# Or one-line bootstrap (no repos yet):
#   curl -fsSL https://raw.githubusercontent.com/bmw-ece-ntust/daily-log/master/lab-automation/deploy-lab-llm.sh | bash
#
# After it finishes, restart Claude Code / Cowork so the new skills + prefs load.
# Idempotent: safe to re-run any time to update to the latest lab config.
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
GH_DIR="${GH_DIR:-$HOME/Documents/GitHub}"
GH_BASE="https://github.com/bmw-ece-ntust"
PREFS_REPO="llm-prefs"
LTM_REPO="llm-skill-ltm"
DAILYLOG_REPO="daily-log"
DO_BACKFILL=0
[ "${1:-}" = "--backfill" ] && DO_BACKFILL=1

say()  { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '    \033[33m! %s\033[0m\n' "$*"; }

# ── 1. Dependencies ───────────────────────────────────────────────────────────
say "1/6 dependencies"
if ! command -v brew >/dev/null 2>&1; then
  warn "Homebrew not found. Install it from https://brew.sh then re-run, or install git/gh/jq/libpq/bitwarden-cli manually."
else
  need=""
  for b in git gh jq; do command -v "$b" >/dev/null 2>&1 || need="$need $b"; done
  command -v bw >/dev/null 2>&1 || need="$need bitwarden-cli"
  [ -x "$(brew --prefix libpq 2>/dev/null)/bin/psql" ] || command -v psql >/dev/null 2>&1 || need="$need libpq"
  if [ -n "$need" ]; then info "installing:$need"; # shellcheck disable=SC2086
    brew install $need; else info "all present (git, gh, jq, psql, bw)"; fi
fi

# ── 2. Clone / update the three lab repos ─────────────────────────────────────
say "2/6 lab repos -> $GH_DIR"
mkdir -p "$GH_DIR"
clone_or_update() {
  local name="$1" dir="$GH_DIR/$1"
  if [ -d "$dir/.git" ]; then
    info "update $name"
    git -C "$dir" pull --ff-only --quiet 2>/dev/null || warn "$name: could not fast-forward (local changes?) — skipped"
  else
    info "clone  $name"
    git clone --quiet "$GH_BASE/$name.git" "$dir" 2>/dev/null || warn "$name: clone failed (private/no access?) — skipped"
  fi
}
clone_or_update "$PREFS_REPO"
clone_or_update "$LTM_REPO"
clone_or_update "$DAILYLOG_REPO"

PREFS_DIR="$GH_DIR/$PREFS_REPO"
LTM_DIR="$GH_DIR/$LTM_REPO"
DAILYLOG_DIR="$GH_DIR/$DAILYLOG_REPO"
export LTM_HOME="$LTM_DIR"

# Resolve this script's own daily-log dir if it differs from the cloned one
# (e.g. running from a checkout elsewhere). Prefer the script's repo for setup-memory.sh.
SELF_DAILYLOG="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$SELF_DAILYLOG/lab-automation/setup-memory.sh" ] && DAILYLOG_DIR="$SELF_DAILYLOG"

# Prefer the canonical prefs file from llm-prefs if present.
for cand in "$PREFS_DIR/CLAUDE.md" "$PREFS_DIR/global-claude.md" "$PREFS_DIR/prefs/global-claude.md"; do
  [ -f "$cand" ] && export LAB_PREFS_FILE="$cand" && break
done

# ── 3. Global prefs (canonical: llm-prefs/install.sh; fallback: setup-memory.sh) ─
say "3/6 global prefs + base settings"
if [ -f "$PREFS_DIR/install.sh" ]; then
  info "running canonical llm-prefs installer"
  ( cd "$PREFS_DIR" && bash install.sh ) 2>&1 | sed 's/^/    /' || warn "llm-prefs install reported an issue"
elif [ -f "$DAILYLOG_DIR/lab-automation/setup-memory.sh" ]; then
  warn "llm-prefs not available — using the daily-log mirror (setup-memory.sh)"
  LAB_DEPLOY_SKIP_LTM=1 bash "$DAILYLOG_DIR/lab-automation/setup-memory.sh" | sed 's/^/    /'
else
  warn "no prefs installer found — skipped prefs"
fi

# ── 4. LTM skills + SessionStart hook + DB check ──────────────────────────────
say "4/6 PostgreSQL LTM (llm-skill-ltm)"
if [ -d "$LTM_DIR" ]; then
  [ -f "$LTM_DIR/.env" ] || { cp "$LTM_DIR/.env.example" "$LTM_DIR/.env" 2>/dev/null && chmod 600 "$LTM_DIR/.env" && warn ".env created from template — fill PG_MEMORY_BW_ITEM + PG_SSH_USER, then re-run"; }
  if [ -f "$LTM_DIR/.env" ]; then
    ( cd "$LTM_DIR" && bash setup.sh ) 2>&1 | sed 's/^/    /' || warn "LTM setup reported an issue (DB may be offline) — skills still installed"
  fi
else
  warn "$LTM_DIR missing — LTM not installed"
fi

# ── 5. daily-log skills + push hook + tool venv ───────────────────────────────
say "5/6 daily-log skills + hooks (daily-log)"
if [ -f "$DAILYLOG_DIR/install.sh" ]; then
  ( cd "$DAILYLOG_DIR" && bash install.sh ) 2>&1 | sed 's/^/    /' || warn "daily-log install reported an issue (venv/pip?) — skills still copied"
else
  warn "$DAILYLOG_DIR/install.sh missing — daily-log skills not installed"
fi

# ── 6. Optional: back up this machine's STM to the LTM ────────────────────────
say "6/6 STM backup to LTM"
if [ "$DO_BACKFILL" = 1 ]; then
  if [ -f "$LTM_DIR/scripts/stm-backup.sh" ]; then
    bash "$LTM_DIR/scripts/stm-backup.sh"       2>&1 | sed 's/^/    /' || warn "stm-backup skipped (LTM offline?)"
    bash "$LTM_DIR/scripts/memory-backfill.sh"  2>&1 | sed 's/^/    /' || warn "memory-backfill skipped (LTM offline?)"
  else
    warn "LTM backup scripts not found"
  fi
else
  info "skipped (pass --backfill to back up past sessions now)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
say "done"
info "Installed: global prefs (~/.claude/CLAUDE.md), LTM skills + SessionStart hook,"
info "daily-log skills + push hook. Restart Claude Code / Cowork to load them."
info "Re-run any time to update; add --backfill to capture past sessions."
