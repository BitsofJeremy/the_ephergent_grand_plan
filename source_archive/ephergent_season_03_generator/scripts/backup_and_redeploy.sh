#!/usr/bin/env bash
# scripts/backup_and_redeploy.sh
# Perform a full backup (DB + media + commit), then run the update script.
# On failure, attempt a rollback using the backup.

set -euo pipefail
PS4='+(${BASH_SOURCE##*/}:${LINENO}) '

DEST="/opt/ephergent_season_03_generator"
APP_USER="ephergent"
POSTGRES_DB="ephergent_season_03"
POSTGRES_USER="ephergent"
BACKUP_ROOT="/var/backups/ephergent"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
UPDATE_SCRIPT="$DEST/scripts/update_on_debian.sh"

print_usage() {
  cat <<EOF
Usage: sudo bash $0 [options]

This script:
  - creates a backup under $BACKUP_DIR (DB dump, media tar, commit info)
  - runs scripts/update_on_debian.sh
  - if update fails, attempts to rollback code and DB/media

Options:
  --dest PATH             Application path (default: $DEST)
  --no-backup             Skip taking backups (not recommended)
  --keep-backups          Keep backups in $BACKUP_DIR (default true)
  --samba-password-file /path/to/file  Optional: pass to update script
  -h, --help              Show this help
EOF
}

# Defaults
DO_BACKUP=true
KEEP_BACKUPS=true
SAMBA_PASSWORD_FILE=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest) DEST="$2"; BACKUP_DIR="$BACKUP_ROOT/$(date +%Y%m%d_%H%M%S)"; shift 2;;
    --no-backup) DO_BACKUP=false; shift 1;;
    --keep-backups) KEEP_BACKUPS=true; shift 1;;
    --samba-password-file) SAMBA_PASSWORD_FILE="$2"; shift 2;;
    -h|--help) print_usage; exit 0;;
    *) echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

if [[ $(id -u) -ne 0 ]]; then
  echo "This script must be run as root" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
chown root:root "$BACKUP_DIR" || true
chmod 700 "$BACKUP_DIR" || true

SUMMARY_FILE="$BACKUP_DIR/summary.json"

log() { echo "[$(date --iso-8601=seconds)] $*"; }

# 1) Backup
DB_DUMP="$BACKUP_DIR/db_${TIMESTAMP}.dump"
MEDIA_TAR="$BACKUP_DIR/media_${TIMESTAMP}.tar.gz"
GIT_COMMIT_FILE="$BACKUP_DIR/commit.txt"

if $DO_BACKUP; then
  log "Creating backups to $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"

  # Record git commit
  if [[ -d "$DEST/.git" ]]; then
    pushd "$DEST" >/dev/null
    git rev-parse HEAD > "$GIT_COMMIT_FILE" 2>/dev/null || echo "unknown" > "$GIT_COMMIT_FILE"
    popd >/dev/null
  else
    echo "no-git" > "$GIT_COMMIT_FILE"
  fi

  # DB dump
  if sudo -u postgres pg_isready -q; then
    log "Dumping database $POSTGRES_DB to $DB_DUMP"
    if ! sudo -u postgres pg_dump -Fc -f "$DB_DUMP" "$POSTGRES_DB"; then
      log "Warning: pg_dump failed"
    fi
  else
    log "Postgres not ready; skipping DB dump"
  fi

  # Media
  if [[ -d "$DEST/upload_storage" || -d "$DEST/stories_archive" ]]; then
    log "Archiving media into $MEDIA_TAR"
    tar -C "$DEST" -czf "$MEDIA_TAR" upload_storage stories_archive || log "Warning: media tar failed"
  else
    log "No media directories found to archive"
  fi
else
  log "Skipping backups as requested"
fi

# 2) Run update script
if [[ ! -x "$UPDATE_SCRIPT" ]]; then
  log "Update script not found or not executable: $UPDATE_SCRIPT"
  echo '{"status":"error","message":"update script missing"}' > "$SUMMARY_FILE"
  exit 1
fi

UPDATE_CMD=("bash" "$UPDATE_SCRIPT")
if [[ -n "$SAMBA_PASSWORD_FILE" ]]; then
  UPDATE_CMD+=("--samba-password-file" "$SAMBA_PASSWORD_FILE")
fi

log "Running update script: ${UPDATE_CMD[*]}"
set +e
"${UPDATE_CMD[@]}"
UPD_EXIT=$?
set -e

if [[ $UPD_EXIT -eq 0 ]]; then
  log "Update succeeded"
  cat > "$SUMMARY_FILE" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "status": "success",
  "backup_dir": "${BACKUP_DIR}"
}
EOF
  if ! $KEEP_BACKUPS; then
    log "Removing backup dir $BACKUP_DIR"
    rm -rf "$BACKUP_DIR" || true
  fi
  exit 0
fi

# 3) On failure: attempt rollback
log "Update failed (exit $UPD_EXIT). Attempting rollback using backups in $BACKUP_DIR"
ROLLBACK_ERRORS=()

# Restore git commit
if [[ -f "$GIT_COMMIT_FILE" && -d "$DEST/.git" ]]; then
  OLD_COMMIT=$(cat "$GIT_COMMIT_FILE" || echo "")
  if [[ -n "$OLD_COMMIT" && "$OLD_COMMIT" != "no-git" ]]; then
    log "Resetting git to previous commit $OLD_COMMIT"
    pushd "$DEST" >/dev/null
    git fetch --all --tags || log "git fetch failed during rollback"
    git reset --hard "$OLD_COMMIT" || ROLLBACK_ERRORS+=("git_reset")
    popd >/dev/null
  else
    log "No previous commit recorded"
  fi
else
  log "No git commit info or git not present; skipping code rollback"
fi

# Restore database
if [[ -f "$DB_DUMP" ]]; then
  if sudo -u postgres pg_isready -q; then
    log "Restoring Postgres DB from $DB_DUMP"
    if ! sudo -u postgres pg_restore -d "$POSTGRES_DB" --clean --if-exists "$DB_DUMP"; then
      log "Warning: pg_restore encountered problems"
      ROLLBACK_ERRORS+=("db_restore")
    fi
  else
    log "Postgres not ready; cannot restore DB"
    ROLLBACK_ERRORS+=("db_service_down")
  fi
else
  log "No DB dump found to restore"
fi

# Restore media
if [[ -f "$MEDIA_TAR" ]]; then
  log "Restoring media from $MEDIA_TAR"
  tar -C "$DEST" -xzf "$MEDIA_TAR" || ROLLBACK_ERRORS+=("media_restore")
  chown -R "$APP_USER:$APP_USER" "$DEST/upload_storage" "$DEST/stories_archive" || true
else
  log "No media tar found to restore"
fi

# Restart services
log "Restarting services after rollback"
systemctl restart ephergent-web || ROLLBACK_ERRORS+=("restart_web")
systemctl restart ephergent-worker || ROLLBACK_ERRORS+=("restart_worker")

# Final summary
if [[ ${#ROLLBACK_ERRORS[@]} -eq 0 ]]; then
  log "Rollback completed successfully"
  cat > "$SUMMARY_FILE" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "status": "rolled_back",
  "backup_dir": "${BACKUP_DIR}"
}
EOF
  exit 0
else
  log "Rollback completed with errors: ${ROLLBACK_ERRORS[*]}"
  cat > "$SUMMARY_FILE" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "status": "rollback_errors",
  "errors": ${ROLLBACK_ERRORS[@]},
  "backup_dir": "${BACKUP_DIR}"
}
EOF
  exit 2
fi

