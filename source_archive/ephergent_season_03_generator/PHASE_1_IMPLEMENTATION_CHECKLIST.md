# Phase 1 Implementation Checklist

**Quick Reference:** Task-by-task checklist for implementing Phase 1 Production Readiness & Stability

**Status Legend:**
- [ ] Not Started
- [~] In Progress
- [x] Completed
- [!] Blocked

---

## Sprint 1: Core Observability (Weeks 1-2)

### Week 1: Structured Logging

#### Day 1-2: Setup Logging Infrastructure

- [ ] Install `python-json-logger` package
  ```bash
  cd /Users/jeremy/Documents/ephergent_next/ephergent_season_03_generator
  source .venv/bin/activate
  pip install python-json-logger
  # Update pyproject.toml to include it
  ```

- [ ] Create `ephergent_generator/utils/` directory
  ```bash
  mkdir -p ephergent_generator/utils
  touch ephergent_generator/utils/__init__.py
  ```

- [ ] Create `ephergent_generator/utils/logging_config.py`
  - Copy implementation from PHASE_1_ARCHITECTURE.md
  - Test JSON logging locally
  - Verify request context inclusion

- [ ] Update `ephergent_generator/__init__.py` to use new logging
  ```python
  from ephergent_generator.utils.logging_config import setup_logging
  app = setup_logging(app)
  ```

#### Day 3: Update Service Logging

- [ ] Update `workflow_service.py` to use structured logging
  - Replace print statements
  - Add contextual fields (story_id, workflow_step, duration_ms)
  - Test log output

- [ ] Update `gemini_service.py` to use structured logging
  - Add API call duration tracking
  - Add error context

- [ ] Update `image_service.py` to use structured logging

- [ ] Update `audio_service.py` to use structured logging

- [ ] Update `video_service.py` to use structured logging

#### Day 4: Configure Log Rotation

- [ ] Create logrotate configuration
  ```bash
  # On Debian VM
  sudo vim /etc/logrotate.d/ephergent
  # Add config from PHASE_1_ARCHITECTURE.md
  ```

- [ ] Test log rotation
  ```bash
  sudo logrotate -f /etc/logrotate.d/ephergent
  ```

- [ ] Verify logs are created in `/var/log/ephergent/`

- [ ] Update deployment script to create log directory

---

### Week 2: Prometheus Metrics & Health Checks

#### Day 1-2: Prometheus Metrics

- [ ] Install `prometheus-client` package
  ```bash
  pip install prometheus-client
  ```

- [ ] Create `ephergent_generator/utils/metrics.py`
  - Copy implementation from PHASE_1_ARCHITECTURE.md
  - Define all metrics (counters, histograms, gauges)
  - Test metric registration

- [ ] Create `/api/metrics.py` blueprint
  - Implement `/metrics` endpoint
  - Test Prometheus format output
  ```bash
  curl http://localhost:5000/metrics
  ```

- [ ] Register metrics blueprint in app factory

- [ ] Add metrics to `workflow_service.py`
  - Track story creation
  - Track workflow step duration
  - Track failures

#### Day 3: Health Checks

- [ ] Create `ephergent_generator/utils/health_checks.py`
  - Copy implementation from PHASE_1_ARCHITECTURE.md
  - Implement HealthChecker class
  - Test each health check method

- [ ] Update existing `api/health.py`
  - Add `/health/liveness` endpoint
  - Add `/health/readiness` endpoint
  - Update `/health` for full health check
  - Test all endpoints

- [ ] Test health checks with database down
  - Verify readiness returns 503
  - Verify liveness still returns 200

#### Day 4: Prometheus Installation

- [ ] Install Prometheus on Debian VM
  ```bash
  ssh debian-vm
  sudo apt-get install -y prometheus prometheus-node-exporter
  ```

