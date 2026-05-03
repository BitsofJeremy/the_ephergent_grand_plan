# Grafana Setup Guide for Ephergent Admin Portal

This guide helps you configure Grafana to work with the Ephergent admin portal's iframe embedding.

## Problem Summary

When accessing the Grafana dashboard through the admin portal (`/admin/monitoring/grafana`), you may encounter one or both of these issues:

1. **Dashboard UID Mismatch**: The admin portal cannot find the dashboard
2. **X-Frame-Options Blocking**: Firefox/Chrome blocks the iframe with "To protect your security..."

## Quick Fix (For Existing Deployments)

If you've already deployed and are experiencing these issues, follow these steps:

### Step 1: Enable Iframe Embedding in Grafana

```bash
# SSH into your server
ssh user@your-server-ip

# Backup the original Grafana configuration
sudo cp /etc/grafana/grafana.ini /etc/grafana/grafana.ini.backup

# Add security settings to allow iframe embedding
sudo tee -a /etc/grafana/grafana.ini > /dev/null <<'EOF'

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
EOF

# Set correct ownership and permissions
sudo chown grafana:grafana /etc/grafana/grafana.ini
sudo chmod 640 /etc/grafana/grafana.ini

# Restart Grafana to apply changes
sudo systemctl restart grafana-server
```

### Step 2: Verify Configuration

```bash
# Check that Grafana restarted successfully
sudo systemctl status grafana-server

# Check for any errors in logs
sudo journalctl -u grafana-server -n 50
```

### Step 3: Test the Admin Portal

1. Navigate to `http://your-server-ip/admin/monitoring/grafana`
2. The Grafana dashboard should now load in the iframe without errors
3. If you still see X-Frame-Options errors, clear your browser cache and try again

## Dashboard Import Issues

If the dashboard isn't showing up in Grafana at all:

### Check Dashboard Files

```bash
# Verify dashboard JSON exists in the correct location
ls -la /var/lib/grafana/dashboards/

# You should see: ephergent-story-generator.json
# If not, copy it manually:
sudo cp /opt/ephergent_season_03_generator/monitoring/grafana-dashboard.json \
  /var/lib/grafana/dashboards/ephergent-story-generator.json

# Set correct ownership
sudo chown grafana:grafana /var/lib/grafana/dashboards/ephergent-story-generator.json
sudo chmod 644 /var/lib/grafana/dashboards/ephergent-story-generator.json

# Restart Grafana
sudo systemctl restart grafana-server
```

### Verify Provisioning Configuration

```bash
# Check provisioning config exists
cat /etc/grafana/provisioning/dashboards/ephergent.yml

# Should contain:
# apiVersion: 1
# providers:
#   - name: 'Ephergent Dashboards'
#     orgId: 1
#     folder: ''
#     type: file
#     ...
```

### Check Dashboard in Grafana UI

1. Log in to Grafana directly: `http://your-server-ip:3000`
2. Default credentials: `admin` / `admin` (change on first login)
3. Navigate to **Dashboards** → **Browse**
4. Look for "Ephergent Story Generator - Production Monitoring"
5. Note the dashboard UID in the URL: `/d/{uid}/...`
6. The UID should be: `ephergent-story-gen`

## Troubleshooting

### Issue: "Dashboard not found" in Admin Portal

**Symptoms**: Admin portal shows 404 or blank page

**Solution**:
1. Check the dashboard UID matches in routes.py (already fixed in latest code)
2. Verify dashboard exists in Grafana: `http://your-server-ip:3000/d/ephergent-story-gen/`
3. Check Grafana logs: `sudo journalctl -u grafana-server -f`

### Issue: X-Frame-Options Still Blocking

**Symptoms**: Firefox/Chrome error about embedding

**Solutions**:

1. **Verify Grafana config was updated**:
   ```bash
   sudo grep "allow_embedding" /etc/grafana/grafana.ini
   # Should output: allow_embedding = true
   ```

2. **Clear browser cache** completely and restart browser

3. **Check if using HTTPS**: If your site uses HTTPS, update:
   ```bash
   sudo nano /etc/grafana/grafana.ini
   # Change: cookie_secure = true
   sudo systemctl restart grafana-server
   ```

4. **Verify Grafana is listening**:
   ```bash
   sudo netstat -tlnp | grep 3000
   # Should show Grafana listening on port 3000
   ```

