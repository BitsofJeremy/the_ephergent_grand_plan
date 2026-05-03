#!/usr/bin/env bash
# reload_grafana_dashboards.sh
# Reload Grafana dashboards after deployment
# Run this on the server if dashboards don't appear after deployment

set -euo pipefail

echo "Reloading Grafana dashboards..."

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo"
   exit 1
fi

# Verify files exist
DASHBOARD_JSON="/var/lib/grafana/dashboards/ephergent-story-generator.json"
PROV_CONFIG="/etc/grafana/provisioning/dashboards/ephergent.yml"

if [[ ! -f "$DASHBOARD_JSON" ]]; then
    echo "Error: Dashboard JSON not found at $DASHBOARD_JSON"
    exit 1
fi

if [[ ! -f "$PROV_CONFIG" ]]; then
    echo "Error: Provisioning config not found at $PROV_CONFIG"
    exit 1
fi

echo "✓ Dashboard files exist"

# Check ownership
echo "Checking file ownership..."
chown -R grafana:grafana /var/lib/grafana/dashboards
chown -R grafana:grafana /etc/grafana/provisioning
echo "✓ Ownership corrected"

# Restart Grafana to force provisioning reload
echo "Restarting Grafana server..."
systemctl restart grafana-server

# Wait for Grafana to be ready
echo "Waiting for Grafana to be ready..."
for i in {1..30}; do
    if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
        echo "✓ Grafana is ready"
        break
    fi
    sleep 1
done

# Test if dashboard was loaded
echo "Testing dashboard provisioning..."
sleep 3  # Give Grafana a moment to scan provisioning directory

DASHBOARD_CHECK=$(curl -sf -u admin:admin "http://localhost:3000/api/dashboards/uid/ephergent-story-gen" || echo "not found")

if echo "$DASHBOARD_CHECK" | grep -q '"dashboard"'; then
    echo "✓ Dashboard successfully provisioned!"
    echo ""
    echo "Dashboard available at:"
    echo "  http://your-server:3000/d/ephergent-story-gen/"
    echo "  Or via admin portal: http://your-server/admin/monitoring/grafana"
    exit 0
else
    echo "⚠ Dashboard not found after restart"
    echo "Checking Grafana logs for errors..."
    journalctl -u grafana-server -n 50 | grep -i "dashboard\|provisioning\|error" || true
    echo ""
    echo "You may need to:"
    echo "  1. Check Grafana logs: journalctl -u grafana-server -f"
    echo "  2. Verify admin password hasn't changed from default"
    echo "  3. Check file permissions on $DASHBOARD_JSON"
    exit 1
fi
