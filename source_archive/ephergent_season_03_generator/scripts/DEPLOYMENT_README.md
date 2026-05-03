Deployment README — Ephergent Season 03 Generator

Overview
--------
This document explains how the automated Debian deploy script (root-run) works, what it installs and configures, and how to verify and maintain the resulting services.

Files
-----
- `scripts/deploy_on_debian.sh` — Main root-run provisioning + deployment script.
- `scripts/run_migrations.py` — Migration runner that imports characters and universe prompt into the DB (writes a JSON result file).
- `wsgi.py` — WSGI entrypoint used by Gunicorn (exposes `app`).
- `scripts/DEPLOYMENT_README.md` — This file.

High-level what the deploy script does
-------------------------------------
- Installs system packages: git, build-essential, Python 3, venv tools, PostgreSQL, Redis, Samba, NFS server, nginx.
- Creates a non-system application user `ephergent` (so you can SSH into it).
- Creates application directories under `DEST` (default: `/opt/ephergent_season_03_generator`).
- Optionally clones your git repository into `DEST` (use `--git`).
- Creates a Python virtualenv in `DEST/.venv`, installs dependencies (requirements or pyproject) and installs `gunicorn`.
- Creates and enables systemd services:
  - `ephergent-web` (Gunicorn binding 127.0.0.1:5000, user: `ephergent`)
  - `ephergent-worker` (runs `worker.py --continuous`, user: `ephergent`)
- Configures nginx as a reverse proxy on port 80 (proxy -> 127.0.0.1:5000).
- Configures both Samba (`[ephergent_app]`) and NFS exports for `DEST` (idempotent appends).
- Ensures PostgreSQL and Redis are running and creates the `ephergent` DB user + database.
- Runs file-based migrations (character JSON + universe prompt) once and writes a JSON migration result file for easy inspection.

Prerequisites & assumptions
---------------------------
- Target host: Debian/Ubuntu-based Linux.
- You will run the deploy script as root (script checks this and will exit if not root).
- If you want to SSH into the host as `ephergent`, the script creates a normal user named `ephergent` (not a system user). You can add that user to `sudo` if desired.
- The app expects configuration values to be provided via `/etc/default/ephergent_web` and optionally `DEST/.env` (the deploy script creates `/etc/default/ephergent_web` automatically).

How to run (example)
--------------------
Place your application code on the VM at `DEST` or have the script clone it via `--git`.
Run the deploy script as root with optional parameters:

```bash
# Basic run (uses default DEST = /opt/ephergent_season_03_generator)
sudo bash scripts/deploy_on_debian.sh --env /root/.env

# With git clone into DEST
git clone https://github.com/you/yourrepo.git /opt/ephergent_season_03_generator
sudo bash scripts/deploy_on_debian.sh --dest /opt/ephergent_season_03_generator --git https://github.com/you/yourrepo.git --env /root/.env
```

Parameters
----------
- `--dest PATH` — Destination path for the application (default: `/opt/ephergent_season_03_generator`).
- `--git REPO_URL` — Optional repo to clone into `DEST`.
- `--env /path/.env` — Optional `.env` file to copy to `DEST/.env` (recommended for secrets).
- `--share samba|nfs` — Not required; the script configures both Samba and NFS by default.

What the script creates
-----------------------
- Systemd units: `/etc/systemd/system/ephergent-web.service` (Gunicorn) and `/etc/systemd/system/ephergent-worker.service`.
- Environment files: `/etc/default/ephergent_web` and `/etc/default/ephergent_worker`.
- Samba share entry in `/etc/samba/smb.conf` under `[ephergent_app]`.
- NFS export entry in `/etc/exports` (appended once for `DEST`).
- Python venv at `$DEST/.venv` and installs `gunicorn` + project requirements.

Migration behavior (characters + universe prompt)
------------------------------------------------
- The deploy script runs `scripts/run_migrations.py` as the `ephergent` user in the app venv (after waiting for Postgres readiness).
- `run_migrations.py` calls `MigrationService.migrate_all()` and writes a JSON result file named `migration_result.json` in the project root (inside `DEST`) by default.
- On successful migration, the deploy script touches `$DEST/.migrations_done` so migrations will not run again on subsequent deploys.
- Migration result JSON location (default):

```
/opt/ephergent_season_03_generator/migration_result.json
```

