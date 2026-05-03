# Phase 1.3: Database Optimization - Quick Reference Card

---

## Architecture Decision: Dual-Table Approach

**Why separate `archived_stories` table instead of soft delete?**

✓ **Query Performance** - Active stories table stays small and fast
✓ **Index Efficiency** - Better index performance with fewer rows
✓ **Storage Tiering** - Can move archived table to slower/cheaper storage
✓ **Backup Strategy** - Archive table can be backed up separately
✓ **Migration Path** - Easy to move archives to S3/Glacier later

---

## Data Flow Overview

```
┌─────────────────────────────────────────────────────┐
│                   Story Lifecycle                   │
└─────────────────────────────────────────────────────┘

Day 0:    Story Created → Workflow → Completed
          (stories table, current_step=COMPLETED)
          ↓
          Media files: static/generated_*/
          Database: stories.id = 123

Day 60:   Archive Threshold Reached
          ↓
          [ARCHIVE PROCESS]
          1. Create archived_stories record (JSON snapshot)
          2. Copy media to archives/stories/YYYY-MM-DD_story-123/
          3. Update stories: is_archived=true, archive_id=456
          4. Create archive_operations audit log
          ↓
          Status:
          - stories.id=123 (is_archived=true)
          - archived_stories.id=456 (story_data JSON)
          - Media in BOTH locations

Day 90:   Media Retention Threshold Reached
          ↓
          [CLEANUP PROCESS]
          1. Delete files from static/generated_*/
          2. Update stories: media_deleted_at=now()
          3. Create archive_operations audit log
          ↓
          Status:
          - stories.id=123 (is_archived=true, media_deleted_at set)
          - archived_stories.id=456 (story_data JSON)
          - Media ONLY in archives/

Day ∞:    Indefinite Archive Storage
          - Can search/restore anytime
          - Can move to S3/Glacier (future)
```

---

## Database Schema Quick View

### New Tables

```sql
-- Complete story snapshots
archived_stories (
    id                    INTEGER PRIMARY KEY,
    original_story_id     INTEGER NOT NULL,
    story_data            TEXT (JSON),  -- Full Story snapshot
    -- Searchable fields
    title                 VARCHAR(200),
    narrator_character_id VARCHAR(100),
    completed_at          TIMESTAMP,
    -- Archive metadata
    archived_at           TIMESTAMP,
    archive_path          VARCHAR(500),
    archive_size_bytes    BIGINT,
    -- Restoration tracking
    restored_at           TIMESTAMP,
    restored_by           INTEGER → users.id
)

-- Audit log
archive_operations (
    id               INTEGER PRIMARY KEY,
    operation_type   VARCHAR(20),  -- 'archive', 'restore', 'delete_media'
    story_id         INTEGER,
    status           VARCHAR(20),  -- 'success', 'failed'
    started_at       TIMESTAMP,
    files_processed  INTEGER,
    bytes_processed  BIGINT
)

-- Backup tracking
backup_logs (
    id                       INTEGER PRIMARY KEY,
    backup_type              VARCHAR(20),  -- 'full', 'incremental'
    backup_path              VARCHAR(500),
    backup_size_bytes        BIGINT,
    started_at               TIMESTAMP,
    status                   VARCHAR(20),
    verification_status      VARCHAR(20),
    retention_expires_at     TIMESTAMP
)
```

### Story Table Additions

```sql
ALTER TABLE stories ADD COLUMN:
    is_archived          BOOLEAN DEFAULT false,
    archived_at          TIMESTAMP,
    archive_id           INTEGER → archived_stories.id,
    preserve_story       BOOLEAN DEFAULT false,
    preserve_until       TIMESTAMP,
    media_deleted_at     TIMESTAMP
```

---

## Service Architecture

### ArchiveService (Enhanced)

```python
# Key Methods
archive_story(story, reason, user_id, preserve_media)
  → Creates ArchivedStory + copies media

archive_stories_by_age(age_days, dry_run, limit)
  → Bulk archive old stories (automated job)

search_archived_stories(query, narrator, genre, date_range)
  → Full-text search across archives

restore_story(archived_story_id, user_id, restore_media)
  → Restores to active stories table

validate_archive_integrity(archived_story_id)
  → Checks JSON + media files
```

### MediaCleanupService (New)

```python
# Key Methods
cleanup_expired_media(retention_days, dry_run, limit)
  → Deletes media files for old stories

calculate_storage_usage()
  → Returns storage by type (images/audio/video)

set_story_preservation(story_id, preserve, reason, until)
  → Prevents auto-archiving/cleanup

get_cleanup_candidates(retention_days)
  → Lists stories eligible for cleanup
```

