# Phase 1.3: Database Optimization - Implementation Summary

**Quick Reference Guide**

---

## Overview

Phase 1.3 implements three critical database optimization features:
1. Story Archiving System
2. Media Retention Policies
3. Backup & Recovery

---

## Implementation Checklist

### Week 1: Database Schema
- [ ] Create migration file `migrations/versions/XXXX_phase_1_3_archiving.py`
- [ ] Add `ArchivedStory` model to `models.py`
- [ ] Add `ArchiveOperation` model to `models.py`
- [ ] Add `BackupLog` model to `models.py`
- [ ] Update `Story` model with archive fields
- [ ] Run migration: `flask db upgrade`
- [ ] Initialize configs: `python -m ephergent_generator.scripts.init_phase_1_3_config`

### Week 2: Archive Service
- [ ] Enhance `services/archive_service.py`
- [ ] Implement `archive_story()` with database integration
- [ ] Implement `search_archived_stories()`
- [ ] Implement `restore_story()`
- [ ] Add integrity validation
- [ ] Write unit tests

### Week 3: Media Cleanup Service
- [ ] Create `services/media_cleanup_service.py`
- [ ] Implement `cleanup_expired_media()`
- [ ] Implement storage monitoring
- [ ] Implement preservation flags
- [ ] Write unit tests

### Week 4: Backup Service
- [ ] Create `services/backup_service.py`
- [ ] Implement `create_backup()` with pg_dump
- [ ] Implement `verify_backup()`
- [ ] Implement retention management
- [ ] Write unit tests

### Week 5: Automation Scripts
- [ ] Create `scripts/archive_stories.py`
- [ ] Create `scripts/cleanup_media.py`
- [ ] Create `scripts/backup_database.py`
- [ ] Create cron jobs in `/etc/cron.d/ephergent-archiving`
- [ ] Test automated execution

### Week 6: Admin UI
- [ ] Add Archive Management page (`/admin/archives`)
- [ ] Add Storage Dashboard (`/admin/storage`)
- [ ] Add Backup Management page (`/admin/backups`)
- [ ] Add Configuration editor
- [ ] Integration testing

### Week 7: Monitoring
- [ ] Add Prometheus metrics to `utils/metrics.py`
- [ ] Update Grafana dashboard
- [ ] Configure AlertManager rules
- [ ] Add health check endpoints

### Week 8: Deployment
- [ ] Update README
- [ ] Create operations runbook
- [ ] Deploy to production
- [ ] Monitor for one week

---

## Quick Start Commands

### Run Migration
```bash
cd /Users/jeremy/Documents/ephergent_next/ephergent_season_03_generator
source .venv/bin/activate
flask db upgrade
python -m ephergent_generator.scripts.init_phase_1_3_config
```

### Test Archive Service
```python
from ephergent_generator import create_app
from ephergent_generator.services.archive_service import ArchiveService
from ephergent_generator.models import Story

app = create_app()
with app.app_context():
    service = ArchiveService()

    # Find old completed stories
    from datetime import datetime, timedelta
    threshold = datetime.utcnow() - timedelta(days=60)
    old_stories = Story.query.filter(
        Story.current_step == WorkflowStep.COMPLETED,
        Story.completed_at < threshold,
        Story.is_archived == False
    ).limit(10).all()

    # Archive one story (dry run)
    result = service.archive_story(old_stories[0], reason='test', preserve_media=True)
    print(f"Archived: {result.archive_path}")
```

### Manual Backup
```bash
python -m ephergent_generator.scripts.backup_database --type full
```

### Manual Cleanup
```bash
python -m ephergent_generator.scripts.cleanup_media --dry-run
```

---

## Key Database Schema Changes

### New Tables

1. **archived_stories**
   - Stores complete JSON snapshot of archived stories
   - Searchable by title, narrator, date
   - Tracks media location and size

2. **archive_operations**
   - Audit log for all archive/restore operations
   - Tracks success/failure, timing, bytes processed

3. **backup_logs**
   - Tracks database backup operations
   - Stores verification status and metadata

### Modified Tables