- [ ] Configure Prometheus scraping
  - Edit `/etc/prometheus/prometheus.yml`
  - Add ephergent-web scrape config
  - Restart Prometheus
  ```bash
  sudo systemctl restart prometheus
  sudo systemctl enable prometheus
  ```

- [ ] Verify Prometheus is scraping metrics
  - Open http://10.0.0.99:9090
  - Check targets page
  - Query `ephergent_stories_created_total`

- [ ] Install Grafana
  ```bash
  # Add Grafana repository
  wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
  sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
  sudo apt-get update
  sudo apt-get install -y grafana

  # Start Grafana
  sudo systemctl start grafana-server
  sudo systemctl enable grafana-server
  ```

- [ ] Configure Grafana
  - Open http://10.0.0.99:3000
  - Login with admin/admin
  - Add Prometheus data source
  - Create test dashboard

#### Day 5: Documentation & Testing

- [ ] Write unit tests for logging
  - Test JSON format
  - Test request context
  ```bash
  pytest tests/test_logging.py -v
  ```

- [ ] Write unit tests for metrics
  - Test counter increments
  - Test histogram observations
  ```bash
  pytest tests/test_metrics.py -v
  ```

- [ ] Write unit tests for health checks
  - Test liveness
  - Test readiness with DB failure
  ```bash
  pytest tests/test_health_checks.py -v
  ```

- [ ] Update CLAUDE.md with new logging/metrics guidelines

- [ ] Document Prometheus queries for common scenarios

---

## Sprint 2: Error Handling & Retry Logic (Weeks 3-4)

### Week 3: Retry Service Implementation

#### Day 1: Database Schema

- [ ] Create `StoryRetry` model in `models.py`
  - Copy implementation from PHASE_1_ARCHITECTURE.md
  - Add all required fields
  - Add helper methods

- [ ] Create database migration
  ```bash
  flask db migrate -m "Add story retry tracking"
  flask db upgrade
  ```

- [ ] Verify migration applied successfully
  ```bash
  flask db current
  psql -U ephergent -d ephergent_production -c "\d story_retries"
  ```

#### Day 2-3: Retry Service

- [ ] Create `ephergent_generator/services/retry_service.py`
  - Copy implementation from PHASE_1_ARCHITECTURE.md
  - Implement ErrorType enum
  - Implement RetryService class

- [ ] Test error classification
  - Test timeout errors
  - Test rate limit errors
  - Test validation errors
  ```python
  # In Python shell
  from ephergent_generator.services.retry_service import RetryService
  RetryService.classify_error(TimeoutError())
  ```

- [ ] Test retry logic
  - Test should_retry() method
  - Test calculate_backoff_seconds()
  - Test mark_dead_letter()

#### Day 4-5: Workflow Integration

- [ ] Update `workflow_service.py` to use RetryService
  - Import RetryService
  - Wrap each workflow step in try/except
  - Call `record_failure()` on exception
  - Call `record_success()` on success

- [ ] Test retry behavior
  - Mock Gemini API to fail 2 times, then succeed
  - Verify story eventually completes
  - Verify retry record shows 2 retries

- [ ] Add retry metrics
  - Track retry attempts
  - Track DLQ size
  - Update `/metrics` endpoint

---

### Week 4: Dead Letter Queue & Admin Tools

#### Day 1-2: DLQ API

- [ ] Create `api/admin/dlq.py` blueprint
  - GET `/api/admin/dlq` - List DLQ stories
  - GET `/api/admin/dlq/<story_id>` - Get DLQ story details
  - POST `/api/admin/dlq/<story_id>/requeue` - Re-queue story
  - DELETE `/api/admin/dlq/<story_id>` - Remove from DLQ

- [ ] Test DLQ endpoints
  ```bash
  curl http://localhost:5000/api/admin/dlq
  ```

- [ ] Add authentication to DLQ endpoints (require admin user)

#### Day 3: DLQ Monitoring