### Issue: Grafana Shows Login Page in Iframe

**Symptoms**: Iframe shows Grafana login instead of dashboard

**Solutions**:

1. **Option A: Enable Anonymous Access (Read-Only)**:
   ```bash
   sudo tee -a /etc/grafana/grafana.ini > /dev/null <<'EOF'

   [auth.anonymous]
   enabled = true
   org_name = Main Org.
   org_role = Viewer
   EOF

   sudo systemctl restart grafana-server
   ```

2. **Option B: Use Logged-In Session**:
   - Log in to Grafana at `http://your-server-ip:3000`
   - Then navigate to admin portal
   - Session cookie will allow iframe access

### Issue: Dashboard Shows "No Data"

**Symptoms**: Dashboard loads but panels show "No data"

**Solution**:
1. Check Prometheus is running: `sudo systemctl status prometheus`
2. Verify metrics endpoint: `curl http://localhost:5000/metrics`
3. Check Prometheus is scraping: `http://your-server-ip:9090/targets`
4. Verify datasource in Grafana: **Configuration** → **Data Sources** → **Prometheus**

## Manual Configuration for Different Setups

### For Docker Deployments

Add environment variables to your Grafana container:

```yaml
environment:
  - GF_SECURITY_ALLOW_EMBEDDING=true
  - GF_SECURITY_COOKIE_SAMESITE=lax
  - GF_SECURITY_COOKIE_SECURE=false
```

### For Kubernetes Deployments

Update your Grafana ConfigMap or values.yaml:

```yaml
grafana.ini:
  security:
    allow_embedding: true
    cookie_samesite: lax
    cookie_secure: false
```

### For Nginx Reverse Proxy

If Grafana is behind nginx, ensure these headers are NOT being set:

```nginx
# DO NOT include these in your nginx config for Grafana:
# add_header X-Frame-Options "DENY";
# add_header X-Frame-Options "SAMEORIGIN";
```

## Security Considerations

### allow_embedding = true

**What it does**: Allows Grafana to be embedded in iframes from any domain

**Security implications**:
- Moderate risk: Allows potential clickjacking if dashboard contains sensitive controls
- Mitigation: The admin portal requires authentication
- Alternative: Use `[auth.anonymous]` with `org_role = Viewer` for read-only access

### cookie_samesite = lax

**What it does**: Allows cookies to be sent in cross-origin requests from same-site contexts

**Security implications**:
- Low risk: More permissive than `strict` but stricter than `none`
- Suitable for HTTP deployments

### Production Recommendations

For HTTPS production deployments:

```ini
[security]
allow_embedding = true
cookie_samesite = none
cookie_secure = true

[server]
root_url = https://your-domain.com/grafana/
serve_from_sub_path = true
```

## Verification Checklist

Use this checklist to verify your Grafana configuration:

- [ ] Grafana is running: `sudo systemctl status grafana-server`
- [ ] Configuration file updated: `sudo grep allow_embedding /etc/grafana/grafana.ini`
- [ ] Dashboard file exists: `ls /var/lib/grafana/dashboards/ephergent-story-generator.json`
- [ ] Provisioning configured: `cat /etc/grafana/provisioning/dashboards/ephergent.yml`
- [ ] Grafana accessible directly: `http://your-server-ip:3000`
- [ ] Dashboard visible in Grafana UI
- [ ] Prometheus datasource configured and working
- [ ] Admin portal shows dashboard: `http://your-server-ip/admin/monitoring/grafana`
- [ ] No X-Frame-Options errors in browser console
- [ ] Metrics panels showing data (not "No data")

## Getting Help

If you're still experiencing issues after following this guide:

1. Check Grafana logs:
   ```bash
   sudo journalctl -u grafana-server -n 100
   ```

2. Check Flask application logs:
   ```bash
   sudo journalctl -u ephergent-web -n 100
   ```

3. Test direct dashboard URL:
   ```bash
   curl -I http://localhost:3000/d/ephergent-story-gen/
   ```

4. Verify iframe embedding works with a simple test:
   ```html
   <!-- test.html -->
   <iframe src="http://your-server-ip:3000/d/ephergent-story-gen/"
           width="100%" height="600px"></iframe>
   ```

## References

- [Grafana Security Configuration](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/)
- [Grafana Dashboard Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [iframe X-Frame-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options)