Inspecting the migration result
-------------------------------
The JSON contains at least these fields:
- `started_at` (ISO UTC)
- `finished_at` (ISO UTC)
- `success` (boolean)
- `exit_code` (0 success, 2 partial migration failures/present, 1 exception)
- `result` (the raw dict returned by `MigrationService.migrate_all()`)

```bash
# Example:
cat /opt/ephergent_season_03_generator/migration_result.json | python -m json.tool
```

Common verification commands
----------------------------
Systemd and logs
```bash
sudo systemctl status ephergent-web ephergent-worker nginx postgresql redis-server smbd nfs-kernel-server
sudo journalctl -u ephergent-web -n 200 --no-pager
sudo journalctl -u ephergent-worker -n 200 --no-pager
```
Gunicorn listening
```bash
ss -tlnp | grep 127.0.0.1:5000 || ss -tlnp | grep 5000
```
Nginx test
```bash
curl -v http://127.0.0.1/
```
Database checks
```bash
sudo -u postgres psql -c '\l'
sudo -u postgres psql -c '\du'
# Check imported characters (update table name if different):
sudo -u postgres psql -d ephergent_season_03 -c "SELECT COUNT(*) FROM characters;"
```
Logs
```bash
# Application log (configure location with /etc/default/ephergent_web LOG_FILE)
tail -n 200 /opt/ephergent_season_03_generator/logs/application.log
```

Samba and NFS mounting (examples)
---------------------------------
macOS — Samba (recommended for macOS)
```bash
# Finder -> Connect to Server -> smb://<vm-ip>/ephergent_app
# or from terminal:
mkdir -p /Volumes/ephergent_app
mount_smbfs //ephergent@<vm-ip>/ephergent_app /Volumes/ephergent_app
```
macOS — NFS
```bash
sudo mkdir -p /Volumes/ephergent_nfs
sudo mount -t nfs <vm-ip>:/opt/ephergent_season_03_generator /Volumes/ephergent_nfs
```
Linux — Samba or NFS
```bash
sudo apt install cifs-utils nfs-common
sudo mount -t cifs -o username=ephergent //vm-ip/ephergent_app /mnt/ephergent_app
sudo mount -t nfs vm-ip:/opt/ephergent_season_03_generator /mnt/ephergent_nfs
```
Note: run `sudo smbpasswd -a ephergent` on the VM to set the Samba password for user `ephergent`.

SSH & sudo for `ephergent` user
--------------------------------
The script creates a standard user `ephergent`. To allow SSH login and sudo:

```bash
# As root on the VM, add your public key then add to sudoers if desired
mkdir -p /home/ephergent/.ssh
echo 'ssh-rsa AAAA... yourkey' >> /home/ephergent/.ssh/authorized_keys
chown -R ephergent:ephergent /home/ephergent/.ssh
chmod 700 /home/ephergent/.ssh
chmod 600 /home/ephergent/.ssh/authorized_keys
# To give sudo rights:
usermod -aG sudo ephergent
# Or passwordless sudo (less secure):
echo 'ephergent ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ephergent
chmod 440 /etc/sudoers.d/ephergent
```

Troubleshooting tips
--------------------
- If `ephergent-web` fails to start: check `journalctl -u ephergent-web` and `logs/application.log`. Ensure the venv exists and `gunicorn` was installed in it.
- If migrations failed: inspect `migration_result.json` and the application logs. Re-run migrations manually (see below).
- If static files 404: ensure nginx `location /static/` alias path matches your app's static directory.

Re-running migrations manually
----------------------------
```bash
# As root or with sudo:
sudo -u ephergent bash -lc '
cd /opt/ephergent_season_03_generator
source .venv/bin/activate
# Load the same envs the deploy uses
set -a; [ -f /etc/default/ephergent_web ] && source /etc/default/ephergent_web || true
set -a; [ -f .env ] && source .env || true
python scripts/run_migrations.py
'

# Check the result file
cat /opt/ephergent_season_03_generator/migration_result.json | python -m json.tool
```

Maintenance suggestions / next steps
-----------------------------------
- Add logrotate configuration for `/opt/ephergent_season_03_generator/logs/*.log`.
- Consider using a process manager or supervising Gunicorn with systemd (already done), and tuning workers/timeouts via a Gunicorn config file.
- Add a systemd timer or cron to backup Postgres regularly.
- If you want TLS on local LAN, add a self-signed cert and configure nginx to listen on 443.

Contact
-------
If anything here is unclear or you'd like the README expanded with example outputs or screenshots, say which section and I'll update it.