- [ ] Create Grafana dashboard for DLQ
  - Panel: DLQ size over time
  - Panel: DLQ stories by error type
  - Panel: Recent DLQ entries (table)

- [ ] Create Prometheus alert for DLQ growth
  - Alert when DLQ size > 25
  - Send notification to Slack/email

- [ ] Test alert
  - Manually add stories to DLQ
  - Verify alert fires

#### Day 4-5: Testing & Documentation

- [ ] Write integration tests for retry logic
  - Test full retry workflow
  - Test DLQ workflow
  ```bash
  pytest tests/integration/test_retry_workflow.py -v
  ```

- [ ] Create operations runbook
  - How to investigate DLQ stories
  - How to manually re-queue
  - How to fix common issues

- [ ] Update CLAUDE.md with retry behavior

---

## Sprint 3: Database Optimization & Alerting (Weeks 5-6)

### Week 5: Database Optimization

#### Day 1: Connection Pooling

- [ ] Update `config.py` with pooling settings
  - Set `DB_POOL_SIZE=10`
  - Set `DB_MAX_OVERFLOW=20`
  - Add environment variable support

- [ ] Test connection pooling
  - Monitor active connections
  ```sql
  SELECT count(*) FROM pg_stat_activity WHERE datname = 'ephergent_production';
  ```

- [ ] Add database connection metrics
  - Track active connections
  - Track pool exhaustion events

#### Day 2-3: Story Archiving

- [ ] Create `ArchivedStory` model
  - Copy implementation from PHASE_1_ARCHITECTURE.md
  - Add migration

- [ ] Update `archive_service.py`
  - Implement `archive_old_stories()`
  - Implement `restore_archived_story()`

- [ ] Create scheduled archiving task
  - Use systemd timer or cron
  - Archive stories >90 days old
  ```bash
  # Create systemd timer
  sudo vim /etc/systemd/system/ephergent-archive.timer
  ```

- [ ] Test archiving workflow
  - Manually archive a story
  - Verify archived data is complete
  - Test restore

#### Day 4-5: Query Optimization

- [ ] Analyze slow query log
  ```bash
  # Enable slow query log in PostgreSQL
  sudo vim /etc/postgresql/15/main/postgresql.conf
  # Add: log_min_duration_statement = 1000
  sudo systemctl restart postgresql
  ```

- [ ] Add database indexes
  - Run migration from PHASE_1_ARCHITECTURE.md
  - Verify indexes created
  ```sql
  SELECT * FROM pg_indexes WHERE tablename = 'stories';
  ```

- [ ] Test query performance improvement
  - Benchmark before/after indexes
  - Document improvements

---

### Week 6: Grafana Dashboards & Alerting

#### Day 1-2: Grafana Dashboards

- [ ] Create "System Overview" dashboard
  - Import dashboard JSON
  - Configure panels
  - Test queries

- [ ] Create "Workflow Performance" dashboard
  - Track P95 latency by step
  - Track success rate by step

- [ ] Create "Error Tracking" dashboard
  - Track error rate
  - Track error breakdown
  - Track DLQ size

#### Day 3-4: Prometheus Alerting

- [ ] Install AlertManager
  ```bash
  sudo apt-get install prometheus-alertmanager
  ```

- [ ] Configure AlertManager
  - Add email/Slack notification channel
  - Test notification delivery

- [ ] Create alert rules
  - Copy from PHASE_1_ARCHITECTURE.md
  - Save to `/etc/prometheus/rules/ephergent_alerts.yml`
  - Reload Prometheus
  ```bash
  sudo systemctl reload prometheus
  ```

- [ ] Test alerts
  - Trigger test alert
  - Verify notification received

#### Day 5: Documentation & Handoff

- [ ] Create monitoring runbook
  - How to investigate alerts
  - How to read Grafana dashboards
  - Common troubleshooting steps

- [ ] Update CLAUDE.md with monitoring guidelines

