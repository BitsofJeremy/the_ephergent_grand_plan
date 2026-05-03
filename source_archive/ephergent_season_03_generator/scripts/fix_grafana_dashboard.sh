#!/usr/bin/env bash
# fix_grafana_dashboard.sh
# Fix the Grafana dashboard JSON format and reload

set -euo pipefail

echo "Fixing Grafana dashboard JSON format..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo"
   exit 1
fi

DASHBOARD_FILE="/var/lib/grafana/dashboards/ephergent-story-generator.json"
TEMP_FILE="/tmp/grafana-dashboard-fixed.json"

if [[ -f "$TEMP_FILE" ]]; then
    echo "Installing fixed dashboard from $TEMP_FILE..."
    cp "$TEMP_FILE" "$DASHBOARD_FILE"
    chown grafana:grafana "$DASHBOARD_FILE"
    chmod 644 "$DASHBOARD_FILE"
    echo "✓ Dashboard file updated"
else
    echo "Error: Fixed dashboard file not found at $TEMP_FILE"
    echo "Please copy the fixed dashboard file to $TEMP_FILE first"
    exit 1
fi

# Restart Grafana
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
sleep 3

DASHBOARD_CHECK=$(curl -sf -u admin:admin "http://localhost:3000/api/dashboards/uid/ephergent-story-gen" 2>&1 || echo "not found")

if echo "$DASHBOARD_CHECK" | grep -q '"dashboard"'; then
    echo "✓ Dashboard successfully provisioned!"
    echo ""
    echo "Dashboard available at:"
    echo "  http://$(hostname -I | awk '{print $1}'):3000/d/ephergent-story-gen/"
    echo "  Or via admin portal: http://$(hostname -I | awk '{print $1}')/admin/monitoring/grafana"
    exit 0
else
    echo "⚠ Dashboard not found after restart"
    echo "Checking Grafana logs for errors..."
    journalctl -u grafana-server --since '1 minute ago' | grep -i "dashboard\|provisioning\|error" | tail -20
    exit 1
fi
