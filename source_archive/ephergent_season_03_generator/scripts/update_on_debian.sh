#!/usr/bin/env bash
# scripts/update_on_debian.sh
# Safe update helper for Ephergent app on Debian-based VMs.
# Run as root or via sudo. Designed to be idempotent and produce a JSON summary in $DEST/logs.

set -euo pipefail
PS4='+(${BASH_SOURCE##*/}:${LINENO}) '

# Defaults (match deploy_on_debian.sh)
DEST="/opt/ephergent_season_03_generator"
APP_USER="ephergent"
POSTGRES_USER="ephergent"
POSTGRES_DB="ephergent_season_03"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUMMARY_FILE="$DEST/logs/update_summary_${TIMESTAMP}.json"
MIGRATION_RESULT_FILE="$DEST/migration_result.json"

# Behavior flags (can be overridden on CLI)
DO_BACKUP=true
DO_PULL=true
DO_DEPS=true
DO_MIGRATE=true
DO_RESTART=true
BRANCH="main"
GIT_REMOTE="origin"
KEEP_BACKUPS=false
# Optional Samba password (prefer file input for security)
SAMBA_PASSWORD="ephergent"
SAMBA_PASSWORD_FILE=""

print_usage() {
  cat <<EOF
Usage: sudo bash $0 [options]

Options:
  --dest PATH           Install path (default: $DEST)
  --user USER           App user (default: $APP_USER)
  --no-backup           Skip taking DB/media backups
  --no-pull             Skip git fetch/pull
  --no-deps             Skip installing/updating Python deps in venv
  --no-migrate          Skip running migrations
  --no-restart          Skip restarting systemd services
  --branch BRANCH       Git branch to checkout/pull (default: $BRANCH)
  --remote REMOTE       Git remote name (default: $GIT_REMOTE)
  --keep-backups        Keep backup artifacts in /tmp (by default they are left in /tmp)
  --samba-password 'pw' Optional (less secure): provide samba password on CLI
  --samba-password-file /path/to/file  Optional (recommended): file (mode 600) containing samba password
  -h, --help            Show this help

Example:
  sudo bash $0 --dest /opt/ephergent_season_03_generator --user ephergent --samba-password-file /root/.smbpass
EOF
}

# CLI arg parsing
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      DEST="$2"; shift 2;;
    --user)
      APP_USER="$2"; shift 2;;
    --no-backup)
      DO_BACKUP=false; shift 1;;
    --no-pull)
      DO_PULL=false; shift 1;;
    --no-deps)
      DO_DEPS=false; shift 1;;
    --no-migrate)
      DO_MIGRATE=false; shift 1;;
    --no-restart)
      DO_RESTART=false; shift 1;;
    --branch)
      BRANCH="$2"; shift 2;;
    --remote)
      GIT_REMOTE="$2"; shift 2;;
    --keep-backups)
      KEEP_BACKUPS=true; shift 1;;
    --samba-password)
      SAMBA_PASSWORD="$2"; shift 2;;
    --samba-password-file)
      SAMBA_PASSWORD_FILE="$2"; shift 2;;
    -h|--help)
      print_usage; exit 0;;
    *)
      echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

# Read samba password if provided via file
if [[ -n "$SAMBA_PASSWORD_FILE" ]]; then
  if [[ -f "$SAMBA_PASSWORD_FILE" ]]; then
    perms=$(stat -c "%a" "$SAMBA_PASSWORD_FILE" 2>/dev/null || echo "")
    if [[ "$perms" != "600" && "$perms" != "400" ]]; then
      echo "Warning: Samba password file $SAMBA_PASSWORD_FILE should be mode 600 (owner read/write) for security. Current mode: $perms"
    fi
    SAMBA_PASSWORD=$(tr -d '\n' < "$SAMBA_PASSWORD_FILE")
  else
    echo "Warning: Samba password file $SAMBA_PASSWORD_FILE not found; ignoring"
  fi
fi

# Helpers
log() { echo "[$(date --iso-8601=seconds)] $*"; }
error_exit() {
  echo "{\"timestamp\": \"$(date --iso-8601=seconds)\", \"status\": \"error\", \"message\": \"$1\"}" > "$SUMMARY_FILE"
  exit 1
}

ensure_dir() {
  local d="$1"; mkdir -p "$d" || true; chown -R "$APP_USER:$APP_USER" "$d" || true
}

# Ensure destination exists
if [[ ! -d "$DEST" ]]; then
  error_exit "Destination $DEST does not exist. Please run initial deploy first."
fi

# Ensure logs dir
ensure_dir "$DEST/logs"

RESULTS=( )
add_result() {
  RESULTS+=("$1")
}

# Verify or install ffmpeg (audio support)
if ! command -v ffmpeg >/dev/null 2>&1; then
  log "ffmpeg not found — installing system ffmpeg"
  apt-get update -y || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg || log "Warning: failed to install ffmpeg via apt"
else
  log "ffmpeg present: $(ffmpeg -version | head -n1)"
fi