- [ ] Create Phase 1 completion report
  - Document all changes
  - List success metrics achieved
  - Identify any outstanding issues

---

## Deployment Checklist

### Pre-Deployment

- [ ] Run all tests locally
  ```bash
  pytest tests/ -v
  ```

- [ ] Review code changes
  ```bash
  git diff main
  ```

- [ ] Update version number
  - Edit `pyproject.toml`
  - Update version to 0.2.0

- [ ] Create deployment branch
  ```bash
  git checkout -b deploy/phase-1
  git commit -am "Phase 1: Production Readiness"
  git push origin deploy/phase-1
  ```

### Deployment to Production

- [ ] Backup production database
  ```bash
  ssh debian-vm
  pg_dump ephergent_production > /backups/ephergent_$(date +%Y%m%d).sql
  ```

- [ ] Stop background worker
  ```bash
  sudo systemctl stop ephergent-worker
  ```

- [ ] Deploy code changes
  ```bash
  cd /opt/ephergent
  git pull origin main
  source .venv/bin/activate
  pip install -e .
  ```

- [ ] Run database migrations
  ```bash
  flask db upgrade
  ```

- [ ] Restart web service (rolling restart)
  ```bash
  sudo systemctl reload ephergent-web
  ```

- [ ] Verify health checks pass
  ```bash
  curl http://localhost:5000/health/readiness
  ```

- [ ] Start background worker
  ```bash
  sudo systemctl start ephergent-worker
  ```

### Post-Deployment Validation

- [ ] Check logs for errors
  ```bash
  sudo journalctl -u ephergent-web -n 100 --no-pager
  sudo journalctl -u ephergent-worker -n 100 --no-pager
  ```

- [ ] Verify metrics endpoint
  ```bash
  curl http://localhost:5000/metrics | grep ephergent_
  ```

- [ ] Check Prometheus targets
  - Open http://10.0.0.99:9090/targets
  - Verify all targets are UP

- [ ] Check Grafana dashboards
  - Open http://10.0.0.99:3000
  - Verify data is flowing

- [ ] Submit test story
  ```bash
  curl -X POST http://localhost:5000/api/stories \
    -H "Content-Type: application/json" \
    -d '{"topic": "Phase 1 validation test story"}'
  ```

- [ ] Monitor test story progression
  ```bash
  # Check queue status
  curl http://localhost:5000/api/queue/status

  # Watch logs
  sudo journalctl -u ephergent-worker -f
  ```

---

## Rollback Plan

### If Deployment Fails

- [ ] Rollback database migration
  ```bash
  flask db downgrade
  ```

- [ ] Restore previous code version
  ```bash
  git checkout <previous-commit>
  pip install -e .
  ```

- [ ] Restart services
  ```bash
  sudo systemctl restart ephergent-web ephergent-worker
  ```

- [ ] Verify rollback successful
  ```bash
  curl http://localhost:5000/health/readiness
  ```

- [ ] Document rollback reason
  - Create incident report
  - Identify root cause
  - Plan fix

---

## Success Criteria

### Phase 1 is Complete When:

- [x] Structured JSON logging operational
- [x] Prometheus metrics exposed on `/metrics`
- [x] Grafana dashboards created and functional
- [x] Health check endpoints operational
- [x] Retry logic implemented and tested
- [x] Dead letter queue operational
- [x] Database connection pooling optimized
- [x] Story archiving automated
- [x] Alerting rules configured
- [x] All tests passing
- [x] Documentation complete

### Key Metrics Achieved:

- [ ] Story success rate >95%
- [ ] P95 workflow step latency <5 minutes
- [ ] DLQ size <10 stories
- [ ] System uptime >99%
- [ ] Database query P95 latency <100ms

---

## Notes & Issues

### Blockers

- List any blockers here

### Decisions Made

- List key technical decisions here

### Lessons Learned

- Document lessons learned during implementation
