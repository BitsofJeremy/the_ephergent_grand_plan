#!/usr/bin/env bash
# sync_to_website.sh — Sync episodes, lore, crew from grand_plan → ephergent.com
# 
# USAGE: ./scripts/sync_to_website.sh [--episodes] [--lore] [--crew] [--all]
#   --episodes  sync episodes → transmissions/
#   --lore       sync lore     → lore/
#   --crew       sync characters/crew → crew/
#   --all        sync all three (default)
#
# IMPORTANT: Website frontmatter is PRESERVED. Source body overwrites, frontmatter stays.
# NEVER use `cp` directly — it wipes website frontmatter.

set -euo pipefail

GP="/Users/jeremy/Documents/current_projects/the_ephergent_projects/the_ephergent_grand_plan"
WEB="/Users/jeremy/Documents/current_projects/my_websites/ephergent.com/src/content"

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
# If web_file has no frontmatter, copies src as-is.
preserve_frontmatter() {
  local src="$1"
  local web="$2"
  local fm_file="/tmp/fm_$$.txt"
  local body_file="/tmp/body_$$.txt"
  local rc=0

  if [[ ! -f "$web" ]]; then
    echo "ERROR: website file not found: $web"
    return 1
  fi

  # Extract frontmatter from web file → fm_file
  "$PYTHON" - "$web" > "$fm_file" << 'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f:
    text = f.read()
m = re.match(r'^---\n(.*?)\n---\n?', text.lstrip('\n'), re.DOTALL)
if m:
    sys.stdout.write(m.group(0))
else:
    sys.exit(1)
PYEOF
  rc=$?

  if [[ $rc -ne 0 ]]; then
    # No frontmatter in web file — copy src as-is
    cp "$src" "$web"
    echo "  COPY    $(basename "$web") (no frontmatter in web file)"
    rm -f "$fm_file" "$body_file"
    return 0
  fi

  # Strip frontmatter from source body → body_file
  "$PYTHON" - "$src" > "$body_file" << 'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f:
    text = f.read()
m = re.match(r'^---\n.*?\n---\n?', text.lstrip('\n'), re.DOTALL)
if m:
    sys.stdout.write(text[m.end():])
else:
    sys.stdout.write(text)
PYEOF

  # Combine: frontmatter + newline + body
  printf '%s\n%s' "$(cat "$fm_file")" "$(cat "$body_file")" > "$web.tmp"
  mv "$web.tmp" "$web"
  rm -f "$fm_file" "$body_file"
}

# ── Filename Validation ───────────────────────────────────────────────────────
# Rule: Space vocabulary only — no sea/nautical language in filenames.
# Ref: CLAUDE.md Rule 2 + Style Rules ("The Space, not the Sea")
NAUTICAL_PATTERN='voyage|voyager|sailing|sailor|seafaring|seascape|sea[rt]|ocean|waves?|harbor|harbour|anchors?|maritime|nautical|boat[sz]?|ferry|captain.*ship|ship.*captain'

validate_filenames() {
  local src_dir="$GP/episodes"
  local violations=0

  echo "=== VALIDATING FILENAMES ==="

  for season in season01 season02 season03; do
    [[ -d "$src_dir/$season" ]] || continue
    for src in "$src_dir/$season"/*.md; do
      [[ -f "$src" ]] || continue
      local fname
      fname=$(basename "$src")
      # Check basename and slug portion (after SXXEXX_)
      local slug="${fname#S??E??_}"
      local check="${fname}_${slug}"
      if echo "$check" | grep -Ei "$NAUTICAL_PATTERN" > /dev/null 2>&1; then
        echo "  [VIOLATION] $fname — contains sea/nautical language"
        violations=$((violations + 1))
      fi
    done
  done

  if [[ $violations -gt 0 ]]; then
    echo ""
    echo "ERROR: $violations filename(s) violate space-vocabulary rule (Rule 2)."
    echo "Fix before syncing. The Space, not the Sea."
    echo ""
    return 1
  fi

  echo "  Filename validation: PASS"
  return 0
}

# ── Episodes ──────────────────────────────────────────────────────────────────
sync_episodes() {
  echo "=== SYNCING EPISODES ==="

  local src_dir="$GP/episodes"
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

  local src_dir="$GP/lore"
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

  local src_dir="$GP/characters"
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
validate_filenames || exit 1
[[ "$SYNC_EPISODES" == true ]] && sync_episodes
[[ "$SYNC_LORE"     == true ]] && sync_lore
[[ "$SYNC_CREW"     == true ]] && sync_crew

echo ""
echo "Done. Run: cd $WEB && npm run build && npm run deploy"
