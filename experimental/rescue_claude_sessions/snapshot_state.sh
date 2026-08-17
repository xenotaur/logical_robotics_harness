#!/usr/bin/env bash
# Snapshot path-keyed Claude Code state before migrating or archiving any of it.
#
# Claude Code already keeps its own rolling backups of ~/.claude.json under
# ~/.claude/backups, but nothing backs up ~/.claude/projects, which holds every
# transcript and every memory corpus. That is the part at risk here.
#
# Snapshots are written outside the repository on purpose: experimental/README.md
# requires raw private transcript captures to stay out of Git.

set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
DEST="${RESCUE_SNAPSHOT_DIR:-/private/tmp/claude-rescue-snapshots}"
SCOPE="all"
COMPRESS="gzip"

usage() {
  cat <<'EOF'
Usage: snapshot_state.sh [--scope all|memory] [--fast] [--dest DIR]

  --scope all     transcripts + memory + .claude.json (default; ~1GB, slow)
  --scope memory  memory corpora + .claude.json only (small, seconds)
  --fast          store uncompressed; much quicker on large scopes
  --dest DIR      output directory (default /private/tmp/claude-rescue-snapshots)

Restore is a manual, deliberate step:
  tar xf <snapshot>.tar[.gz] -C /   # archive holds paths relative to /
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) SCOPE="${2:?--scope needs a value}"; shift 2 ;;
    --fast) COMPRESS="none"; shift ;;
    --dest) DEST="${2:?--dest needs a value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

case "$SCOPE" in
  all|memory) ;;
  *) echo "--scope must be 'all' or 'memory'" >&2; exit 2 ;;
esac

if [[ ! -d "$CLAUDE_DIR/projects" ]]; then
  echo "no projects directory at $CLAUDE_DIR/projects" >&2
  exit 1
fi

mkdir -p "$DEST"
stamp="$(date +%Y%m%d-%H%M%S)"
if [[ "$COMPRESS" == "gzip" ]]; then
  archive="$DEST/claude-state-$SCOPE-$stamp.tar.gz"
  tar_flags="czf"
else
  archive="$DEST/claude-state-$SCOPE-$stamp.tar"
  tar_flags="cf"
fi

# Paths are stored relative to / so a restore is an unambiguous `tar xf ... -C /`.
members=()
if [[ "$SCOPE" == "all" ]]; then
  members+=("${CLAUDE_DIR#/}/projects")
else
  while IFS= read -r dir; do
    members+=("${dir#/}")
  done < <(find "$CLAUDE_DIR/projects" -mindepth 2 -maxdepth 2 -type d -name memory)
fi
[[ -f "$HOME/.claude.json" ]] && members+=("${HOME#/}/.claude.json")

if [[ ${#members[@]} -eq 0 ]]; then
  echo "nothing matched scope '$SCOPE'" >&2
  exit 1
fi

echo "scope   : $SCOPE (${#members[@]} tree(s))"
echo "source  : $CLAUDE_DIR"
echo "archive : $archive"
echo "writing..."
tar -C / -"$tar_flags" "$archive" "${members[@]}"

echo "verifying archive integrity..."
tar -tf "$archive" >/dev/null

size="$(du -h "$archive" | cut -f1)"
count="$(tar -tf "$archive" | wc -l | tr -d ' ')"
echo
echo "OK  $archive"
echo "    $size, $count entries"
echo "    restore with: tar xf '$archive' -C /"