**stories** - Added:
- `is_archived` (bool) - Is story archived?
- `archived_at` (datetime) - When archived
- `archive_id` (FK) - Link to archived_stories
- `preserve_story` (bool) - Prevent auto-archiving
- `preserve_until` (datetime) - Preservation expiration
- `media_deleted_at` (datetime) - When media cleaned up

---

## Configuration Reference

### Archiving Settings

```python
SystemConfig.get_config('archive_enabled')  # True/False
SystemConfig.get_config('archive_age_threshold_days')  # Default: 60
SystemConfig.get_config('archive_batch_size')  # Default: 50
SystemConfig.get_config('archive_preserve_media')  # Default: True
```

### Retention Settings

```python
SystemConfig.get_config('media_cleanup_enabled')  # True/False
SystemConfig.get_config('media_retention_days')  # Default: 90
SystemConfig.get_config('media_cleanup_require_archive')  # Default: True
```

### Backup Settings

```python
SystemConfig.get_config('backup_enabled')  # True/False
SystemConfig.get_config('backup_daily_retention')  # Default: 7 days
SystemConfig.get_config('backup_weekly_retention')  # Default: 30 days
SystemConfig.get_config('backup_monthly_retention')  # Default: 365 days
```

---

## Cron Job Schedule

```bash
# /etc/cron.d/ephergent-archiving

# Archive old stories daily at 2:00 AM
0 2 * * * ephergent cd /path/to/project && source .venv/bin/activate && python -m ephergent_generator.scripts.archive_stories

# Cleanup old media daily at 2:30 AM
30 2 * * * ephergent cd /path/to/project && source .venv/bin/activate && python -m ephergent_generator.scripts.cleanup_media

# Backup database daily at 3:00 AM
0 3 * * * ephergent cd /path/to/project && source .venv/bin/activate && python -m ephergent_generator.scripts.backup_database

# Verify backups weekly on Sundays at 4:00 AM
0 4 * * 0 ephergent cd /path/to/project && source .venv/bin/activate && python -m ephergent_generator.scripts.verify_backups
```

---

## Monitoring Dashboard

### Grafana Panels to Add

1. **Archive Statistics**
   - Total archived stories
   - Archive growth rate
   - Archive size (GB)

2. **Storage Usage**
   - Storage by media type
   - Cleanup rate
   - Space freed by cleanup

3. **Backup Health**
   - Time since last backup
   - Backup success rate
   - Latest backup size

### Alert Thresholds

- Storage Warning: 100GB
- Storage Critical: 150GB
- Backup Stale: 26 hours
- Archive Job Failed: No operations during scheduled time

---

## Common Operations

### Archive a Specific Story

```python
from ephergent_generator.services.archive_service import ArchiveService

service = ArchiveService()
archived = service.archive_story(
    story=story,
    reason='manual',
    user_id=1,
    preserve_media=True
)
```

### Search Archived Stories

```python
results = service.search_archived_stories(
    query='robot',
    narrator='dr_bytes',
    date_from=datetime(2025, 1, 1),
    limit=50
)
```

### Restore an Archived Story

```python
restored_story = service.restore_story(
    archived_story_id=456,
    user_id=1,
    restore_media=True,
    notes='Requested by user for re-publication'
)
```

### Set Preservation Flag

```python
from ephergent_generator.services.media_cleanup_service import MediaCleanupService

cleanup_service = MediaCleanupService()
cleanup_service.set_story_preservation(
    story_id=123,
    preserve=True,
    reason='Featured story for marketing',
    until=datetime(2025, 12, 31),
    user_id=1
)
```

### Check Storage Usage

```python
storage = cleanup_service.calculate_storage_usage()
print(f"Total storage: {storage['total_gb']:.2f} GB")
print(f"Deletable: {storage['deletable_bytes'] / (1024**3):.2f} GB")
```

### Manual Backup

```python
from ephergent_generator.services.backup_service import BackupService

backup_service = BackupService()
backup_log = backup_service.create_backup(
    backup_type='full',
    verify=True
)
print(f"Backup created: {backup_log.backup_path}")
```

