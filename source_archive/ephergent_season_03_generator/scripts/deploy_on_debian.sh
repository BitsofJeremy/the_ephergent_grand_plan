#!/usr/bin/env bash
# deploy_on_debian.sh
# Run as root on a fresh Debian/Ubuntu VM to install dependencies and deploy the Ephergent app.
# Usage: sudo bash deploy_on_debian.sh [--dest /opt/ephergent_season_03_generator] [--git <repo-url>] [--share samba|nfs] [--env /path/to/.env]

set -euo pipefail
PS4='+(${BASH_SOURCE##*/}:${LINENO}) '

DEST="/opt/ephergent_season_03_generator"
GIT_REPO="git@github.com:ephergent/ephergent_season_03_generator.git"
SHARE_TYPE="samba"
ENV_FILE="/root/.env"
POSTGRES_PASSWORD="ephergent123"
POSTGRES_DB="ephergent_season_03"
POSTGRES_USER="ephergent"
APP_USER="ephergent"
PYTHON_BIN="python3"
VENV_DIR=".venv"
# Optional Samba password (CLI or file). Prefer file input for security.
SAMBA_PASSWORD="ephergent"
SAMBA_PASSWORD_FILE=""
# New: secrets source directory (default is /root/secrets). Can be overridden with --secrets-src
SECRETS_SRC="/root/secrets"

print_usage() {
  cat <<EOF
Usage: sudo bash $0 [options]

Options:
  --dest PATH         Destination install path (default: /opt/ephergent_season_03_generator)
  --git REPO_URL      Optional: git repository URL to clone into destination
  --share samba|nfs   Share type to configure (default: samba)
  --env /path/.env    Optional: .env file to copy into app directory (recommended)
  --samba-password 'pw'    Optional (less secure): provide samba password on CLI
  --samba-password-file /path/to/file  Optional (recommended): file (mode 600) containing samba password
  --secrets-src /path/to/secrets  Optional: directory containing secrets to copy into the app (default: /root/secrets)
  -h, --help          Show this help

Example:
  sudo bash $0 --git https://github.com/you/repo.git --dest /opt/ephergent_season_03_generator --share samba --env /root/.env --samba-password-file /root/.smbpass --secrets-src /root/secrets
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      DEST="$2"; shift 2;;
    --git)
      GIT_REPO="$2"; shift 2;;
    --share)
      SHARE_TYPE="$2"; shift 2;;
    --env)
      ENV_FILE="$2"; shift 2;;
    --samba-password)
      SAMBA_PASSWORD="$2"; shift 2;;
    --samba-password-file)
      SAMBA_PASSWORD_FILE="$2"; shift 2;;
    --secrets-src)
      SECRETS_SRC="$2"; shift 2;;
    -h|--help)
      print_usage; exit 0;;
    *)
      echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

# If samba password file provided, read it (prefer file over CLI)
if [[ -n "$SAMBA_PASSWORD_FILE" ]]; then
  if [[ -f "$SAMBA_PASSWORD_FILE" ]]; then
    # warn if file perms are too open
    perms=$(stat -c "%a" "$SAMBA_PASSWORD_FILE" 2>/dev/null || echo "")
    if [[ "$perms" != "600" && "$perms" != "400" ]]; then
      echo "Warning: Samba password file $SAMBA_PASSWORD_FILE should be mode 600 (owner read/write) for security. Current mode: $perms"
    fi
    SAMBA_PASSWORD=$(tr -d '\n' < "$SAMBA_PASSWORD_FILE" )
  else
    echo "Warning: Samba password file $SAMBA_PASSWORD_FILE not found; ignoring"
  fi
fi

echo "Deploying Ephergent app to: $DEST"
echo "Share type: $SHARE_TYPE"

# Basic checks
if [[ $(id -u) -ne 0 ]]; then
  echo "This script must be run as root." >&2
  exit 1
fi

# Detect OS
if [[ -f /etc/debian_version ]]; then
  echo "Detected Debian-based system"
else
  echo "This script is intended for Debian/Ubuntu systems." >&2
  exit 1
fi

