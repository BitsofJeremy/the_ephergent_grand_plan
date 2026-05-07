#!/usr/bin/env bash
# sync_to_website.sh — Sync episodes, lore, crew from grand_plan → ephergent.com
# 
# USAGE: ./scripts/sync_to_website.sh [--episodes] [--lore] [--crew] [--all]
#   --episodes  sync phase_04_episodes → transmissions/
#   --lore       sync phase_05_lore     → lore/
#   --crew       sync phase_02_characters/crew → crew/
#   --all        sync all three (default)
#
# IMPORTANT: Website frontmatter is PRESERVED. Source body overwrites, frontmatter stays.
# NEVER use `cp` directly — it wipes website frontmatter.

set -euo pipefail

GP="/home/debian/Documents/code_repos/the_ephergent_grand_plan"
WEB="/home/debian/Documents/code_repos/ephergent.com/src/content"

PYTHON=$(command -v python3)

# ── Argument parsing ──────────────────────────────────────────────────────────
SYNC_EPISODES=false
SYNC_LORE=false
SYNC_CREW=false

if [[ $# -eq 0 ]] || [[ "${1:-}" == "--all" ]]; then
  SYNC_EPISODES=true
  SYNC_LORE=true
  SYNC_CREW=true
else
  for arg in "$@"; do
    case "$arg" in
      --episodes) SYNC_EPISODES=true ;;
      --lore)     SYNC_LORE=true ;;
      --crew)     SYNC_CREW=true ;;
      *)          echo "Unknown: $arg" && exit 1 ;;
    esac
  done
fi

# ── Helpers ──────────────────────────────────────────────────────────────────

# preserve_frontmatter src_body web_file
# Reads: web_file's frontmatter, replaces body with src_body, writes back.
preserve_frontmatter() {
  local src="$1"
  local web="$2"

  if [[ ! -f "$web" ]]; then
    echo "ERROR: website file not found: $web"
    return 1
  fi

  # Extract frontmatter from website file
  local fm=$("$PYTHON" - "$web" << 'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f:
    text = f.read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
if m:
    print(m.group(0), end='')
else:
    print("---", file=sys.stderr)
    sys.exit(1)
PYEOF
)

  # Strip frontmatter from source body
  local body=$("$PYTHON" - "$src" << 'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f:
    text = f.read()
m = re.match(r'^---\n.*?\n---\n', text, re.DOTALL)
if m:
    print(text[m.end():], end='')
else:
    print(text, end='')
PYEOF
)

  # Combine and write back
  printf '%s\n%s' "$fm" "$body" > "$web.tmp"
  mv "$web.tmp" "$web"
}

# ── Episodes ──────────────────────────────────────────────────────────────────
sync_episodes() {
  echo "=== SYNCING EPISODES ==="

  local src_dir="$GP/phase_04_episodes"
  local web_dir="$WEB/transmissions"
  local count=0

  for season in season01 season02 season03; do
    if [[ ! -d "$src_dir/$season" ]]; then
      echo "  ($season: no directory, skipping)"
      continue
    fi
    for src in "$src_dir/$season"/*.md; do
      [[ -f "$src" ]] || continue
      local fname
      fname=$(basename "$src")
      local web="$web_dir/$fname"

      if [[ -f "$web" ]]; then
        preserve_frontmatter "$src" "$web"
        echo "  MERGED  $fname"
      else
        # New episode — copy as-is, no frontmatter merge needed
        cp "$src" "$web"
        echo "  NEW     $fname"
      fi
      ((count++)) || true
    done
  done
  echo "  → $count episode(s) synced"
}

# ── Lore ──────────────────────────────────────────────────────────────────────
sync_lore() {
  echo "=== SYNCING LORE ==="

  local src_dir="$GP/phase_05_lore"
  local web_dir="$WEB/lore"
  local count=0

  # Ensure directory exists
  mkdir -p "$web_dir"

  for src in "$src_dir"/*.md; do
    [[ -f "$src" ]] || continue
    local fname
    fname=$(basename "$src")
    local web="$web_dir/$fname"

    if [[ -f "$web" ]]; then
      preserve_frontmatter "$src" "$web"
      echo "  MERGED  $fname"
    else
      cp "$src" "$web"
      echo "  NEW     $fname"
    fi
    ((count++)) || true
  done
  echo "  → $count lore entry(s) synced"
}

# ── Crew ──────────────────────────────────────────────────────────────────────
sync_crew() {
  echo "=== SYNCING CREW ==="

  local src_dir="$GP/phase_02_characters/crew"
  local web_dir="$WEB/crew"
  local count=0

  mkdir -p "$web_dir"

  for src in "$src_dir"/*.md; do
    [[ -f "$src" ]] || continue
    local fname
    fname=$(basename "$src")
    local web="$web_dir/$fname"

    if [[ -f "$web" ]]; then
      preserve_frontmatter "$src" "$web"
      echo "  MERGED  $fname"
    else
      cp "$src" "$web"
      echo "  NEW     $fname"
    fi
    ((count++)) || true
  done
  echo "  → $count crew file(s) synced"
}

# ── Run ───────────────────────────────────────────────────────────────────────
[[ "$SYNC_EPISODES" == true ]] && sync_episodes
[[ "$SYNC_LORE"     == true ]] && sync_lore
[[ "$SYNC_CREW"     == true ]] && sync_crew

echo ""
echo "Done. Run: cd $WEB && npm run build && npm run deploy"