---

## Testing Strategy

### Unit Tests

```bash
# Test individual services
pytest tests/test_archive_service.py
pytest tests/test_media_cleanup_service.py
pytest tests/test_backup_service.py
```

### Integration Tests

```bash
# Test complete workflows
pytest tests/integration/test_archiving_workflow.py
```

### Manual Testing Checklist

- [ ] Archive a story and verify ArchivedStory record
- [ ] Verify media files copied to archive directory
- [ ] Restore archived story and verify data matches
- [ ] Cleanup media for old story
- [ ] Create backup and verify file
- [ ] Test restore from backup (to test database)
- [ ] Trigger storage alert by filling disk
- [ ] Test preservation flag prevents archiving

---

## Troubleshooting

### Archive Operation Failed

```bash
# Check logs
tail -f season_03_generator.log | grep -i archive

# Check database
psql -d ephergent_db -c "SELECT * FROM archive_operations WHERE status='failed' ORDER BY started_at DESC LIMIT 10;"

# Check disk space
df -h
```

### Backup Failed

```bash
# Check pg_dump is available
which pg_dump

# Test pg_dump manually
pg_dump ephergent_db > /tmp/test_backup.sql

# Check backup logs
tail -f /var/log/ephergent/backup.log
```

### Storage Full

```bash
# Check usage
du -sh archives/
du -sh ephergent_generator/static/generated_*

# Find large files
find archives/ -type f -size +100M -exec ls -lh {} \;

# Emergency cleanup
python -m ephergent_generator.scripts.cleanup_media --force --retention-days 30
```

---

## Safety Checklist

Before deploying to production:

- [ ] Tested migration on development database
- [ ] Verified rollback procedure works
- [ ] Created manual backup before deployment
- [ ] Tested archive and restore operations
- [ ] Verified cron jobs are scheduled correctly
- [ ] Confirmed Prometheus metrics are collecting
- [ ] Set up AlertManager notifications
- [ ] Documented emergency procedures
- [ ] Trained team on admin UI

---

## Emergency Procedures

### Disable Automated Jobs

```bash
sudo vim /etc/cron.d/ephergent-archiving
# Comment out all lines with #
```

### Rollback Migration

```bash
cd /path/to/project
source .venv/bin/activate
flask db downgrade  # Reverts one migration
```

### Restore Database from Backup

```bash
# Find latest backup
ls -lht backups/daily/

# Restore (DESTRUCTIVE - use test database first)
gunzip -c backup.sql.gz | psql ephergent_db_test
```

---

## File Locations Reference

```
/Users/jeremy/Documents/ephergent_next/ephergent_season_03_generator/
├── ephergent_generator/
│   ├── models.py                     # Add new models here
│   ├── services/
│   │   ├── archive_service.py        # Enhance this
│   │   ├── media_cleanup_service.py  # Create new
│   │   └── backup_service.py         # Create new
│   ├── scripts/
│   │   ├── archive_stories.py        # Create new
│   │   ├── cleanup_media.py          # Create new
│   │   └── backup_database.py        # Create new
│   └── utils/
│       └── metrics.py                # Add new metrics
├── migrations/versions/
│   └── XXXX_phase_1_3_archiving.py   # Create new
├── archives/                         # Create directory
│   └── stories/
├── backups/                          # Create directory
│   ├── daily/
│   ├── weekly/
│   └── monthly/
└── PHASE_1_3_ARCHITECTURE.md         # Full architecture doc
```

---

## Success Metrics

After deployment, monitor these for one week:

- Archive operations complete successfully daily
- No backup failures
- Storage usage stays below warning threshold
- Restore operations work correctly
- No data loss incidents
- System performance unchanged
- All alerts functioning

---

## Next Steps After Phase 1.3

**Phase 2.0 Enhancements:**
- S3/Glacier integration for cold storage
- Backup encryption with GPG
- Cross-region backup replication
- Archive compression optimization
- Full-text search for archived stories
- Automated restore testing
- Archive analytics dashboard

---

For detailed technical specifications, see: **PHASE_1_3_ARCHITECTURE.md**