# 1) Optional backups
DB_BACKUP=""
MEDIA_BACKUP=""
if $DO_BACKUP; then
  log "Starting backups..."
  DB_BACKUP="/tmp/ephergent_db_${TIMESTAMP}.dump"
  MEDIA_BACKUP="/tmp/ephergent_media_${TIMESTAMP}.tar.gz"
  # DB dump (custom format)
  if sudo -u postgres pg_isready -q; then
    log "Dumping Postgres DB $POSTGRES_DB to $DB_BACKUP"
    if sudo -u postgres pg_dump -Fc -f "$DB_BACKUP" "$POSTGRES_DB"; then
      add_result "db_backup:$DB_BACKUP"
    else
      log "Warning: pg_dump failed; continuing"
    fi
  else
    log "Postgres not ready; skipping DB dump"
  fi
  # Media backup (upload_storage + stories_archive)
  if tar -C "$DEST" -czf "$MEDIA_BACKUP" upload_storage stories_archive 2>/dev/null; then
    add_result "media_backup:$MEDIA_BACKUP"
  else
    log "Warning: media backup failed (maybe dirs missing)"
  fi
  if ! $KEEP_BACKUPS; then
    # files left in /tmp; admin can move them elsewhere
    log "Backups placed in /tmp (KEEP_BACKUPS=$KEEP_BACKUPS)"
  fi
else
  log "Skipping backups (as requested)"
fi

# 2) Git fetch & pull
if $DO_PULL; then
  if [[ -d "$DEST/.git" ]]; then
    log "Fetching and pulling latest code (branch: $BRANCH, remote: $GIT_REMOTE)"
    pushd "$DEST" >/dev/null
    # Record current commit for simple rollback trace
    CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    git fetch "$GIT_REMOTE" --tags || log "git fetch failed (continuing)"
    git checkout "$BRANCH" || git checkout -B "$BRANCH" "$GIT_REMOTE/$BRANCH"
    git pull --ff-only "$GIT_REMOTE" "$BRANCH" || log "git pull failed (non-fast-forward?), continuing"
    NEW_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    popd >/dev/null
    add_result "git_from:$CURRENT_COMMIT->${NEW_COMMIT}"
  else
    log "No .git directory at $DEST; skipping git pull"
  fi
else
  log "Skipping git pull (as requested)"
fi

# 3) Update Python dependencies in venv (as APP_USER)
if $DO_DEPS; then
  log "Updating Python dependencies in venv"
  if [[ -x "$DEST/.venv/bin/activate" ]] || [[ -d "$DEST/.venv" ]]; then
    # Run pip install as the app user inside venv
    su - "$APP_USER" -c "bash -lc 'cd \"$DEST\" && source .venv/bin/activate && pip install --upgrade pip setuptools wheel >/tmp/pip_update_${TIMESTAMP}.log 2>&1 || true'"
    if [[ -f "$DEST/requirements.txt" ]]; then
      log "Installing from requirements.txt"
      su - "$APP_USER" -c "bash -lc 'cd \"$DEST\" && source .venv/bin/activate && pip install -r requirements.txt >>/tmp/pip_update_${TIMESTAMP}.log 2>&1'"
    elif [[ -f "$DEST/pyproject.toml" ]]; then
      log "Installing package from pyproject.toml"
      su - "$APP_USER" -c "bash -lc 'cd \"$DEST\" && source .venv/bin/activate && pip install . >>/tmp/pip_update_${TIMESTAMP}.log 2>&1 || pip install -e . >>/tmp/pip_update_${TIMESTAMP}.log 2>&1'"
    else
      log "No requirements.txt or pyproject.toml found; skipping pip install"
    fi
    # copy pip log
    cp /tmp/pip_update_${TIMESTAMP}.log "$DEST/logs/pip_update_${TIMESTAMP}.log" 2>/dev/null || true
    chown $APP_USER:$APP_USER "$DEST/logs/pip_update_${TIMESTAMP}.log" 2>/dev/null || true
    add_result "deps_log:logs/pip_update_${TIMESTAMP}.log"
  else
    log "Virtualenv not found at $DEST/.venv; skipping deps update"
  fi
else
  log "Skipping dependency update (as requested)"
fi

# 4) Stop worker (to avoid race conditions during migrations)
log "Stopping worker service"
if systemctl is-active --quiet ephergent-worker; then
  systemctl stop ephergent-worker || log "Failed to stop ephergent-worker (continuing)"
else
  log "ephergent-worker not active"
fi

