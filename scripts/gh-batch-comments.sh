#!/usr/bin/env bash
# gh-batch-comments.sh — create and/or update many issue comments in ONE GitHub request.
#
# WHY THIS EXISTS. Backfilling the daily-log meant 14 comments, and the REST API has no
# bulk endpoint, so the obvious loop is 14 round trips: slow, rate-limit-hungry, and
# non-atomic — a failure halfway leaves the issue half-updated with no record of where it
# stopped. GraphQL accepts many aliased mutations in one document, so the whole backfill
# becomes a single request.
#
# Usage:
#   gh-batch-comments.sh --issue <owner/repo#number> --create <dir>
#   gh-batch-comments.sh --issue <owner/repo#number> --update <dir>
#   gh-batch-comments.sh --issue ... --create <dir> --update <dir> [--dry-run]
#
#   --create  posts every *.md in the directory as a NEW comment
#   --update  edits existing comments; each file is named <comment_id>.md
#   --dry-run print the GraphQL document and exit, writing nothing
set -euo pipefail
ISSUE=""; CREATE_DIR=""; UPDATE_DIR=""; DRY=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --issue)   shift; ISSUE="${1:-}" ;;
    --create)  shift; CREATE_DIR="${1:-}" ;;
    --update)  shift; UPDATE_DIR="${1:-}" ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "gh-batch-comments: unknown argument: $1" >&2; exit 2 ;;
  esac
  shift || true
done
[ -n "$ISSUE" ] || { sed -n '2,18p' "$0"; exit 2; }
[ -n "$CREATE_DIR$UPDATE_DIR" ] || { echo "gh-batch-comments: nothing to do" >&2; exit 2; }
command -v gh >/dev/null || { echo "gh-batch-comments: gh required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "gh-batch-comments: python3 required" >&2; exit 1; }

REPO="${ISSUE%%#*}"; NUM="${ISSUE##*#}"
OWNER="${REPO%%/*}"; NAME="${REPO##*/}"
MANIFEST="$(mktemp)"; trap 'rm -f "$MANIFEST"' EXIT

# Resolve every node id FIRST, in bash, so the document builder is pure string work.
{
  printf '{"subject":'
  if [ -n "$CREATE_DIR" ]; then
    sid="$(gh api graphql -f query='query($o:String!,$n:String!,$i:Int!){repository(owner:$o,name:$n){issue(number:$i){id}}}' \
           -F o="$OWNER" -F n="$NAME" -F i="$NUM" --jq '.data.repository.issue.id')"
    [ -n "$sid" ] || { echo "gh-batch-comments: could not resolve issue node id" >&2; exit 1; }
    printf '"%s"' "$sid"
  else
    printf 'null'
  fi
  printf ',"creates":['
  first=1
  if [ -n "$CREATE_DIR" ]; then
    for f in "$CREATE_DIR"/*.md; do
      [ -e "$f" ] || continue
      [ "$first" = 1 ] || printf ','; first=0
      printf '"%s"' "$f"
    done
  fi
  printf '],"updates":['
  first=1
  if [ -n "$UPDATE_DIR" ]; then
    for f in "$UPDATE_DIR"/*.md; do
      [ -e "$f" ] || continue
      cid="$(basename "$f" .md)"
      case "$cid" in ''|*[!0-9]*) echo "gh-batch-comments: skipping $f (name is not a numeric comment id)" >&2; continue ;; esac
      node="$(gh api "repos/$OWNER/$NAME/issues/comments/$cid" --jq '.node_id' 2>/dev/null || true)"
      [ -n "$node" ] || { echo "gh-batch-comments: cannot resolve node id for comment $cid" >&2; exit 1; }
      [ "$first" = 1 ] || printf ','; first=0
      printf '{"node":"%s","path":"%s"}' "$node" "$f"
    done
  fi
  printf ']}'
} > "$MANIFEST"

DOC="$(GB_MANIFEST="$MANIFEST" python3 - <<'PY'
import json, os
m = json.load(open(os.environ["GB_MANIFEST"], encoding="utf-8"))

def lit(s):
    # json.dumps yields a GraphQL-safe double-quoted string: the escaping rules for
    # quotes, backslashes and newlines are identical, and daily-log bodies contain all
    # three. Hand-rolling this is how a stray quote silently truncates a comment body.
    return json.dumps(s)

parts = []
for i, path in enumerate(m.get("creates") or []):
    body = open(path, encoding="utf-8").read()
    parts.append(f'  c{i}: addComment(input:{{subjectId:{lit(m["subject"])}, body:{lit(body)}}})'
                 f' {{ commentEdge {{ node {{ url }} }} }}')
for i, up in enumerate(m.get("updates") or []):
    body = open(up["path"], encoding="utf-8").read()
    parts.append(f'  u{i}: updateIssueComment(input:{{id:{lit(up["node"])}, body:{lit(body)}}})'
                 f' {{ issueComment {{ url }} }}')
print("mutation {\n" + "\n".join(parts) + "\n}" if parts else "")
PY
)"

[ -n "$DOC" ] || { echo "gh-batch-comments: no comment files found"; exit 0; }
COUNT="$(printf '%s' "$DOC" | grep -cE 'addComment|updateIssueComment' || true)"

if [ "$DRY" = 1 ]; then
  printf '%s\n' "$DOC"
  echo "--- dry run: $COUNT mutation(s) in 1 request; nothing sent ---" >&2
  exit 0
fi

echo "gh-batch-comments: sending $COUNT mutation(s) in 1 request" >&2
gh api graphql -f query="$DOC" --jq '.data | to_entries[] | .value | (.commentEdge.node.url // .issueComment.url)'