### BackupService (New)

```python
# Key Methods
create_backup(backup_type, verify)
  → Executes pg_dump + compression

verify_backup(backup_log_id)
  → Checks file integrity + restore-ability

test_restore(backup_log_id)
  → Tests restore to temporary database

cleanup_old_backups(retention_days)
  → Implements retention policy (7/30/365 days)
```

---

## Configuration Quick Reference

```python
# ARCHIVING
'archive_enabled'                 = True
'archive_age_threshold_days'      = 60    # Archive after 60 days
'archive_batch_size'              = 50    # Max per run
'archive_preserve_media'          = True  # Copy media to archive

# RETENTION
'media_cleanup_enabled'           = True
'media_retention_days'            = 90    # Delete media after 90 days
'media_cleanup_require_archive'   = True  # Only cleanup archived stories

# STORAGE
'storage_warning_threshold_gb'    = 100   # Warning at 100GB
'storage_critical_threshold_gb'   = 150   # Critical at 150GB

# BACKUP
'backup_enabled'                  = True
'backup_daily_retention'          = 7     # Keep 7 days
'backup_weekly_retention'         = 30    # Keep 30 days
'backup_monthly_retention'        = 365   # Keep 365 days
'backup_verify_enabled'           = True
```

---

## Automation Schedule

```
┌─────────────┬────────────────────────────────────┐
│    Time     │              Operation             │
├─────────────┼────────────────────────────────────┤
│ 02:00 daily │ Archive old stories                │
│ 02:30 daily │ Cleanup expired media              │
│ 03:00 daily │ Backup database                    │
│ 04:00 Sun   │ Verify backups (weekly)            │
└─────────────┴────────────────────────────────────┘
```

---

## Storage Layout

```
/ephergent_season_03_generator/
│
├── ephergent_generator/static/
│   ├── generated_images/    ← Active story images
│   ├── generated_audio/     ← Active story audio
│   └── generated_videos/    ← Active story videos
│
├── archives/stories/        ← Archived story media
│   ├── 2025-10-01_story-123_robot_learns_love/
│   │   ├── metadata.json
│   │   ├── story.md
│   │   ├── images/
│   │   ├── audio/
│   │   └── video/
│   └── 2025-10-02_story-124_*/
│
└── backups/                 ← Database backups
    ├── daily/
    │   └── ephergent_db_20251010_020000_full.sql.gz
    ├── weekly/
    └── monthly/
```

---

## Prometheus Metrics

```promql
# ARCHIVING
ephergent_stories_archived_total{reason}
ephergent_archive_operation_duration_seconds
ephergent_archive_size_bytes
ephergent_archive_count

# STORAGE
ephergent_storage_usage_bytes{media_type}
ephergent_media_cleanup_files_deleted_total{media_type}
ephergent_media_cleanup_bytes_freed_total{media_type}

# BACKUP
ephergent_backup_operations_total{type,status}
ephergent_backup_duration_seconds{type}
ephergent_last_successful_backup_timestamp
ephergent_backup_verification_failures_total
```

---

## Alert Thresholds

```yaml
StorageWarning:       > 100 GB
StorageCritical:      > 150 GB
BackupStale:          > 26 hours since last backup
BackupFailed:         Any failure in 24h
ArchivingFailed:      No operations during scheduled time
```

---

## Common CLI Operations

```bash
# Manual archive
python -m ephergent_generator.scripts.archive_stories --dry-run

# Manual cleanup
python -m ephergent_generator.scripts.cleanup_media --retention-days 60

# Manual backup
python -m ephergent_generator.scripts.backup_database --type full

# Check storage
python -c "
from ephergent_generator import create_app
from ephergent_generator.services.media_cleanup_service import MediaCleanupService
app = create_app()
with app.app_context():
    service = MediaCleanupService()
    storage = service.calculate_storage_usage()
    print(f'Total: {storage[\"total_gb\"]:.2f} GB')
"
```

---

## Safety Features

```
┌───────────────────────────────────────────────────┐
│          Multi-Layer Safety Mechanisms            │
├───────────────────────────────────────────────────┤
│ 1. Transaction Wrapping                           │
│    All database operations in transactions        │
│                                                    │
│ 2. Dry Run Mode                                   │
│    Test operations without executing              │
│                                                    │
│ 3. Batch Limits                                   │
│    Process max 50-100 items per run               │
│                                                    │
│ 4. Preserve Flag                                  │
│    Stories can be marked "do not archive"         │
│                                                    │
│ 5. Archive Before Delete                          │
│    Media only deleted after successful archive    │
│                                                    │
│ 6. Audit Logging                                  │
│    Every operation logged to archive_operations   │
│                                                    │
│ 7. Integrity Checks                               │
│    Validate archives before restoration           │
│                                                    │
│ 8. Backup Verification                            │
│    Test backups immediately after creation        │
└───────────────────────────────────────────────────┘
```

