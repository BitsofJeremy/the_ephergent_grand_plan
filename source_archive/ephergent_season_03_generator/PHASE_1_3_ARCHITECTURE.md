# Phase 1.3: Database Optimization - Technical Architecture

**Document Version:** 1.0
**Date:** 2025-10-10
**Status:** Design Document
**Author:** A.R.C.H.I.E. (AI Technical Lead)

---

## Executive Summary

This document provides the complete technical architecture for Phase 1.3: Database Optimization, focusing on three key areas:

1. **Story Archiving System** - Long-term storage for completed stories with search/restore capabilities
2. **Media Retention Policies** - Automated cleanup with configurable retention periods
3. **Backup & Recovery** - Automated PostgreSQL backups with verification and monitoring

The design prioritizes **production safety**, **data integrity**, and **operational maintainability** while integrating seamlessly with the existing Prometheus/Grafana monitoring infrastructure established in Phase 1.2.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Database Schema Design](#2-database-schema-design)
3. [Service Architecture](#3-service-architecture)
4. [Storage Strategy](#4-storage-strategy)
5. [Operational Procedures](#5-operational-procedures)
6. [Configuration Management](#6-configuration-management)
7. [Security & Safety](#7-security--safety)
8. [Implementation Plan](#8-implementation-plan)
9. [Risk Assessment](#9-risk-assessment)
10. [Monitoring & Alerting](#10-monitoring--alerting)

---

## 1. Architecture Overview

### 1.1 Design Philosophy

**Key Principles:**
- **Non-Destructive First**: Archiving moves data to separate storage before any deletion
- **Configurable by Default**: All thresholds and policies controlled via SystemConfig
- **Audit Everything**: Every archival/deletion/restore operation is logged
- **Fail-Safe Operations**: All operations have rollback capability and validation
- **Production Ready**: Designed for 24/7 operation with minimal manual intervention

### 1.2 Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                     Web Application Layer                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │ Admin Dashboard  │  │   Story Routes   │  │  Health Check  ││
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬───────┘│
└───────────┼────────────────────┼─────────────────────┼─────────┘
            │                    │                     │
            ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ArchiveService │  │MediaCleanup  │  │  BackupService     │   │
│  │               │  │Service       │  │                    │   │
│  │- Archive      │  │- Cleanup     │  │- Backup DB         │   │
│  │- Restore      │  │- Calculate   │  │- Verify            │   │
│  │- Search       │  │  Storage     │  │- Restore Test      │   │
│  └───────┬───────┘  └──────┬───────┘  └─────────┬──────────┘   │
└──────────┼──────────────────┼────────────────────┼──────────────┘
           │                  │                    │
           ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐        │
│  │   Story    │  │ArchivedStory │  │  SystemConfig    │        │
│  │StoryQueue  │  │              │  │  (retention      │        │
│  │StoryFailure│  │              │  │   policies)      │        │
│  └────────────┘  └──────────────┘  └──────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
           │                  │                    │
           ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     File System Layer                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  Active Media    │  │  Archived Media  │  │   Backups     │ │
│  │  /static/        │  │  /archives/      │  │  /backups/    │ │
│  │  generated_*     │  │  media/          │  │  db/          │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │                  │                    │
           ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Layer                              │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         Prometheus Metrics / Grafana Dashboard          │     │
│  │  - Archive operations      - Backup success/failure     │     │
│  │  - Storage usage           - DLQ stats (Phase 1.2)      │     │
│  │  - Cleanup operations      - Retry metrics (Phase 1.2)  │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Data Flow: Story Archiving Process

```
┌──────────────┐
│   Cron Job   │ (Daily at 2 AM)
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│ Find stories matching archive criteria:             │
│ - current_step = COMPLETED                          │
│ - completed_at < (now - archive_threshold)          │
│ - preserve_story = false                            │
│ - is_archived = false                               │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  For each story:     │
       └──────────┬───────────┘
                  │
                  ▼
   ┌──────────────────────────────────────┐
   │ 1. Create ArchivedStory record       │
   │    (full JSON snapshot of Story)     │
   └──────────────┬───────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────┐
   │ 2. Copy media files to archive dir   │
   │    /archives/YYYY-MM-DD_story-{id}/  │
   └──────────────┬───────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────┐
   │ 3. Update Story record:              │
   │    - is_archived = true              │
   │    - archived_at = now()             │
   │    - archive_id = FK to ArchivedStory│
   └──────────────┬───────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────┐
   │ 4. Create ArchiveOperation log entry │
   └──────────────┬───────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────┐
   │ 5. Update Prometheus metrics         │
   └──────────────────────────────────────┘
```

---

## 2. Database Schema Design

### 2.1 Design Decision: Dual-Table Approach

**Chosen Strategy:** Separate `archived_stories` table (NOT soft delete in main table)

**Rationale:**
- **Query Performance**: Active stories table remains small and fast
- **Index Efficiency**: Fewer rows = better index performance
- **Backup Strategy**: Can backup/archive tables separately
- **Storage Tiering**: Can move archived_stories to slower/cheaper storage
- **Migration Path**: Can dump archived_stories to cold storage (S3/Glacier) later

**Rejected Alternatives:**
1. **Soft Delete (is_archived flag only)**: Stories table grows indefinitely, indexes bloat
2. **Separate Database Schema**: Adds complexity, connection pooling issues
3. **Delete Without Archive**: Data loss risk, no restoration capability

### 2.2 New Tables

#### 2.2.1 ArchivedStory Table

```python
class ArchivedStory(db.Model):
    """
    Long-term storage for completed stories removed from active table.

    Design Philosophy:
    - Full JSON snapshot of original Story record (denormalized for safety)
    - Separate media file storage location
    - Searchable by key fields (title, narrator, date range)
    - Can be restored to active Stories table
    """
    __tablename__ = 'archived_stories'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Reference to original story (for restoration and tracking)
    original_story_id = db.Column(db.Integer, nullable=False, index=True)

    # Complete story data snapshot (JSON)
    # Contains full Story model as JSON for safe restoration
    story_data = db.Column(db.Text, nullable=False)  # JSON

    # Searchable fields (denormalized for performance)
    title = db.Column(db.String(200), nullable=True, index=True)
    topic = db.Column(db.Text, nullable=True)
    narrator_character_id = db.Column(db.String(100), nullable=True, index=True)
    genre = db.Column(db.String(50), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True, index=True)

    # Archive metadata
    archived_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    archived_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    archive_reason = db.Column(db.String(200), nullable=True)  # 'age_threshold', 'manual', 'storage_cleanup'

    # Archive location and status
    archive_path = db.Column(db.String(500), nullable=True)  # Path to archived media files
    archive_size_bytes = db.Column(db.BigInteger, nullable=True)  # Total size of archived media
    media_preserved = db.Column(db.Boolean, default=True, nullable=False)  # Were media files archived?

    # Restoration tracking
    restored_at = db.Column(db.DateTime, nullable=True)
    restored_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    restoration_notes = db.Column(db.Text, nullable=True)

    # Compression/optimization
    is_compressed = db.Column(db.Boolean, default=False, nullable=False)
    compression_ratio = db.Column(db.Float, nullable=True)

    # Relationships
    archiver = db.relationship('User', foreign_keys=[archived_by], backref='archived_stories')
    restorer = db.relationship('User', foreign_keys=[restored_by], backref='restored_stories')

    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_archived_story_search', 'archived_at', 'narrator_character_id'),
        db.Index('idx_archived_story_title', 'title'),
        db.Index('idx_archived_story_completed', 'completed_at'),
    )

    def get_story_data(self):
        """Parse story_data JSON field."""
        if self.story_data:
            try:
                return json.loads(self.story_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_story_data(self, data):
        """Set story_data as JSON."""
        self.story_data = json.dumps(data) if data else None
```

#### 2.2.2 ArchiveOperation Table (Audit Log)

```python
class ArchiveOperation(db.Model):
    """
    Audit log for all archive/restore operations.

    Purpose:
    - Track who did what, when
    - Debugging failed operations
    - Compliance and auditing
    - Operational metrics
    """
    __tablename__ = 'archive_operations'

    id = db.Column(db.Integer, primary_key=True)

    # Operation details
    operation_type = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )  # 'archive', 'restore', 'delete_media', 'compress'

    story_id = db.Column(db.Integer, nullable=False, index=True)
    archived_story_id = db.Column(db.Integer, db.ForeignKey('archived_stories.id'), nullable=True)

    # Execution details
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, success, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # User and automation tracking
    initiated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    automated = db.Column(db.Boolean, default=False, nullable=False)

    # Operation results
    files_processed = db.Column(db.Integer, default=0)
    bytes_processed = db.Column(db.BigInteger, default=0)
    error_message = db.Column(db.Text, nullable=True)

    # Metadata
    operation_metadata = db.Column(db.Text, nullable=True)  # JSON with operation-specific data

    # Relationships
    initiator = db.relationship('User', backref='archive_operations')
    archived_story = db.relationship('ArchivedStory', backref='operations')

    # Indexes
    __table_args__ = (
        db.Index('idx_archive_op_type_status', 'operation_type', 'status'),
        db.Index('idx_archive_op_date', 'started_at'),
    )
```

#### 2.2.3 BackupLog Table

```python
class BackupLog(db.Model):
    """
    Track database backup operations for monitoring and verification.
    """
    __tablename__ = 'backup_logs'

    id = db.Column(db.Integer, primary_key=True)

    # Backup identification
    backup_type = db.Column(db.String(20), nullable=False)  # 'full', 'incremental', 'schema_only'
    backup_path = db.Column(db.String(500), nullable=False)
    backup_size_bytes = db.Column(db.BigInteger, nullable=True)

    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)

    # Status and verification
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    verification_status = db.Column(db.String(20), nullable=True)  # 'passed', 'failed', 'skipped'
    verification_completed_at = db.Column(db.DateTime, nullable=True)

    # Metadata
    pg_dump_version = db.Column(db.String(50), nullable=True)
    database_size_bytes = db.Column(db.BigInteger, nullable=True)
    table_count = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    # Retention
    retention_expires_at = db.Column(db.DateTime, nullable=True, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        db.Index('idx_backup_status_date', 'status', 'started_at'),
        db.Index('idx_backup_retention', 'retention_expires_at', 'deleted_at'),
    )
```

### 2.3 Modifications to Existing Tables

#### 2.3.1 Story Table Additions

```python
# Add to existing Story model:

# Archive tracking
is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
archived_at = db.Column(db.DateTime, nullable=True)
archive_id = db.Column(db.Integer, db.ForeignKey('archived_stories.id'), nullable=True)

# Preservation flag (prevent automatic archiving)
preserve_story = db.Column(db.Boolean, default=False, nullable=False)
preserve_reason = db.Column(db.String(200), nullable=True)
preserve_until = db.Column(db.DateTime, nullable=True)  # Optional expiration

# Media retention tracking
media_deleted_at = db.Column(db.DateTime, nullable=True)
media_deletion_reason = db.Column(db.String(200), nullable=True)

# Relationship
archive_record = db.relationship('ArchivedStory', foreign_keys=[archive_id], backref='original_story')

# Add index for archive queries
__table_args__ = (
    # ... existing indexes ...
    db.Index('idx_story_archive_candidate', 'current_step', 'completed_at', 'is_archived', 'preserve_story'),
)
```

### 2.4 Migration Strategy

**Migration File:** `migrations/versions/XXXX_phase_1_3_archiving.py`

```python
"""Phase 1.3: Add archiving, retention, and backup tracking

Revision ID: XXXX
Revises: YYYY  # Previous migration
Create Date: 2025-10-10

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create archived_stories table
    op.create_table(
        'archived_stories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_story_id', sa.Integer(), nullable=False),
        sa.Column('story_data', sa.Text(), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('topic', sa.Text(), nullable=True),
        sa.Column('narrator_character_id', sa.String(100), nullable=True),
        sa.Column('genre', sa.String(50), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=False),
        sa.Column('archived_by', sa.Integer(), nullable=True),
        sa.Column('archive_reason', sa.String(200), nullable=True),
        sa.Column('archive_path', sa.String(500), nullable=True),
        sa.Column('archive_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('media_preserved', sa.Boolean(), nullable=False, default=True),
        sa.Column('restored_at', sa.DateTime(), nullable=True),
        sa.Column('restored_by', sa.Integer(), nullable=True),
        sa.Column('restoration_notes', sa.Text(), nullable=True),
        sa.Column('is_compressed', sa.Boolean(), nullable=False, default=False),
        sa.Column('compression_ratio', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['archived_by'], ['users.id']),
        sa.ForeignKeyConstraint(['restored_by'], ['users.id'])
    )

    # Create indexes
    op.create_index('idx_archived_story_id', 'archived_stories', ['original_story_id'])
    op.create_index('idx_archived_story_title', 'archived_stories', ['title'])
    op.create_index('idx_archived_story_search', 'archived_stories', ['archived_at', 'narrator_character_id'])
    op.create_index('idx_archived_story_completed', 'archived_stories', ['completed_at'])
    op.create_index('idx_archived_story_archived_at', 'archived_stories', ['archived_at'])

    # Create archive_operations table
    op.create_table(
        'archive_operations',
        # ... similar structure as above ...
    )

    # Create backup_logs table
    op.create_table(
        'backup_logs',
        # ... similar structure as above ...
    )

    # Add columns to stories table
    op.add_column('stories', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('stories', sa.Column('archived_at', sa.DateTime(), nullable=True))
    op.add_column('stories', sa.Column('archive_id', sa.Integer(), nullable=True))
    op.add_column('stories', sa.Column('preserve_story', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('stories', sa.Column('preserve_reason', sa.String(200), nullable=True))
    op.add_column('stories', sa.Column('preserve_until', sa.DateTime(), nullable=True))
    op.add_column('stories', sa.Column('media_deleted_at', sa.DateTime(), nullable=True))
    op.add_column('stories', sa.Column('media_deletion_reason', sa.String(200), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key('fk_story_archive', 'stories', 'archived_stories', ['archive_id'], ['id'])

    # Add index for archive queries
    op.create_index('idx_story_archive_candidate', 'stories',
                   ['current_step', 'completed_at', 'is_archived', 'preserve_story'])
    op.create_index('idx_story_is_archived', 'stories', ['is_archived'])

def downgrade():
    # Drop indexes first
    op.drop_index('idx_story_archive_candidate', 'stories')
    op.drop_index('idx_story_is_archived', 'stories')

    # Drop foreign key
    op.drop_constraint('fk_story_archive', 'stories', type_='foreignkey')

    # Drop columns
    op.drop_column('stories', 'media_deletion_reason')
    op.drop_column('stories', 'media_deleted_at')
    op.drop_column('stories', 'preserve_until')
    op.drop_column('stories', 'preserve_reason')
    op.drop_column('stories', 'preserve_story')
    op.drop_column('stories', 'archive_id')
    op.drop_column('stories', 'archived_at')
    op.drop_column('stories', 'is_archived')

    # Drop tables
    op.drop_table('backup_logs')
    op.drop_table('archive_operations')
    op.drop_table('archived_stories')
```

---

## 3. Service Architecture

### 3.1 Enhanced ArchiveService

The existing `/Users/jeremy/Documents/ephergent_next/ephergent_season_03_generator/ephergent_generator/services/archive_service.py` needs significant enhancements.

**Current Limitations:**
- Only archives to filesystem (no database archiving)
- No search/restore capabilities
- No integration with Story model flags
- No audit logging

**New Architecture:**

```python
"""
Enhanced Archive Service for Phase 1.3

Responsibilities:
1. Archive completed stories to archived_stories table
2. Copy media files to archive directory
3. Search archived stories
4. Restore archived stories to active table
5. Audit all operations
"""

class ArchiveService:
    def __init__(self):
        self.archive_base = self._get_archive_base_path()
        self.logger = logging.getLogger(__name__)

    # ========== ARCHIVING OPERATIONS ==========

    def archive_story(
        self,
        story: Story,
        reason: str = 'age_threshold',
        user_id: int = None,
        preserve_media: bool = True
    ) -> ArchivedStory:
        """
        Archive a completed story (database + media files).

        Process:
        1. Validate story is eligible for archiving
        2. Create ArchivedStory record with JSON snapshot
        3. Copy media files to archive directory
        4. Update Story record (is_archived=True)
        5. Create ArchiveOperation audit log
        6. Update Prometheus metrics

        Args:
            story: Story to archive
            reason: Reason for archiving ('age_threshold', 'manual', 'storage_cleanup')
            user_id: User who initiated archiving (None if automated)
            preserve_media: Whether to copy media files to archive

        Returns:
            ArchivedStory record

        Raises:
            ValueError: If story is not eligible for archiving
            ArchiveException: If archiving fails
        """
        pass

    def archive_stories_by_age(
        self,
        age_days: int = None,
        dry_run: bool = False,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Archive all completed stories older than specified age.

        This is the method called by the automated cron job.

        Args:
            age_days: Age threshold in days (uses SystemConfig if None)
            dry_run: If True, simulate but don't actually archive
            limit: Maximum number of stories to archive in one run

        Returns:
            Dict with archiving statistics
        """
        pass

    # ========== SEARCH OPERATIONS ==========

    def search_archived_stories(
        self,
        query: str = None,
        narrator: str = None,
        genre: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ArchivedStory]:
        """
        Search archived stories with flexible criteria.

        Returns:
            List of matching ArchivedStory records
        """
        pass

    def get_archived_story(self, archived_story_id: int) -> Optional[ArchivedStory]:
        """Get specific archived story by ID."""
        pass

    # ========== RESTORE OPERATIONS ==========

    def restore_story(
        self,
        archived_story_id: int,
        user_id: int,
        restore_media: bool = True,
        notes: str = None
    ) -> Story:
        """
        Restore an archived story back to active stories table.

        Process:
        1. Retrieve ArchivedStory record
        2. Validate original story doesn't exist in active table
        3. Create new Story from archived JSON data
        4. Optionally restore media files
        5. Update ArchivedStory (restored_at, restored_by)
        6. Create ArchiveOperation audit log
        7. Update metrics

        Args:
            archived_story_id: ID of ArchivedStory to restore
            user_id: User performing restoration
            restore_media: Whether to copy media files back
            notes: Optional restoration notes

        Returns:
            Restored Story record

        Raises:
            ValueError: If archived story not found or already restored
            RestoreException: If restoration fails
        """
        pass

    # ========== UTILITY METHODS ==========

    def get_archive_statistics(self) -> Dict[str, Any]:
        """
        Get archive statistics for dashboard.

        Returns:
            {
                'total_archived_stories': int,
                'total_archive_size_gb': float,
                'archived_this_month': int,
                'oldest_archive': datetime,
                'newest_archive': datetime,
                'stories_by_narrator': Dict[str, int],
                'media_preserved_count': int,
                'media_deleted_count': int
            }
        """
        pass

    def calculate_archive_size(self, story: Story) -> int:
        """Calculate total size of story's media files in bytes."""
        pass

    def validate_archive_integrity(self, archived_story_id: int) -> Dict[str, Any]:
        """
        Verify archived story data and media files are intact.

        Returns:
            {
                'valid': bool,
                'issues': List[str],
                'media_files_found': int,
                'media_files_missing': int
            }
        """
        pass

    # ========== PRIVATE METHODS ==========

    def _create_archive_operation_log(
        self,
        operation_type: str,
        story_id: int,
        status: str,
        user_id: int = None,
        **metadata
    ) -> ArchiveOperation:
        """Create audit log entry for archive operation."""
        pass

    def _copy_media_to_archive(
        self,
        story: Story,
        archive_dir: Path
    ) -> Tuple[int, int]:
        """
        Copy all media files for story to archive directory.

        Returns:
            Tuple of (files_copied, total_bytes)
        """
        pass

    def _create_story_snapshot(self, story: Story) -> Dict:
        """Create complete JSON snapshot of story data."""
        pass
```

### 3.2 MediaCleanupService (New)

**File:** `ephergent_generator/services/media_cleanup_service.py`

```python
"""
Media Cleanup Service for Phase 1.3

Responsibilities:
1. Delete media files for stories past retention period
2. Calculate storage usage
3. Respect preserve_story flag
4. Audit all deletions
5. Generate cleanup reports
"""

class MediaCleanupService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.static_base = Path(__file__).parent.parent / 'static'

    # ========== CLEANUP OPERATIONS ==========

    def cleanup_expired_media(
        self,
        retention_days: int = None,
        dry_run: bool = False,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Delete media files for completed stories past retention period.

        Process:
        1. Find stories with:
           - current_step = COMPLETED
           - completed_at < (now - retention_days)
           - is_archived = true (safer to delete archived stories)
           - preserve_story = false
           - media_deleted_at IS NULL
        2. For each story, delete media files:
           - Images (static/generated_images/*)
           - Audio (static/generated_audio/*)
           - Video (static/generated_videos/*)
        3. Update Story record (media_deleted_at, media_deletion_reason)
        4. Create ArchiveOperation audit log
        5. Update metrics

        Args:
            retention_days: Retention period in days (uses SystemConfig if None)
            dry_run: Simulate without actually deleting
            limit: Max files to delete in one run (safety limit)

        Returns:
            {
                'stories_processed': int,
                'files_deleted': int,
                'bytes_freed': int,
                'errors': List[str]
            }
        """
        pass

    def delete_story_media(
        self,
        story: Story,
        reason: str = 'retention_policy'
    ) -> Dict[str, Any]:
        """
        Delete all media files for a specific story.

        Returns:
            {
                'files_deleted': int,
                'bytes_freed': int,
                'media_types': List[str]  # ['images', 'audio', 'video']
            }
        """
        pass

    # ========== STORAGE MONITORING ==========

    def calculate_storage_usage(self) -> Dict[str, Any]:
        """
        Calculate current storage usage by media type.

        Returns:
            {
                'total_bytes': int,
                'total_gb': float,
                'by_type': {
                    'images': {'count': int, 'bytes': int},
                    'audio': {'count': int, 'bytes': int},
                    'video': {'count': int, 'bytes': int}
                },
                'archived_bytes': int,
                'active_bytes': int,
                'deletable_bytes': int  # Past retention period
            }
        """
        pass

    def get_cleanup_candidates(
        self,
        retention_days: int = None
    ) -> List[Story]:
        """
        Find stories eligible for media cleanup.

        Returns:
            List of Story records that can have media deleted
        """
        pass

    def estimate_cleanup_impact(
        self,
        retention_days: int
    ) -> Dict[str, Any]:
        """
        Estimate how much space would be freed with given retention period.

        Returns:
            {
                'stories_affected': int,
                'estimated_bytes_freed': int,
                'estimated_gb_freed': float,
                'oldest_story_date': datetime,
                'newest_story_date': datetime
            }
        """
        pass

    # ========== PRESERVATION MANAGEMENT ==========

    def set_story_preservation(
        self,
        story_id: int,
        preserve: bool,
        reason: str,
        until: datetime = None,
        user_id: int = None
    ) -> Story:
        """
        Set preservation flag on a story to prevent archiving/cleanup.

        Args:
            story_id: Story to preserve
            preserve: True to preserve, False to unpreserve
            reason: Why story should be preserved
            until: Optional expiration date for preservation
            user_id: User setting preservation
        """
        pass

    def expire_preservation_flags(self) -> int:
        """
        Remove preservation flags that have expired.

        Returns:
            Number of stories un-preserved
        """
        pass

    # ========== PRIVATE METHODS ==========

    def _delete_file_safely(self, file_path: Path) -> bool:
        """Delete file with error handling and logging."""
        pass

    def _get_file_size(self, path: str) -> int:
        """Get size of file from path (handles URLs and local paths)."""
        pass
```

### 3.3 BackupService (New)

**File:** `ephergent_generator/services/backup_service.py`

```python
"""
Database Backup Service for Phase 1.3

Responsibilities:
1. Execute PostgreSQL pg_dump backups
2. Verify backup integrity
3. Manage backup retention
4. Test restoration capability
5. Monitor backup health
"""

class BackupService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backup_base = self._get_backup_base_path()
        self.pg_dump_path = self._find_pg_dump()

    # ========== BACKUP OPERATIONS ==========

    def create_backup(
        self,
        backup_type: str = 'full',
        verify: bool = True
    ) -> BackupLog:
        """
        Create PostgreSQL database backup using pg_dump.

        Process:
        1. Create BackupLog record (status='pending')
        2. Generate backup filename with timestamp
        3. Execute pg_dump command
        4. Compress backup file (gzip)
        5. Update BackupLog with results
        6. Optionally verify backup
        7. Update Prometheus metrics

        Args:
            backup_type: 'full', 'schema_only', or 'data_only'
            verify: Whether to verify backup after creation

        Returns:
            BackupLog record

        Raises:
            BackupException: If backup fails
        """
        pass

    def verify_backup(self, backup_log_id: int) -> Dict[str, Any]:
        """
        Verify backup file integrity and restore-ability.

        Verification Steps:
        1. Check file exists and is readable
        2. Verify gzip integrity
        3. Check file size is reasonable (not too small)
        4. Parse pg_dump header
        5. Optionally test restore to temporary database

        Returns:
            {
                'valid': bool,
                'file_exists': bool,
                'gzip_valid': bool,
                'size_valid': bool,
                'header_valid': bool,
                'restore_tested': bool,
                'issues': List[str]
            }
        """
        pass

    def test_restore(self, backup_log_id: int) -> Dict[str, Any]:
        """
        Test restore backup to temporary database.

        WARNING: This is a HEAVY operation, only run periodically.

        Process:
        1. Create temporary database
        2. Restore backup to temp database
        3. Run basic validation queries
        4. Drop temporary database

        Returns:
            {
                'success': bool,
                'temp_db_name': str,
                'restore_duration': int,
                'row_counts': Dict[str, int],
                'errors': List[str]
            }
        """
        pass

    # ========== RETENTION MANAGEMENT ==========

    def cleanup_old_backups(
        self,
        retention_days: int = None
    ) -> Dict[str, Any]:
        """
        Delete backup files older than retention period.

        Retention Strategy:
        - Keep all daily backups for last 7 days
        - Keep weekly backups (Sunday) for last 30 days
        - Keep monthly backups (1st of month) for last 365 days
        - Delete everything older

        Args:
            retention_days: Days to keep backups (uses SystemConfig if None)

        Returns:
            {
                'backups_deleted': int,
                'bytes_freed': int,
                'oldest_remaining': datetime
            }
        """
        pass

    def get_backup_retention_policy(self) -> Dict[str, int]:
        """
        Get current backup retention policy from SystemConfig.

        Returns:
            {
                'daily_retention_days': int,
                'weekly_retention_days': int,
                'monthly_retention_days': int
            }
        """
        pass

    # ========== MONITORING ==========

    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Get backup statistics for dashboard.

        Returns:
            {
                'total_backups': int,
                'total_size_gb': float,
                'latest_backup': BackupLog,
                'last_success': datetime,
                'last_failure': datetime,
                'success_rate_30d': float,
                'average_size_gb': float,
                'average_duration_minutes': float
            }
        """
        pass

    def check_backup_health(self) -> Dict[str, Any]:
        """
        Check backup system health for alerting.

        Health Checks:
        - Last backup within 24 hours?
        - Recent backups successful?
        - Backup sizes consistent?
        - Disk space available?

        Returns:
            {
                'healthy': bool,
                'issues': List[str],
                'warnings': List[str],
                'last_backup_age_hours': float
            }
        """
        pass

    # ========== RESTORATION ==========

    def restore_from_backup(
        self,
        backup_log_id: int,
        target_database: str = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Restore database from backup file.

        WARNING: This is a DESTRUCTIVE operation. Use with extreme caution.

        Safety Requirements:
        - Must provide target_database explicitly
        - Must start with dry_run=True
        - Requires admin user confirmation
        - Creates restore confirmation record

        Args:
            backup_log_id: Backup to restore from
            target_database: Name of target database (required)
            dry_run: If True, validate only, don't restore

        Returns:
            {
                'success': bool,
                'restored_tables': List[str],
                'duration_seconds': int,
                'errors': List[str]
            }
        """
        pass

    # ========== PRIVATE METHODS ==========

    def _execute_pg_dump(
        self,
        output_path: Path,
        backup_type: str
    ) -> Tuple[bool, str]:
        """Execute pg_dump command and return (success, error_message)."""
        pass

    def _get_database_credentials(self) -> Dict[str, str]:
        """Get database connection details from config."""
        pass

    def _calculate_backup_size(self, backup_path: Path) -> int:
        """Get size of backup file in bytes."""
        pass

    def _generate_backup_filename(self, backup_type: str) -> str:
        """
        Generate backup filename.

        Format: ephergent_db_YYYYMMDD_HHMMSS_full.sql.gz
        """
        pass
```

---

## 4. Storage Strategy

### 4.1 Directory Structure

```
/Users/jeremy/Documents/ephergent_next/ephergent_season_03_generator/
│
├── ephergent_generator/
│   └── static/
│       ├── generated_images/     # Active story images
│       ├── generated_audio/      # Active story audio
│       └── generated_videos/     # Active story videos
│
├── archives/                     # NEW: Archived story data
│   ├── stories/                  # Archived story media
│   │   ├── 2025-10-01_story-123_robot_learns_love/
│   │   │   ├── metadata.json
│   │   │   ├── story.md
│   │   │   ├── images/
│   │   │   ├── audio/
│   │   │   └── video/
│   │   └── 2025-10-02_story-124_space_adventure/
│   │       └── ...
│   └── indexes/                  # Search indexes (optional)
│
└── backups/                      # NEW: Database backups
    ├── daily/
    │   ├── ephergent_db_20251010_020000_full.sql.gz
    │   └── ephergent_db_20251009_020000_full.sql.gz
    ├── weekly/
    │   └── ephergent_db_20251006_020000_full.sql.gz
    └── monthly/
        └── ephergent_db_20251001_020000_full.sql.gz
```

### 4.2 Storage Tiers

**Tier 1: Active Stories (Hot Storage)**
- Location: `static/generated_*`
- Performance: Fast local SSD
- Retention: Until archived or retention period expires
- Backup: Included in database backups (paths only)

**Tier 2: Archived Stories (Warm Storage)**
- Location: `archives/stories/`
- Performance: Standard HDD acceptable
- Retention: Indefinite (can be moved to cold storage later)
- Backup: Separate backup schedule

**Tier 3: Database Backups (Cold Storage)**
- Location: `backups/`
- Performance: Standard HDD acceptable
- Retention: 7 days (daily), 30 days (weekly), 365 days (monthly)
- Backup: Replicated to remote location (manual for Phase 1.3)

### 4.3 Media Retention Policy

**Default Retention Periods (Configurable via SystemConfig):**

```python
# SystemConfig entries for retention policies
RETENTION_CONFIGS = {
    'media_retention_days': {
        'value': 90,  # Keep media for 90 days after completion
        'type': 'int',
        'description': 'Days to retain media files for completed stories',
        'category': 'retention',
        'is_public': False
    },
    'archive_age_threshold_days': {
        'value': 60,  # Archive stories after 60 days
        'type': 'int',
        'description': 'Days before archiving completed stories to archive table',
        'category': 'retention',
        'is_public': False
    },
    'media_cleanup_batch_size': {
        'value': 100,  # Process 100 stories per cleanup run
        'type': 'int',
        'description': 'Maximum stories to process in single cleanup operation',
        'category': 'retention',
        'is_public': False
    },
    'preserve_media_on_archive': {
        'value': True,  # Copy media to archive by default
        'type': 'bool',
        'description': 'Whether to copy media files when archiving stories',
        'category': 'retention',
        'is_public': False
    }
}
```

**Retention Workflow:**

```
Story Completion → Archive After 60 Days → Delete Media After 90 Days

Day 0:   Story completed (current_step=COMPLETED)
         ↓
Day 60:  Story archived to archived_stories table
         (is_archived=True, media still in static/)
         ↓
Day 90:  Media files deleted from static/
         (media_deleted_at set, media still in archives/)
         ↓
Day ∞:   Archived data remains indefinitely
         (can be moved to S3/Glacier in future)
```

### 4.4 Disk Space Monitoring

**Storage Thresholds (Configurable):**

```python
STORAGE_THRESHOLDS = {
    'storage_warning_threshold_gb': {
        'value': 100,  # Warning at 100GB
        'type': 'int',
        'description': 'Disk usage threshold for warnings (GB)',
        'category': 'storage',
        'is_public': False
    },
    'storage_critical_threshold_gb': {
        'value': 150,  # Critical at 150GB
        'type': 'int',
        'description': 'Disk usage threshold for critical alerts (GB)',
        'category': 'storage',
        'is_public': False
    },
    'auto_cleanup_enabled': {
        'value': False,  # Manual approval required by default
        'type': 'bool',
        'description': 'Automatically cleanup media when storage critical',
        'category': 'storage',
        'is_public': False
    }
}
```

---

## 5. Operational Procedures

### 5.1 Automated Archiving Cron Job

**Deployment Location:** Debian VM (10.0.0.99)

**Cron Configuration:** `/etc/cron.d/ephergent-archiving`

```bash
# /etc/cron.d/ephergent-archiving
# Daily archiving of old stories at 2:00 AM

# Story archiving (database + media copy)
0 2 * * * ephergent cd /path/to/ephergent_season_03_generator && source .venv/bin/activate && python -m ephergent_generator.scripts.archive_stories >> /var/log/ephergent/archive.log 2>&1

# Media cleanup (delete old media files)
30 2 * * * ephergent cd /path/to/ephergent_season_03_generator && source .venv/bin/activate && python -m ephergent_generator.scripts.cleanup_media >> /var/log/ephergent/cleanup.log 2>&1

# Database backup
0 3 * * * ephergent cd /path/to/ephergent_season_03_generator && source .venv/bin/activate && python -m ephergent_generator.scripts.backup_database >> /var/log/ephergent/backup.log 2>&1

# Backup verification (weekly on Sundays)
0 4 * * 0 ephergent cd /path/to/ephergent_season_03_generator && source .venv/bin/activate && python -m ephergent_generator.scripts.verify_backups >> /var/log/ephergent/verify.log 2>&1
```

### 5.2 Archive Script

**File:** `ephergent_generator/scripts/archive_stories.py`

```python
#!/usr/bin/env python3
"""
Automated story archiving script.

Usage:
    python -m ephergent_generator.scripts.archive_stories [options]

Options:
    --dry-run          Simulate without actually archiving
    --age-days N       Archive stories older than N days (overrides config)
    --limit N          Maximum stories to archive in this run
    --force            Skip safety checks
    --verbose          Detailed logging
"""

import sys
import argparse
from datetime import datetime
from ephergent_generator import create_app, db
from ephergent_generator.services.archive_service import ArchiveService
from ephergent_generator.models import SystemConfig

def main():
    parser = argparse.ArgumentParser(description='Archive old completed stories')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without archiving')
    parser.add_argument('--age-days', type=int, help='Archive stories older than N days')
    parser.add_argument('--limit', type=int, help='Maximum stories to archive')
    parser.add_argument('--force', action='store_true', help='Skip safety checks')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    args = parser.parse_args()

    # Create Flask app context
    app = create_app()
    with app.app_context():
        archive_service = ArchiveService()

        # Get age threshold from config if not specified
        age_days = args.age_days or SystemConfig.get_config('archive_age_threshold_days', 60)

        print(f"Starting story archiving process...")
        print(f"Age threshold: {age_days} days")
        print(f"Dry run: {args.dry_run}")

        # Run archiving
        result = archive_service.archive_stories_by_age(
            age_days=age_days,
            dry_run=args.dry_run,
            limit=args.limit
        )

        # Print results
        print(f"\nArchiving Complete:")
        print(f"  Stories archived: {result['archived_count']}")
        print(f"  Stories skipped: {result['skipped_count']}")
        print(f"  Errors: {result['error_count']}")
        print(f"  Total size archived: {result['total_bytes'] / (1024**3):.2f} GB")

        if result['errors']:
            print(f"\nErrors encountered:")
            for error in result['errors']:
                print(f"  - {error}")
            sys.exit(1)

        sys.exit(0)

if __name__ == '__main__':
    main()
```

### 5.3 Backup Script

**File:** `ephergent_generator/scripts/backup_database.py`

```python
#!/usr/bin/env python3
"""
Automated database backup script.

Usage:
    python -m ephergent_generator.scripts.backup_database [options]

Options:
    --type TYPE        Backup type: full (default), schema_only, data_only
    --no-verify        Skip backup verification
    --test-restore     Test restore to temporary database (slow)
"""

import sys
import argparse
from ephergent_generator import create_app
from ephergent_generator.services.backup_service import BackupService

def main():
    parser = argparse.ArgumentParser(description='Backup PostgreSQL database')
    parser.add_argument('--type', choices=['full', 'schema_only', 'data_only'],
                       default='full', help='Backup type')
    parser.add_argument('--no-verify', action='store_true', help='Skip verification')
    parser.add_argument('--test-restore', action='store_true', help='Test restore')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        backup_service = BackupService()

        print(f"Starting database backup ({args.type})...")

        # Create backup
        backup_log = backup_service.create_backup(
            backup_type=args.type,
            verify=not args.no_verify
        )

        if backup_log.status == 'success':
            print(f"✓ Backup successful: {backup_log.backup_path}")
            print(f"  Size: {backup_log.backup_size_bytes / (1024**2):.2f} MB")
            print(f"  Duration: {backup_log.duration_seconds}s")

            if args.test_restore:
                print(f"\nTesting restore...")
                restore_result = backup_service.test_restore(backup_log.id)
                if restore_result['success']:
                    print(f"✓ Restore test successful")
                else:
                    print(f"✗ Restore test failed: {restore_result['errors']}")
                    sys.exit(1)

            # Cleanup old backups
            cleanup_result = backup_service.cleanup_old_backups()
            print(f"\nCleaned up {cleanup_result['backups_deleted']} old backups")

            sys.exit(0)
        else:
            print(f"✗ Backup failed: {backup_log.error_message}")
            sys.exit(1)

if __name__ == '__main__':
    main()
```

### 5.4 Manual Operations

#### Archive a Specific Story

```bash
# Via CLI
python -c "
from ephergent_generator import create_app, db
from ephergent_generator.services.archive_service import ArchiveService
from ephergent_generator.models import Story

app = create_app()
with app.app_context():
    service = ArchiveService()
    story = Story.query.get(123)
    archived = service.archive_story(story, reason='manual', user_id=1)
    print(f'Archived story {story.id} to {archived.archive_path}')
"
```

#### Restore an Archived Story

```bash
# Via CLI
python -c "
from ephergent_generator import create_app
from ephergent_generator.services.archive_service import ArchiveService

app = create_app()
with app.app_context():
    service = ArchiveService()
    story = service.restore_story(archived_story_id=456, user_id=1, restore_media=True)
    print(f'Restored story {story.id}: {story.title}')
"
```

#### Emergency Backup

```bash
# Create immediate backup
python -m ephergent_generator.scripts.backup_database --type full --test-restore
```

---

## 6. Configuration Management

### 6.1 SystemConfig Entries

**File:** `ephergent_generator/scripts/init_phase_1_3_config.py`

```python
#!/usr/bin/env python3
"""
Initialize SystemConfig entries for Phase 1.3.

Run after migration to set up default configuration values.
"""

from ephergent_generator import create_app, db
from ephergent_generator.models import SystemConfig

PHASE_1_3_CONFIGS = {
    # ========== ARCHIVING ==========
    'archive_enabled': {
        'value': True,
        'type': 'bool',
        'description': 'Enable automated story archiving',
        'category': 'archiving',
        'is_public': False
    },
    'archive_age_threshold_days': {
        'value': 60,
        'type': 'int',
        'description': 'Archive completed stories older than N days',
        'category': 'archiving',
        'is_public': False
    },
    'archive_batch_size': {
        'value': 50,
        'type': 'int',
        'description': 'Maximum stories to archive per automated run',
        'category': 'archiving',
        'is_public': False
    },
    'archive_preserve_media': {
        'value': True,
        'type': 'bool',
        'description': 'Copy media files to archive directory',
        'category': 'archiving',
        'is_public': False
    },

    # ========== MEDIA RETENTION ==========
    'media_cleanup_enabled': {
        'value': True,
        'type': 'bool',
        'description': 'Enable automated media cleanup',
        'category': 'retention',
        'is_public': False
    },
    'media_retention_days': {
        'value': 90,
        'type': 'int',
        'description': 'Delete media files N days after story completion',
        'category': 'retention',
        'is_public': False
    },
    'media_cleanup_batch_size': {
        'value': 100,
        'type': 'int',
        'description': 'Maximum files to delete per cleanup run',
        'category': 'retention',
        'is_public': False
    },
    'media_cleanup_require_archive': {
        'value': True,
        'type': 'bool',
        'description': 'Only delete media for archived stories',
        'category': 'retention',
        'is_public': False
    },

    # ========== STORAGE MONITORING ==========
    'storage_warning_threshold_gb': {
        'value': 100,
        'type': 'int',
        'description': 'Warn when storage exceeds N GB',
        'category': 'storage',
        'is_public': False
    },
    'storage_critical_threshold_gb': {
        'value': 150,
        'type': 'int',
        'description': 'Critical alert when storage exceeds N GB',
        'category': 'storage',
        'is_public': False
    },
    'storage_auto_cleanup': {
        'value': False,
        'type': 'bool',
        'description': 'Automatically cleanup when storage critical',
        'category': 'storage',
        'is_public': False
    },

    # ========== BACKUP ==========
    'backup_enabled': {
        'value': True,
        'type': 'bool',
        'description': 'Enable automated database backups',
        'category': 'backup',
        'is_public': False
    },
    'backup_daily_retention': {
        'value': 7,
        'type': 'int',
        'description': 'Keep daily backups for N days',
        'category': 'backup',
        'is_public': False
    },
    'backup_weekly_retention': {
        'value': 30,
        'type': 'int',
        'description': 'Keep weekly backups for N days',
        'category': 'backup',
        'is_public': False
    },
    'backup_monthly_retention': {
        'value': 365,
        'type': 'int',
        'description': 'Keep monthly backups for N days',
        'category': 'backup',
        'is_public': False
    },
    'backup_verify_enabled': {
        'value': True,
        'type': 'bool',
        'description': 'Verify backups after creation',
        'category': 'backup',
        'is_public': False
    },
    'backup_test_restore_weekly': {
        'value': True,
        'type': 'bool',
        'description': 'Test restore weekly (resource intensive)',
        'category': 'backup',
        'is_public': False
    }
}

def init_config():
    app = create_app()
    with app.app_context():
        for key, config in PHASE_1_3_CONFIGS.items():
            existing = SystemConfig.query.filter_by(config_key=key).first()
            if existing:
                print(f"Skipping {key} (already exists)")
                continue

            SystemConfig.set_config(
                key=key,
                value=config['value'],
                config_type=config['type'],
                description=config['description'],
                category=config['category'],
                is_public=config['is_public']
            )
            print(f"Created config: {key}")

        db.session.commit()
        print(f"\n✓ Initialized {len(PHASE_1_3_CONFIGS)} configuration entries")

if __name__ == '__main__':
    init_config()
```

### 6.2 Admin UI Requirements

**New Admin Pages Needed:**

1. **Archive Management** (`/admin/archives`)
   - Search archived stories
   - View archive statistics
   - Restore individual stories
   - Bulk archive operations

2. **Storage Dashboard** (`/admin/storage`)
   - Current storage usage by type
   - Cleanup candidates list
   - Manual cleanup triggers
   - Preservation flag management

3. **Backup Management** (`/admin/backups`)
   - Backup history and status
   - Manual backup trigger
   - Backup verification status
   - Restore interface (with safeguards)

4. **Configuration** (`/admin/config/retention`)
   - Edit retention policies
   - Test configuration impact
   - View configuration history

---

## 7. Security & Safety

### 7.1 Backup Encryption (Future Enhancement)

**Current Phase 1.3 Scope:**
- Backups stored unencrypted on local filesystem
- Access controlled by file permissions (600)
- Located on VM with SSH key authentication

**Future Enhancement (Phase 2.0):**
```bash
# Encrypted backup with GPG
pg_dump dbname | gzip | gpg --encrypt --recipient admin@ephergent.local > backup.sql.gz.gpg

# Restore
gpg --decrypt backup.sql.gz.gpg | gunzip | psql dbname
```

### 7.2 Archival Data Integrity

**Integrity Checks:**

1. **Checksum Verification**
   - Generate SHA256 hash of archive when created
   - Store hash in ArchivedStory.archive_metadata
   - Verify hash periodically

2. **JSON Validation**
   - Validate story_data JSON structure on archive
   - Validate again before restoration

3. **Media File Verification**
   - Check all expected media files exist
   - Verify file sizes are reasonable
   - Periodic integrity sweeps

**Implementation:**

```python
def validate_archive_integrity(self, archived_story_id: int) -> Dict[str, Any]:
    """
    Comprehensive integrity check for archived story.
    """
    archived = ArchivedStory.query.get(archived_story_id)
    issues = []

    # Check JSON parses correctly
    try:
        story_data = archived.get_story_data()
        if not story_data:
            issues.append("Empty story data")
    except Exception as e:
        issues.append(f"Invalid JSON: {e}")

    # Check media files exist
    if archived.archive_path:
        archive_dir = Path(archived.archive_path)
        if not archive_dir.exists():
            issues.append(f"Archive directory missing: {archive_dir}")
        else:
            # Check expected files
            expected_files = ['metadata.json', 'story.md']
            for file in expected_files:
                if not (archive_dir / file).exists():
                    issues.append(f"Missing file: {file}")

    # Verify checksum if present
    metadata = json.loads(archived.archive_metadata or '{}')
    if 'checksum' in metadata:
        current_checksum = self._calculate_checksum(archive_dir)
        if current_checksum != metadata['checksum']:
            issues.append("Checksum mismatch - data may be corrupted")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'checked_at': datetime.utcnow()
    }
```

### 7.3 Restoration Safeguards

**Safety Measures:**

1. **No Overwrite Protection**
   - Check if story_id already exists in active stories
   - Require explicit confirmation to overwrite

2. **Dry Run First**
   - Always simulate restoration before executing
   - Show what will be restored

3. **Audit Trail**
   - Log all restorations with user, timestamp, reason
   - Track restoration success/failure

4. **Rollback Capability**
   - Keep original archived record until restoration confirmed
   - Allow re-archive if restoration fails

**Restoration Process:**

```python
def restore_story(self, archived_story_id: int, user_id: int,
                 restore_media: bool = True, notes: str = None) -> Story:
    """
    Safe story restoration with multiple validation steps.
    """
    # 1. Validate archived story exists
    archived = ArchivedStory.query.get(archived_story_id)
    if not archived:
        raise ValueError(f"Archived story {archived_story_id} not found")

    # 2. Check if already restored
    if archived.restored_at:
        raise ValueError(f"Story already restored on {archived.restored_at}")

    # 3. Check if original story ID exists
    existing = Story.query.get(archived.original_story_id)
    if existing:
        raise ValueError(
            f"Story {archived.original_story_id} already exists in active table. "
            f"Use force=True to overwrite."
        )

    # 4. Validate archive integrity
    integrity = self.validate_archive_integrity(archived_story_id)
    if not integrity['valid']:
        raise ValueError(f"Archive integrity check failed: {integrity['issues']}")

    # 5. Start restoration (wrapped in transaction)
    try:
        story_data = archived.get_story_data()
        story = Story(**story_data)
        story.is_archived = False  # Restore to active status
        story.archived_at = None
        story.archive_id = None

        db.session.add(story)

        # 6. Restore media files if requested
        if restore_media and archived.archive_path:
            self._restore_media_files(archived, story)

        # 7. Update archived record
        archived.restored_at = datetime.utcnow()
        archived.restored_by = user_id
        archived.restoration_notes = notes

        # 8. Create audit log
        self._create_archive_operation_log(
            operation_type='restore',
            story_id=story.id,
            status='success',
            user_id=user_id,
            archived_story_id=archived_story_id
        )

        db.session.commit()

        self.logger.info(f"Successfully restored story {story.id} from archive {archived_story_id}")
        return story

    except Exception as e:
        db.session.rollback()
        self.logger.error(f"Failed to restore story {archived_story_id}: {e}")
        raise
```

### 7.4 Audit Logging

**All operations log to:**
1. Application logs (`season_03_generator.log`)
2. Database (`archive_operations` table)
3. Prometheus metrics

**Logged Information:**
- Who performed the operation (user_id or 'system')
- What operation (archive, restore, delete_media, compress)
- When it occurred (timestamp)
- Which story (story_id)
- Result (success/failure)
- Detailed metadata (files affected, bytes processed, errors)

---

## 8. Implementation Plan

### 8.1 Implementation Phases

**Phase 1.3.1: Database Schema & Models (Week 1)**
- Create migration file
- Add new models (ArchivedStory, ArchiveOperation, BackupLog)
- Update Story model with archive fields
- Initialize SystemConfig entries
- Test migration on development database

**Phase 1.3.2: Archive Service (Week 2)**
- Enhance existing ArchiveService
- Implement archive_story() with database integration
- Implement search_archived_stories()
- Implement restore_story()
- Add integrity validation
- Unit tests for archive operations

**Phase 1.3.3: Media Cleanup Service (Week 3)**
- Create MediaCleanupService
- Implement cleanup_expired_media()
- Implement storage monitoring
- Implement preservation flag management
- Unit tests for cleanup operations

**Phase 1.3.4: Backup Service (Week 4)**
- Create BackupService
- Implement pg_dump wrapper
- Implement backup verification
- Implement retention management
- Test restore procedures
- Unit tests for backup operations

**Phase 1.3.5: Automation Scripts (Week 5)**
- Create archive_stories.py script
- Create cleanup_media.py script
- Create backup_database.py script
- Set up cron jobs on production VM
- Test automated execution

**Phase 1.3.6: Admin UI (Week 6)**
- Add Archive Management page
- Add Storage Dashboard
- Add Backup Management page
- Add Configuration editor
- Integration testing

**Phase 1.3.7: Monitoring & Alerts (Week 7)**
- Add Prometheus metrics for archiving
- Add Prometheus metrics for storage
- Add Prometheus metrics for backups
- Update Grafana dashboard
- Configure alerts for failures

**Phase 1.3.8: Documentation & Deployment (Week 8)**
- Update README with archiving procedures
- Create runbook for operations
- Deploy to production
- Monitor for one week
- Final adjustments

### 8.2 Testing Strategy

**Unit Tests:**
```python
# tests/test_archive_service.py
def test_archive_story_creates_archived_record():
    """Test archiving creates ArchivedStory with correct data."""
    pass

def test_archive_story_copies_media_files():
    """Test media files are copied to archive directory."""
    pass

def test_restore_story_recreates_story():
    """Test restored story matches original."""
    pass

def test_archive_prevents_duplicate():
    """Test cannot archive already archived story."""
    pass

def test_search_archived_stories():
    """Test search finds correct archived stories."""
    pass
```

**Integration Tests:**
```python
# tests/integration/test_archiving_workflow.py
def test_complete_archive_restore_cycle():
    """Test archiving and restoring a story preserves all data."""
    # 1. Create and complete a story
    # 2. Archive the story
    # 3. Verify archived record
    # 4. Restore the story
    # 5. Verify restored story matches original
    pass

def test_media_cleanup_after_retention():
    """Test media files are deleted after retention period."""
    pass
```

**Load Tests:**
```python
# tests/load/test_archive_performance.py
def test_archive_1000_stories():
    """Test archiving 1000 stories completes in reasonable time."""
    pass

def test_search_archived_stories_performance():
    """Test searching 10,000 archived stories is fast."""
    pass
```

### 8.3 Rollback Plan

**If Issues Arise:**

1. **Disable Automated Jobs**
   ```bash
   # Comment out cron jobs
   sudo vim /etc/cron.d/ephergent-archiving
   # Add # before each job
   ```

2. **Revert Migration (if necessary)**
   ```bash
   cd /path/to/ephergent_season_03_generator
   source .venv/bin/activate
   flask db downgrade  # Reverts one migration
   ```

3. **Restore from Backup**
   ```bash
   # Restore database from pre-Phase-1.3 backup
   python -m ephergent_generator.scripts.restore_database --backup-id XXXX
   ```

4. **Preserve Existing Archives**
   - Even if rolling back code, keep `archives/` directory
   - Archived stories can be restored manually if needed

---

## 9. Risk Assessment

### 9.1 Identified Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Data Loss During Archive** | Critical | Low | Transaction-based archiving, validate before deletion |
| **Corrupted Backup Files** | High | Medium | Verify after creation, test restore weekly |
| **Archive Table Growth** | Medium | High | Monitor size, implement compression, plan S3 migration |
| **Media Cleanup Deletes Wrong Files** | High | Low | Require archive first, audit all deletions, dry-run mode |
| **Restore Overwrites Active Story** | High | Low | Check for conflicts, require explicit confirmation |
| **Backup Fails Silently** | High | Medium | Prometheus alerts, daily health checks |
| **Disk Space Exhaustion** | Critical | Medium | Storage alerts, auto-cleanup threshold |
| **Performance Degradation** | Medium | Low | Batch operations, off-peak scheduling |
| **Migration Fails** | High | Low | Test on development first, maintain backups |

### 9.2 Mitigation Strategies

**Data Integrity:**
- All archiving wrapped in database transactions
- Validate data before deletion
- Create checksums for archives
- Periodic integrity sweeps

**Backup Reliability:**
- Automated verification after creation
- Weekly restore testing
- Prometheus metrics for monitoring
- Alerts for failed backups

**Performance:**
- Batch operations (limit 50-100 per run)
- Run during off-peak hours (2-4 AM)
- Index optimization for archive queries
- Monitor query performance

**Operational Safety:**
- Dry-run mode for all destructive operations
- Audit logging for all operations
- Admin confirmation for manual operations
- Rollback capability

---

## 10. Monitoring & Alerting

### 10.1 Prometheus Metrics

**New Metrics for Phase 1.3:**

```python
# File: ephergent_generator/utils/metrics.py
# Add to existing MetricsService class

class MetricsService:
    def __init__(self):
        # ... existing metrics ...

        # ========== ARCHIVING METRICS ==========
        self.stories_archived_total = Counter(
            'ephergent_stories_archived_total',
            'Total number of stories archived',
            ['reason']  # age_threshold, manual, storage_cleanup
        )

        self.archive_operations_duration_seconds = Histogram(
            'ephergent_archive_operation_duration_seconds',
            'Time spent archiving stories',
            ['operation']  # archive, restore, compress
        )

        self.archive_size_bytes = Gauge(
            'ephergent_archive_size_bytes',
            'Total size of archived stories'
        )

        self.archive_count = Gauge(
            'ephergent_archive_count',
            'Number of archived stories'
        )

        # ========== STORAGE METRICS ==========
        self.storage_usage_bytes = Gauge(
            'ephergent_storage_usage_bytes',
            'Storage usage by type',
            ['media_type']  # images, audio, video, archives
        )

        self.media_cleanup_files_deleted = Counter(
            'ephergent_media_cleanup_files_deleted_total',
            'Total files deleted by cleanup',
            ['media_type']
        )

        self.media_cleanup_bytes_freed = Counter(
            'ephergent_media_cleanup_bytes_freed_total',
            'Total bytes freed by cleanup',
            ['media_type']
        )

        # ========== BACKUP METRICS ==========
        self.backup_operations_total = Counter(
            'ephergent_backup_operations_total',
            'Total backup operations',
            ['type', 'status']  # type: full/incremental, status: success/failed
        )

        self.backup_duration_seconds = Histogram(
            'ephergent_backup_duration_seconds',
            'Backup operation duration',
            ['type']
        )

        self.backup_size_bytes = Gauge(
            'ephergent_backup_size_bytes',
            'Size of latest backup',
            ['type']
        )

        self.last_successful_backup_timestamp = Gauge(
            'ephergent_last_successful_backup_timestamp',
            'Unix timestamp of last successful backup'
        )

        self.backup_verification_failures = Counter(
            'ephergent_backup_verification_failures_total',
            'Total backup verification failures'
        )

    # ========== METRIC RECORDING METHODS ==========

    def record_archive_operation(self, operation: str, duration: float,
                                 reason: str = 'age_threshold'):
        """Record archiving operation metrics."""
        self.stories_archived_total.labels(reason=reason).inc()
        self.archive_operations_duration_seconds.labels(operation=operation).observe(duration)

    def update_storage_metrics(self, storage_usage: Dict[str, int]):
        """Update storage usage metrics."""
        for media_type, bytes_used in storage_usage.items():
            self.storage_usage_bytes.labels(media_type=media_type).set(bytes_used)

    def record_backup(self, backup_type: str, status: str,
                     duration: float, size_bytes: int):
        """Record backup operation metrics."""
        self.backup_operations_total.labels(type=backup_type, status=status).inc()
        self.backup_duration_seconds.labels(type=backup_type).observe(duration)

        if status == 'success':
            self.backup_size_bytes.labels(type=backup_type).set(size_bytes)
            self.last_successful_backup_timestamp.set(time.time())
```

### 10.2 Grafana Dashboard Updates

**New Dashboard Panels:**

1. **Archive Statistics Panel**
   ```promql
   # Total archived stories
   ephergent_archive_count

   # Archive growth rate (stories/day)
   rate(ephergent_stories_archived_total[24h]) * 86400

   # Archive size
   ephergent_archive_size_bytes / (1024^3)  # GB
   ```

2. **Storage Usage Panel**
   ```promql
   # Storage by media type
   ephergent_storage_usage_bytes / (1024^3)  # GB

   # Cleanup rate
   rate(ephergent_media_cleanup_files_deleted_total[24h]) * 86400

   # Space freed by cleanup
   rate(ephergent_media_cleanup_bytes_freed_total[24h]) * 86400 / (1024^3)
   ```

3. **Backup Health Panel**
   ```promql
   # Time since last successful backup
   (time() - ephergent_last_successful_backup_timestamp) / 3600  # hours

   # Backup success rate
   rate(ephergent_backup_operations_total{status="success"}[7d]) /
   rate(ephergent_backup_operations_total[7d]) * 100

   # Latest backup size
   ephergent_backup_size_bytes{type="full"} / (1024^2)  # MB
   ```

### 10.3 Alert Rules

**File:** `monitoring/alerts/phase_1_3_alerts.yml` (for Prometheus AlertManager)

```yaml
groups:
- name: ephergent_phase_1_3_alerts
  interval: 1m
  rules:

  # ========== ARCHIVING ALERTS ==========
  - alert: ArchivingFailed
    expr: |
      increase(ephergent_archive_operations_duration_seconds_count{operation="archive"}[1h]) == 0
      and hour() == 2  # Should run at 2 AM
    for: 30m
    labels:
      severity: warning
      component: archiving
    annotations:
      summary: "Archiving job may have failed"
      description: "No archiving operations detected in the last hour during scheduled time"

  # ========== STORAGE ALERTS ==========
  - alert: StorageWarning
    expr: ephergent_storage_usage_bytes / (1024^3) > 100
    for: 5m
    labels:
      severity: warning
      component: storage
    annotations:
      summary: "Storage usage exceeds warning threshold"
      description: "Storage usage: {{ $value | humanize }}GB (threshold: 100GB)"

  - alert: StorageCritical
    expr: ephergent_storage_usage_bytes / (1024^3) > 150
    for: 5m
    labels:
      severity: critical
      component: storage
    annotations:
      summary: "CRITICAL: Storage usage exceeds critical threshold"
      description: "Storage usage: {{ $value | humanize }}GB (threshold: 150GB). Immediate cleanup required."

  # ========== BACKUP ALERTS ==========
  - alert: BackupFailed
    expr: |
      increase(ephergent_backup_operations_total{status="failed"}[24h]) > 0
    for: 5m
    labels:
      severity: critical
      component: backup
    annotations:
      summary: "Database backup failed"
      description: "{{ $value }} backup failures in last 24 hours"

  - alert: BackupStale
    expr: (time() - ephergent_last_successful_backup_timestamp) / 3600 > 26
    for: 10m
    labels:
      severity: critical
      component: backup
    annotations:
      summary: "No successful backup in 26+ hours"
      description: "Last successful backup: {{ $value | humanizeDuration }} ago"

  - alert: BackupVerificationFailed
    expr: increase(ephergent_backup_verification_failures_total[24h]) > 0
    for: 5m
    labels:
      severity: warning
      component: backup
    annotations:
      summary: "Backup verification failed"
      description: "{{ $value }} backup verification failures in last 24 hours"
```

### 10.4 Health Check Endpoints

**Add to:** `ephergent_generator/blueprints/api/health.py`

```python
@health_bp.route('/health/archiving', methods=['GET'])
def archiving_health():
    """
    Check archiving system health.

    Returns:
        {
            'healthy': bool,
            'last_archive': datetime,
            'archives_today': int,
            'storage_usage_gb': float,
            'issues': List[str]
        }
    """
    pass

@health_bp.route('/health/backups', methods=['GET'])
def backup_health():
    """
    Check backup system health.

    Returns:
        {
            'healthy': bool,
            'last_backup': datetime,
            'last_successful_backup': datetime,
            'backup_age_hours': float,
            'verification_status': str,
            'issues': List[str]
        }
    """
    pass
```

---

## Conclusion

This architecture provides a comprehensive, production-ready solution for Phase 1.3: Database Optimization. The design prioritizes **data safety**, **operational maintainability**, and **monitoring** while integrating seamlessly with the existing Ephergent story generation infrastructure.

**Key Achievements:**

✓ **Dual-table archiving** prevents active table bloat
✓ **Configurable retention policies** via SystemConfig
✓ **Automated backups** with verification
✓ **Complete audit trail** for all operations
✓ **Prometheus/Grafana integration** for monitoring
✓ **Safe restoration procedures** with rollback
✓ **Storage optimization** without data loss
✓ **Production-ready** with comprehensive error handling

**Next Steps:**

1. Review and approve this architecture
2. Begin implementation starting with Phase 1.3.1 (Database Schema)
3. Iterate through implementation phases with testing
4. Deploy to production with monitoring
5. Plan Phase 2.0 enhancements (S3 integration, encryption)

---

**Document Approval:**

- [ ] Technical Lead Review
- [ ] Security Review
- [ ] Operations Review
- [ ] Final Approval

**Revision History:**
- 2025-10-10: Initial architecture design (v1.0)