apt_update_and_install() {
  echo "Updating apt and installing packages..."
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git curl ca-certificates build-essential \
    openssh-client \
    $PYTHON_BIN $PYTHON_BIN-venv \
    python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib redis-server \
    samba smbclient \
    nginx ffmpeg rsync

  # On minimal installs the package name python3-venv may already be satisfied; ignore failures above
}

create_app_user_and_dirs() {
  echo "Creating application user and directories..."
  if ! id -u "$APP_USER" >/dev/null 2>&1; then
    # Create a regular user (not system) so you can SSH in as 'ephergent' and give it sudo later if desired.
    useradd --create-home --home-dir /home/$APP_USER --shell /bin/bash $APP_USER
    echo "$APP_USER created"
  else
    echo "User $APP_USER already exists"
  fi

  mkdir -p "$DEST"
  chown -R $APP_USER:$APP_USER "$DEST"
  chmod 755 "$DEST"

  mkdir -p $DEST/logs
  mkdir -p $DEST/upload_storage
  mkdir -p $DEST/stories_archive
  chown -R $APP_USER:$APP_USER $DEST
}

fetch_application() {
  if [[ -n "$GIT_REPO" ]]; then
    echo "Cloning git repository $GIT_REPO into $DEST"
    # If cloning over SSH from github, ensure the app user's known_hosts includes github.com's host key
    if [[ "$GIT_REPO" == git@github.com:* || "$GIT_REPO" == ssh://git@github.com/* ]]; then
      echo "Ensuring $APP_USER's ~/.ssh/known_hosts has GitHub host key"
      su - $APP_USER -c "bash -lc 'mkdir -p ~/.ssh; chmod 700 ~/.ssh; ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null || true; chmod 644 ~/.ssh/known_hosts'"
    fi
    # Perform clone as the application user so SSH keys / known_hosts configured for that user are used
    su - $APP_USER -c "bash -lc 'rm -rf \"$DEST\"/* || true; git clone --depth 1 \"$GIT_REPO\" \"$DEST\"'"
    # Ensure correct ownership after clone
    chown -R $APP_USER:$APP_USER "$DEST"
  else
    echo "No git repository provided. Assuming application code is already placed at $DEST"
  fi

  if [[ -n "$ENV_FILE" ]]; then
    echo "Copying env file $ENV_FILE to $DEST/.env"
    cp -f "$ENV_FILE" "$DEST/.env"
    chown $APP_USER:$APP_USER "$DEST/.env"
    chmod 600 "$DEST/.env"
  fi
}

# New: copy secrets placed at SECRETS_SRC into the app directory and set secure ownership/permissions
copy_root_secrets() {
  SRC="$SECRETS_SRC"
  DEST_SECRETS_DIR="$DEST/secrets"

  # Required YouTube secret filenames (assumption: client_secret.json and token.json)
  REQUIRED_SECRETS=("client_secret.json" "token.json")

  if [[ -d "$SRC" ]]; then
    echo "Found secrets at $SRC — verifying required files..."

    missing=()
    for f in "${REQUIRED_SECRETS[@]}"; do
      if [[ ! -f "$SRC/$f" ]]; then
        missing+=("$f")
      fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
      echo "Error: required secret file(s) missing in $SRC: ${missing[*]}" >&2
      echo "Please copy the YouTube secret files (e.g. client_secret.json and token.json) to $SRC before running the deploy." >&2
      exit 1
    fi

    echo "All required secret files present — copying to $DEST_SECRETS_DIR"
    mkdir -p "$DEST_SECRETS_DIR"

    # Prefer rsync if available for a reliable, idempotent copy; otherwise fall back to cp -a
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete --chmod=Du=rwx,Dg=,Do=,Fu=rw,Fg=,Fo= "$SRC/" "$DEST_SECRETS_DIR/"
    else
      # Use tar piped to preserve attributes and be robust for large directories
      (cd "$SRC" && tar cf - .) | (cd "$DEST_SECRETS_DIR" && tar xpf -) || cp -a "$SRC/." "$DEST_SECRETS_DIR/"
    fi

    # Ensure the application user owns the secrets and make permissions restrictive:
    # directories -> 700, files -> 600
    chown -R $APP_USER:$APP_USER "$DEST_SECRETS_DIR" || true
    find "$DEST_SECRETS_DIR" -type d -exec chmod 700 {} \; || true
    find "$DEST_SECRETS_DIR" -type f -exec chmod 600 {} \; || true

    echo "Secrets copied to $DEST_SECRETS_DIR and secured (owner: $APP_USER, dirs:700, files:600)"
  else
    echo "No secrets directory at $SRC; skipping secrets copy"
  fi
}

setup_python_env() {
  echo "Setting up Python virtual environment and installing dependencies..."
  su - $APP_USER -c "bash -lc 'cd $DEST && $PYTHON_BIN -m venv $VENV_DIR && source $VENV_DIR/bin/activate && pip install --upgrade pip setuptools wheel'"

  # Ensure gunicorn is available in the venv for the web service
  su - $APP_USER -c "bash -lc 'cd $DEST && source $VENV_DIR/bin/activate && pip install gunicorn || true'"

  # Prefer requirements.txt, fallback to pyproject-based install
  if [[ -f "$DEST/requirements.txt" ]]; then
    echo "Installing from requirements.txt"
    su - $APP_USER -c "bash -lc 'cd $DEST && source $VENV_DIR/bin/activate && pip install -r requirements.txt'"
  elif [[ -f "$DEST/pyproject.toml" ]]; then
    echo "Installing package from pyproject.toml (PEP 517/518)"
    su - $APP_USER -c "bash -lc 'cd $DEST && source $VENV_DIR/bin/activate && pip install . || pip install -e .'"
  else
    echo "No requirements.txt or pyproject.toml found; skipping pip install. You may need to install dependencies manually."
  fi
}

setup_postgres() {
  echo "Configuring PostgreSQL database and user..."
  # Ensure postgres service is running (silence extraneous output that can confuse psql)
  systemctl enable --now postgresql >/dev/null 2>&1 || true

  # Wait for postgres to be actually ready
  if ! wait_for_postgres; then
    echo "Postgres did not become ready; continuing but commands may fail"
  fi

  # Ensure required variables are set
  : "${POSTGRES_USER:?POSTGRES_USER not set}"
  : "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set}"
  : "${POSTGRES_DB:?POSTGRES_DB not set}"

  # Use psql in a non-interactive, quiet mode and test for existence before creating
  # Create role/user if it doesn't exist
  ROLE_EXISTS=$(sudo -u postgres psql -X -q -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$POSTGRES_USER'" || true)
  if [[ -z "${ROLE_EXISTS//[[:space:]]/}" ]]; then
    echo "Creating PostgreSQL role: $POSTGRES_USER"
    sudo -u postgres psql -X -v ON_ERROR_STOP=1 -c "CREATE ROLE \"$POSTGRES_USER\" LOGIN PASSWORD '$POSTGRES_PASSWORD';"
  else
    echo "Postgres role $POSTGRES_USER already exists"
  fi

  # Create database if it doesn't exist
  DB_EXISTS=$(sudo -u postgres psql -X -q -tAc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" || true)
  if [[ -z "${DB_EXISTS//[[:space:]]/}" ]]; then
    echo "Creating PostgreSQL database: $POSTGRES_DB"
    sudo -u postgres psql -X -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\";"
  else
    echo "Postgres database $POSTGRES_DB already exists"
  fi

  echo "Postgres user and database ensured (user: $POSTGRES_USER, db: $POSTGRES_DB)"
}

wait_for_postgres() {
  echo "Waiting for PostgreSQL to become available (up to 60s)..."
  for i in {1..60}; do
    if sudo -u postgres pg_isready -q; then
      echo "Postgres is ready"
      return 0
    fi
    sleep 1
  done
  echo "Warning: Postgres did not become ready after 60 seconds"
  return 1
}

setup_redis() {
  echo "Enabling and starting redis-server..."
  systemctl enable --now redis-server
}

create_systemd_services() {
  echo "Creating systemd service files for web, worker, and MCP server..."

  WEB_ENV_FILE="/etc/default/ephergent_web"
  WORKER_ENV_FILE="/etc/default/ephergent_worker"
  MCP_ENV_FILE="/etc/default/ephergent_mcp"

  cat > $WEB_ENV_FILE <<EOF
# Environment vars for ephergent web service
FLASK_ENV=production
# Bind to localhost; nginx reverse-proxy will serve externally
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=false
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB
LOG_LEVEL=INFO
LOG_FILE=$DEST/logs/application.log
SECRET_KEY=
# Monitoring configuration
GRAFANA_URL=http://10.0.0.99:3000
# Add any other env vars (GEMINI_API_KEY, GHOST_API_KEY, etc.) in $DEST/.env or here
EOF

  cat > $WORKER_ENV_FILE <<EOF
# Environment vars for ephergent worker
FLASK_ENV=production
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB
LOG_LEVEL=INFO
LOG_FILE=$DEST/logs/worker.log
WORKER_SLEEP_INTERVAL=5
WORKER_TIMEOUT_MINUTES=30
EOF

  cat > $MCP_ENV_FILE <<EOF
# Environment vars for ephergent MCP server (SSE transport)
EPHERGENT_API_URL=http://127.0.0.1:5000
# IMPORTANT: Set EPHERGENT_API_KEY in $DEST/.env (this is required for MCP server to start)
# Generate an admin API key via the web interface: Profile → API Keys
MCP_HOST=0.0.0.0
MCP_PORT=8765
LOG_LEVEL=INFO
EOF

  chown root:root $WEB_ENV_FILE $WORKER_ENV_FILE $MCP_ENV_FILE
  chmod 644 $WEB_ENV_FILE $WORKER_ENV_FILE $MCP_ENV_FILE

  # Ensure environment files are world-readable so the app user (and migrations run as that user) can source them
  # These files don't hold secrets; $DEST/.env is used for secrets and remains 600 for safety
  chmod 644 $WEB_ENV_FILE $WORKER_ENV_FILE $MCP_ENV_FILE

  # Web service unit
  cat > /etc/systemd/system/ephergent-web.service <<EOF
[Unit]
Description=Ephergent Season 03 Web Application (Gunicorn)
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$DEST
EnvironmentFile=$WEB_ENV_FILE
# Also load optional application .env if present (ignore if missing)
EnvironmentFile=-$DEST/.env
# Use gunicorn to run the Flask WSGI app
ExecStart=$DEST/$VENV_DIR/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  # Worker service unit
  cat > /etc/systemd/system/ephergent-worker.service <<EOF
[Unit]
Description=Ephergent Season 03 Background Worker
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$DEST
EnvironmentFile=$WORKER_ENV_FILE
# Also load optional application .env if present (ignore if missing)
EnvironmentFile=-$DEST/.env
ExecStart=$DEST/$VENV_DIR/bin/python $DEST/worker.py --continuous
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  # MCP server service unit (SSE transport for Claude Desktop integration)
  cat > /etc/systemd/system/ephergent-mcp.service <<EOF
[Unit]
Description=Ephergent MCP Server (SSE Transport)
After=network.target ephergent-web.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$DEST
EnvironmentFile=$MCP_ENV_FILE
# Load API key from .env (EPHERGENT_API_KEY is required)
EnvironmentFile=-$DEST/.env
ExecStart=$DEST/$VENV_DIR/bin/python $DEST/mcp_server/mcp_server_sse.py
Restart=always
RestartSec=5
# Restart strategy: If MCP server fails due to missing API key, don't restart indefinitely
StartLimitBurst=3
StartLimitIntervalSec=60

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable --now ephergent-web ephergent-worker ephergent-mcp
}

configure_nfs() {
  echo "Configuring NFS export for $DEST"
  apt-get install -y nfs-kernel-server
  EXPORT_LINE="$DEST *(rw,sync,no_root_squash,no_subtree_check)"

  # Append export line only if not present
  if ! grep -Fq "$DEST " /etc/exports; then
    echo "$EXPORT_LINE" >> /etc/exports
    exportfs -ra
    echo "NFS export added"
  else
    echo "NFS export for $DEST already exists in /etc/exports"
  fi

  systemctl enable --now nfs-kernel-server
  echo "NFS configured. On macOS, mount with: sudo mount -t nfs <vm-ip>:$DEST /path/to/mount"
}

configure_samba() {
  echo "Configuring Samba share for $DEST"
  apt-get install -y samba
  SAMBA_CONF="/etc/samba/smb.conf"

  # Create a backup of the smb.conf
  cp -n $SAMBA_CONF ${SAMBA_CONF}.orig || true

  # Add share config only if not already present
  if ! grep -q "\[ephergent_app\]" $SAMBA_CONF; then
    cat >> $SAMBA_CONF <<EOF

[ephergent_app]
  path = $DEST
  browsable = yes
  read only = no
  create mask = 0660
  directory mask = 0770
  force user = $APP_USER
EOF
    echo "Samba share appended to $SAMBA_CONF"
  else
    echo "Samba share already present in $SAMBA_CONF"
  fi

  # Do not try to set samba password non-interactively. Instruct the admin to run smbpasswd.
  if ! pdbedit -L | grep -q "^$APP_USER:"; then
    if [[ -n "$SAMBA_PASSWORD" ]]; then
      echo "Adding Samba user $APP_USER with provided password"
      (echo "$SAMBA_PASSWORD"; echo "$SAMBA_PASSWORD") | smbpasswd -a -s "$APP_USER"
    else
      echo "Samba user $APP_USER not present in Samba DB. Run 'sudo smbpasswd -a $APP_USER' to add and set a password."
    fi
  else
    echo "Samba user $APP_USER already exists"
  fi

  systemctl restart smbd
  systemctl enable smbd
  echo "Samba share configured. On macOS, connect with: smb://<vm-ip>/ephergent_app"
}

install_prometheus() {
  echo "Installing Prometheus for metrics collection..."

  # Install Prometheus from official apt repository
  apt-get install -y prometheus prometheus-node-exporter

  # Create Prometheus configuration directory
  mkdir -p /etc/prometheus/targets

  # Prometheus will be configured via config file created later
  systemctl enable prometheus
  systemctl enable prometheus-node-exporter

  echo "Prometheus installed successfully"
}

install_grafana() {
  echo "Installing Grafana for metrics visualization..."

  # Ensure apt cache is fresh and install prerequisites
  apt-get update -y
  apt-get install -y wget apt-transport-https software-properties-common || \
    apt-get install -y wget apt-transport-https

  # Add Grafana GPG key and repository
  wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key
  echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

  apt-get update -y
  apt-get install -y grafana

  # Enable Grafana (start later after provisioning is configured)
  systemctl enable grafana-server

  echo "Grafana installed successfully - will be available at http://<vm-ip>:3000"
  echo "Default credentials: admin/admin (change on first login)"
}

create_prometheus_config() {
  echo "Creating Prometheus configuration..."

  PROM_CONFIG="/etc/prometheus/prometheus.yml"

  # Backup original config
  if [ -f "$PROM_CONFIG" ]; then
    cp "$PROM_CONFIG" "${PROM_CONFIG}.orig"
  fi

  cat > $PROM_CONFIG <<'PROMEOF'
# Prometheus configuration for Ephergent Story Generator
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'ephergent-vm'
    environment: 'production'

# Alertmanager configuration (optional, configure if needed)
# alerting:
#   alertmanagers:
#     - static_configs:
#         - targets: ['localhost:9093']

# Load rules once and periodically evaluate them
rule_files:
  - "/etc/prometheus/rules/*.yml"

# Scrape configurations
scrape_configs:
  # Scrape Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          instance: 'prometheus'

  # Scrape Node Exporter for system metrics
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']
        labels:
          instance: 'ephergent-vm'

  # Scrape Ephergent Flask application metrics
  - job_name: 'ephergent_app'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:5000']
        labels:
          instance: 'ephergent-app'
          service: 'story-generator'

    # Scrape every 10 seconds for application metrics
    scrape_interval: 10s

  # Scrape Nginx metrics (if nginx-prometheus-exporter is installed)
  # - job_name: 'nginx'
  #   static_configs:
  #     - targets: ['localhost:9113']

  # Scrape PostgreSQL metrics (if postgres_exporter is installed)
  # - job_name: 'postgresql'
  #   static_configs:
  #     - targets: ['localhost:9187']
PROMEOF

  chown prometheus:prometheus $PROM_CONFIG
  chmod 644 $PROM_CONFIG

  # Create rules directory
  mkdir -p /etc/prometheus/rules
  chown -R prometheus:prometheus /etc/prometheus/rules

  # Restart Prometheus to apply configuration
  systemctl restart prometheus

  echo "Prometheus configuration created at $PROM_CONFIG"
}

create_grafana_datasource() {
  echo "Configuring Grafana Prometheus datasource..."

  GRAFANA_PROVISIONING="/etc/grafana/provisioning/datasources"
  mkdir -p $GRAFANA_PROVISIONING

  cat > $GRAFANA_PROVISIONING/prometheus.yml <<'GRAFANAEOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
GRAFANAEOF

  chown -R grafana:grafana /etc/grafana/provisioning

  echo "Grafana datasource configured"
}

import_grafana_dashboards() {
  echo "Importing Grafana dashboards..."

  # Create dashboards provisioning directory
  GRAFANA_DASHBOARDS_PROVISIONING="/etc/grafana/provisioning/dashboards"
  GRAFANA_DASHBOARDS_DIR="/var/lib/grafana/dashboards"

  mkdir -p $GRAFANA_DASHBOARDS_PROVISIONING
  mkdir -p $GRAFANA_DASHBOARDS_DIR

  # Create dashboard provisioning config
  cat > $GRAFANA_DASHBOARDS_PROVISIONING/ephergent.yml <<'DASHBOARDEOF'
apiVersion: 1

providers:
  - name: 'Ephergent Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
DASHBOARDEOF

  # Copy dashboard JSON from app to Grafana directory
  if [ -f "$DEST/monitoring/grafana-dashboard.json" ]; then
    echo "Copying Ephergent dashboard JSON to Grafana..."
    cp "$DEST/monitoring/grafana-dashboard.json" "$GRAFANA_DASHBOARDS_DIR/ephergent-story-generator.json"
    chown grafana:grafana "$GRAFANA_DASHBOARDS_DIR/ephergent-story-generator.json"
    chmod 644 "$GRAFANA_DASHBOARDS_DIR/ephergent-story-generator.json"
    echo "Dashboard JSON copied successfully"
  else
    echo "Warning: Dashboard JSON not found at $DEST/monitoring/grafana-dashboard.json"
  fi

  # Set correct ownership
  chown -R grafana:grafana $GRAFANA_DASHBOARDS_PROVISIONING
  chown -R grafana:grafana $GRAFANA_DASHBOARDS_DIR

  # Start Grafana if not running, otherwise restart to apply changes
  if systemctl is-active --quiet grafana-server; then
    systemctl restart grafana-server
  else
    systemctl start grafana-server
  fi

  # Wait for Grafana to be ready before proceeding
  echo "Waiting for Grafana to be ready..."
  for i in {1..30}; do
    if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
      echo "Grafana is ready"
      break
    fi
    sleep 1
  done

  echo "Grafana dashboards imported successfully"
}

configure_grafana_security() {
  echo "Configuring Grafana security settings for iframe embedding..."

  GRAFANA_INI="/etc/grafana/grafana.ini"

  # Backup original grafana.ini if not already backed up
  if [ -f "$GRAFANA_INI" ] && [ ! -f "${GRAFANA_INI}.orig" ]; then
    cp "$GRAFANA_INI" "${GRAFANA_INI}.orig"
    echo "Backed up original Grafana config to ${GRAFANA_INI}.orig"
  fi

  # Check if security settings already configured
  if grep -q "^allow_embedding = true" "$GRAFANA_INI"; then
    echo "Grafana security settings already configured"
    return 0
  fi

  # Add security configuration to allow iframe embedding
  # This is required for the admin portal to display Grafana dashboards
  cat >> $GRAFANA_INI <<'GRAFANAINIEOF'

# ==============================================================================
# Security settings for Ephergent admin portal iframe embedding
# ==============================================================================

[security]
# Allow Grafana dashboards to be embedded in iframes
allow_embedding = true

# Cookie SameSite policy (lax allows same-origin embedding)
cookie_samesite = lax

# Cookie secure flag (set to false for HTTP, true for HTTPS)
cookie_secure = false
GRAFANAINIEOF

  chown grafana:grafana $GRAFANA_INI
  chmod 640 $GRAFANA_INI

  # Restart Grafana to apply security changes
  if systemctl is-active --quiet grafana-server; then
    systemctl restart grafana-server
    echo "Grafana restarted to apply security configuration"
  else
    echo "Grafana not running yet, will start after all configuration is complete"
  fi

  echo "Grafana security configuration completed - iframe embedding enabled"
}

create_nginx_config() {
  echo "Creating nginx reverse-proxy configuration"
  # Create a simple site that proxies to the local Flask app
  NGINX_SITE="/etc/nginx/sites-available/ephergent"
  cat > $NGINX_SITE <<EOF
server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 200M;

    location / {
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:5000;
        proxy_read_timeout 120s;
        proxy_connect_timeout 5s;
    }

    # MCP Server SSE endpoint (for Claude Desktop integration)
    location /mcp/ {
        proxy_pass http://127.0.0.1:8765/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }

    # Optional: expose static files directly if you prefer
    location /static/ {
        alias ${DEST}/ephergent_generator/static/;
        access_log off;
        expires 1d;
    }

    # Prometheus metrics endpoint (accessible via /prometheus/)
    location /prometheus/ {
        proxy_pass http://localhost:9090/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Grafana dashboard (accessible via /grafana/)
    location /grafana/ {
        proxy_pass http://localhost:3000/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support for Grafana live updates
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

  ln -sf $NGINX_SITE /etc/nginx/sites-enabled/ephergent
  # Remove default if present
  if [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default
  fi

  nginx -t && systemctl restart nginx && systemctl enable nginx
}

run_migrations() {
  echo "Running file-based data migrations into database (personality_prompts_s3.json + universe prompt)"

  # Ensure Postgres is available first
  wait_for_postgres || true

  # Migration marker to avoid re-running on subsequent deploys
  MIGRATION_MARKER="$DEST/.migrations_done"
  if [ -f "$MIGRATION_MARKER" ]; then
    echo "Migration marker found at $MIGRATION_MARKER — skipping migrations"
    return 0
  fi

  # Run as app user inside venv; source environment from /etc/default/ephergent_web and $DEST/.env so create_app uses production DB URL
  if [ -x "$DEST/$VENV_DIR/bin/python" ] && [ -f "$DEST/scripts/run_migrations.py" ]; then
    # Run migrations as the app user. Capture stdout/stderr for debugging and set PYTHONPATH to include project root
    su - $APP_USER -c "bash -lc 'cd $DEST && if [ -f /etc/default/ephergent_web ]; then set -a; source /etc/default/ephergent_web; fi; if [ -f $DEST/.env ]; then set -a; source $DEST/.env; fi; export MIGRATION_RESULT_FILE=\"$DEST/migration_result.json\"; PYTHONPATH=\"$DEST\" $DEST/$VENV_DIR/bin/python scripts/run_migrations.py > /tmp/eph_mig_out 2>&1; echo exit_code:\$? > /tmp/eph_mig_exit'"

    MIG_EXIT=$(cat /tmp/eph_mig_exit 2>/dev/null | sed -n 's/^exit_code:\([0-9][0-9]*\)/\1/p' || true)
    rm -f /tmp/eph_mig_exit || true
    # Save the migrations stdout/stderr next to the app for inspection
    if [ -f /tmp/eph_mig_out ]; then
      cp /tmp/eph_mig_out "$DEST/logs/migration_output.log" 2>/dev/null || true
      chown $APP_USER:$APP_USER "$DEST/logs/migration_output.log" 2>/dev/null || true
      rm -f /tmp/eph_mig_out || true
    fi

    if [[ "$MIG_EXIT" == "0" ]]; then
      echo "Migration script completed successfully; marking as done: $MIGRATION_MARKER"
      touch "$MIGRATION_MARKER"
      chown $APP_USER:$APP_USER "$MIGRATION_MARKER" || true
    else
      echo "Migration script exited with code: ${MIG_EXIT:-unknown}. Check logs for details."
    fi

    echo "Migration script executed (check logs for details)."
  else
    echo "Migration script or Python venv not found; skipping migration."
  fi
}

final_notes() {
  echo "======================================================================"
  echo "                    DEPLOYMENT COMPLETED SUCCESSFULLY"
  echo "======================================================================"
  echo ""
  echo "📦 Application:"
  echo "   Location: $DEST"
  echo "   Web UI: http://<vm-ip>/"
  echo "   Systemd services: ephergent-web, ephergent-worker, ephergent-mcp"
  echo ""
  echo "📊 Monitoring & Observability:"
  echo "   Prometheus: http://<vm-ip>/prometheus/ (or :9090 direct)"
  echo "   Grafana: http://<vm-ip>/grafana/ (or :3000 direct)"
  echo "   Grafana login: admin/admin (CHANGE ON FIRST LOGIN)"
  echo "   Admin Portal Grafana: http://<vm-ip>/admin/monitoring/grafana"
  echo "   📋 Ephergent Dashboard: Auto-imported and ready to use!"
  echo "   Metrics endpoint: http://<vm-ip>/metrics"
  echo "   Health checks:"
  echo "     - Liveness:  http://<vm-ip>/api/health/liveness"
  echo "     - Readiness: http://<vm-ip>/api/health/readiness"
  echo "     - Full:      http://<vm-ip>/api/health/full"
  echo ""
  echo "💾 Database:"
  echo "   PostgreSQL: user=$POSTGRES_USER db=$POSTGRES_DB"
  echo "   Connection: localhost:5432"
  echo ""
  echo "🔌 File Sharing:"
  echo "   Samba: smb://<vm-ip>/ephergent_app"
  echo "   NFS: <vm-ip>:$DEST"
  echo ""
  echo "⚙️  IMPORTANT - Required Configuration:"
  echo "   Add these environment variables to $DEST/.env:"
  echo "   - GEMINI_API_KEY: Required for story generation"
  echo "   - SECRET_KEY: Required for Flask sessions (generate random string)"
  echo "   - EPHERGENT_API_KEY: For MCP server (generate via web UI)"
  echo "   - GHOST_API_KEY, GHOST_ADMIN_KEY, GHOST_DOMAIN: Optional for blog publishing"
  echo ""
  echo "🔗 MCP Server Setup (Claude Desktop integration):"
  echo "   1. Log in to web interface: http://<vm-ip>"
  echo "   2. Navigate to Profile → API Keys"
  echo "   3. Create an admin API key"
  echo "   4. Add EPHERGENT_API_KEY=ephg_your_key to $DEST/.env"
  echo "   5. Restart: systemctl restart ephergent-mcp"
  echo "   6. Endpoints:"
  echo "      - Direct: http://<vm-ip>:8765/sse"
  echo "      - Via nginx: http://<vm-ip>/mcp/sse (recommended)"
  echo ""
  echo "🔧 Service Management:"
  echo "   Start/stop: systemctl [start|stop|status] <service>"
  echo "   Services: ephergent-web, ephergent-worker, ephergent-mcp, nginx, prometheus, grafana-server"
  echo "   View logs: journalctl -u <service> -f"
  echo ""
  echo "📈 Next Steps:"
  echo "   1. Configure environment variables in $DEST/.env"
  echo "   2. Restart services: systemctl restart ephergent-web ephergent-worker ephergent-mcp"
  echo "   3. Log in to Grafana and verify dashboard was auto-imported:"
  echo "      - Go to http://<vm-ip>:3000"
  echo "      - Login with admin/admin (change password)"
  echo "      - Navigate to Dashboards → Ephergent Story Generator"
  echo "      - Or use admin portal: http://<vm-ip>/admin/monitoring/grafana"
  echo "   4. Verify metrics: curl http://<vm-ip>/metrics"
  echo "   5. Check health: curl http://<vm-ip>/api/health/full"
  echo ""
  echo "======================================================================"
}

# Execution order
apt_update_and_install
create_app_user_and_dirs
fetch_application
copy_root_secrets
setup_python_env
setup_postgres
setup_redis

# Install and configure monitoring stack
install_prometheus
install_grafana
create_prometheus_config
create_grafana_datasource
import_grafana_dashboards
configure_grafana_security

# Create and start application services
create_systemd_services

# Configure file sharing (idempotent)
configure_samba
configure_nfs

# Configure nginx reverse proxy with monitoring endpoints
create_nginx_config

# Run migrations after all services are available
run_migrations

final_notes

exit 0