---

## Restoration Process

```
┌─────────────────────────────────────────────┐
│      Story Restoration Workflow             │
└─────────────────────────────────────────────┘

1. VALIDATE
   ✓ Archived story exists
   ✓ Not already restored
   ✓ Original story_id not in active table
   ✓ Archive integrity check passes

2. RESTORE DATABASE
   → Create Story from archived JSON
   → Set is_archived=false
   → Update ArchivedStory (restored_at, restored_by)

3. RESTORE MEDIA (optional)
   → Copy files from archives/ to static/

4. AUDIT
   → Create archive_operations log entry

5. METRICS
   → Update Prometheus counters
```

---

## Implementation Priority Order

```
Priority 1 (Must Have - Week 1-4):
  ✓ Database schema migration
  ✓ Archive service (database integration)
  ✓ Backup service (basic pg_dump)
  ✓ Automated scripts

Priority 2 (Should Have - Week 5-6):
  ✓ Media cleanup service
  ✓ Admin UI
  ✓ Storage monitoring

Priority 3 (Nice to Have - Week 7-8):
  ✓ Advanced metrics
  ✓ Grafana dashboard
  ✓ Alert rules
  ✓ Backup verification

Future (Phase 2.0):
  ○ S3/Glacier integration
  ○ Backup encryption
  ○ Archive compression
  ○ Full-text search
```

---

## Risk Mitigation Summary

| Risk                    | Mitigation                        |
|------------------------|-----------------------------------|
| Data Loss              | Archive before delete             |
| Corrupted Backups      | Verify after creation             |
| Archive Table Growth   | Monitor + plan S3 migration       |
| Wrong File Deletion    | Audit all operations              |
| Restore Conflicts      | Check for existing story_id       |
| Backup Failures        | Prometheus alerts                 |
| Disk Space Exhaustion  | Storage alerts + auto-cleanup     |
| Performance Impact     | Batch operations + off-peak runs  |

---

## Testing Checklist

```
Unit Tests:
  □ archive_story() creates ArchivedStory record
  □ archive_story() copies media files
  □ restore_story() recreates Story correctly
  □ cleanup_expired_media() deletes correct files
  □ create_backup() generates valid backup
  □ verify_backup() detects corruption

Integration Tests:
  □ Complete archive → restore cycle
  □ Media cleanup after retention period
  □ Backup → verify → restore workflow
  □ Storage monitoring accuracy

Manual Tests:
  □ Archive a real story
  □ Restore archived story
  □ Cleanup media for old story
  □ Create and verify backup
  □ Trigger storage alert
  □ Test preservation flag
```

---

## Emergency Contacts / Procedures

### Disable Automation
```bash
sudo vim /etc/cron.d/ephergent-archiving
# Comment out all jobs with #
```

### Emergency Backup
```bash
pg_dump ephergent_db | gzip > /tmp/emergency_backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Check Last Operations
```sql
-- Last archive operations
SELECT * FROM archive_operations
ORDER BY started_at DESC LIMIT 10;

-- Last backups
SELECT * FROM backup_logs
ORDER BY started_at DESC LIMIT 10;

-- Storage usage
SELECT
    SUM(CASE WHEN is_archived THEN 1 ELSE 0 END) as archived_count,
    SUM(CASE WHEN is_archived=false THEN 1 ELSE 0 END) as active_count,
    SUM(CASE WHEN media_deleted_at IS NOT NULL THEN 1 ELSE 0 END) as media_deleted_count
FROM stories
WHERE current_step = 'completed';
```

---

## Success Criteria

After deployment, verify:

✓ Archive operations complete successfully daily
✓ No backup failures for 7 consecutive days
✓ Storage usage below warning threshold
✓ Can restore archived story successfully
✓ No data loss incidents
✓ System performance unchanged
✓ All Prometheus metrics collecting
✓ Grafana dashboard showing data
✓ Alerts trigger correctly

---

**Full Architecture:** `/PHASE_1_3_ARCHITECTURE.md` (40+ pages)
**Implementation Guide:** `/PHASE_1_3_IMPLEMENTATION_SUMMARY.md`
**This Quick Reference:** `/PHASE_1_3_QUICK_REFERENCE.md`