# 5) Run migrations
MIG_EXIT=0
if $DO_MIGRATE; then
  log "Running migrations (file-based + DB migrations if present)"
  # Reuse the same approach as deploy: run via su - APP_USER so venv + envs are applied
  su - $APP_USER -c "bash -lc 'cd \"$DEST\" && if [ -f /etc/default/ephergent_web ]; then set -a; source /etc/default/ephergent_web; fi; if [ -f \"$DEST/.env\" ]; then set -a; source \"$DEST/.env\"; fi; export MIGRATION_RESULT_FILE=\"$MIGRATION_RESULT_FILE\"; PYTHONPATH=\"$DEST\" .venv/bin/python scripts/run_migrations.py > /tmp/eph_update_mig_${TIMESTAMP}.out 2>&1; echo exit_code:\$? > /tmp/eph_update_mig_${TIMESTAMP}.exit'"
  MIG_EXIT=$(cat /tmp/eph_update_mig_${TIMESTAMP}.exit 2>/dev/null | sed -n 's/^exit_code:\([0-9][0-9]*\)/\1/p' || echo 1)
  if [[ -f /tmp/eph_update_mig_${TIMESTAMP}.out ]]; then
    cp /tmp/eph_update_mig_${TIMESTAMP}.out "$DEST/logs/migration_update_${TIMESTAMP}.log" 2>/dev/null || true
    chown $APP_USER:$APP_USER "$DEST/logs/migration_update_${TIMESTAMP}.log" 2>/dev/null || true
  fi
  rm -f /tmp/eph_update_mig_${TIMESTAMP}.out /tmp/eph_update_mig_${TIMESTAMP}.exit || true
  if [[ "$MIG_EXIT" == "0" ]]; then
    add_result "migrations:success"
  else
    add_result "migrations:failed($MIG_EXIT)"
    log "Migrations failed with exit code $MIG_EXIT"
  fi
else
  log "Skipping migrations (as requested)"
fi

# 5.5) Optional non-interactive Samba user creation (if password provided)
if [[ -n "$SAMBA_PASSWORD" ]]; then
  log "Ensuring Samba user $APP_USER exists and setting password non-interactively"
  if ! pdbedit -L | grep -q "^$APP_USER:"; then
    # create unix user if not exists (should exist already)
    if ! id -u "$APP_USER" >/dev/null 2>&1; then
      log "App user $APP_USER does not exist; creating..."
      useradd --create-home --home-dir /home/$APP_USER --shell /bin/bash $APP_USER || true
    fi
    # add smbpasswd non-interactively
    printf "%s\n%s\n" "$SAMBA_PASSWORD" "$SAMBA_PASSWORD" | smbpasswd -s -a "$APP_USER" || log "Failed to add Samba user non-interactively"
    add_result "samba_user_added"
  else
    log "Samba user $APP_USER already present"
    add_result "samba_user_exists"
  fi
else
  log "No Samba password provided; skipping non-interactive Samba account creation"
fi

# 6) Start/restart services
if $DO_RESTART; then
  log "Starting/restarting services"
  systemctl restart ephergent-web || log "Failed to restart ephergent-web"
  systemctl start ephergent-worker || systemctl restart ephergent-worker || log "Failed to (re)start ephergent-worker"
  systemctl restart nginx || log "Failed to restart nginx"
  add_result "services:restarted"
else
  log "Skipping service restarts (as requested)"
fi

# 7) Verification: quick health checks
log "Verifying services and collecting logs"
APP_STATUS=0
if systemctl is-active --quiet ephergent-web; then
  log "ephergent-web active"
else
  log "ephergent-web not active"
  APP_STATUS=1
fi
if systemctl is-active --quiet ephergent-worker; then
  log "ephergent-worker active"
else
  log "ephergent-worker not active"
  APP_STATUS=1
fi

# Collect tail of logs
tail -n 200 "$DEST/logs/application.log" > "$DEST/logs/update_app_tail_${TIMESTAMP}.log" 2>/dev/null || true
tail -n 200 "$DEST/logs/worker.log" > "$DEST/logs/update_worker_tail_${TIMESTAMP}.log" 2>/dev/null || true
chown $APP_USER:$APP_USER "$DEST/logs/update_app_tail_${TIMESTAMP}.log" "$DEST/logs/update_worker_tail_${TIMESTAMP}.log" 2>/dev/null || true

# 8) Write summary JSON
# Build a proper JSON array for results
results_json="["
if [[ ${#RESULTS[@]} -gt 0 ]]; then
  for r in "${RESULTS[@]}"; do
    # escape double quotes
    esc=$(printf '%s' "$r" | sed 's/"/\\"/g')
    results_json+="\"${esc}\","
  done
  # remove trailing comma
  results_json=${results_json%,}
fi
results_json+="]"

# Write summary file with safe quoting
cat > "$SUMMARY_FILE" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "destination": "$DEST",
  "git_changes": "${CURRENT_COMMIT:-unknown}->${NEW_COMMIT:-unknown}",
  "results": $results_json,
  "migration_exit": $MIG_EXIT,
  "service_ok": $([[ $APP_STATUS -eq 0 ]] && echo true || echo false)
}
EOF
chown $APP_USER:$APP_USER "$SUMMARY_FILE" 2>/dev/null || true

log "Update completed. Summary: $SUMMARY_FILE"
log "Migration result (if any): $MIGRATION_RESULT_FILE"
log "Collected logs: $DEST/logs/"

# Exit non-zero if migration or services failed
if [[ "$MIG_EXIT" != "0" ]] || [[ $APP_STATUS -ne 0 ]]; then
  echo "One or more steps reported problems (migration_exit=$MIG_EXIT, service_ok=$( [[ $APP_STATUS -eq 0 ]] && echo true || echo false ) ). See $SUMMARY_FILE and logs for details."
  exit 2
fi

exit 0
