# Phase 1 Architecture - Visual Diagrams

**Reference:** Visual diagrams for the Phase 1 Production Readiness & Stability architecture

---

## Diagram 1: System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL CLIENTS                                 │
│                                                                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐ │
│  │ Web Browser │  │ Claude Code  │  │ Mobile App  │  │ External APIs  │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘  └────────┬───────┘ │
│         │                │                  │                   │         │
└─────────┼────────────────┼──────────────────┼───────────────────┼─────────┘
          │                │                  │                   │
          │                │                  │                   │
┌─────────▼────────────────▼──────────────────▼───────────────────▼─────────┐
│                         NGINX REVERSE PROXY                                │
│                                                                            │
│  • SSL/TLS Termination                                                    │
│  • Rate Limiting (IP-based)                                               │
│  • Static File Caching                                                    │
│  • Health Check Routing                                                   │
│  • Metrics Endpoint Access Control                                        │
│                                                                            │
│  Port 80/443 → 127.0.0.1:5000                                            │
└─────────┬──────────────────────────────────────────────────────────────────┘
          │
          ├─────────────────┬─────────────────┬────────────────┐
          │                 │                 │                │
┌─────────▼─────────┐ ┌─────▼──────────┐ ┌──▼──────────┐ ┌──▼─────────┐
│  Flask Web App    │ │ Background     │ │ MCP Server  │ │ Prometheus │
│  (Gunicorn)       │ │ Worker         │ │ (Async)     │ │ (Scraper)  │
│                   │ │                │ │             │ │            │
│ Port: 5000        │ │ Continuous     │ │ Port: 8000  │ │ Port: 9090 │
│ Workers: 4        │ │ Processing     │ │             │ │            │
│                   │ │                │ │             │ │            │
│ Endpoints:        │ │ Components:    │ │ Tools:      │ │ Scrapes:   │
│ • /api/stories    │ │ • Queue Poller │ │ • create_   │ │ • /metrics │
│ • /api/health     │ │ • Workflow Svc │ │   story     │ │   (10s int)│
│ • /metrics        │ │ • Retry Logic  │ │ • get_story │ │ • Stores:  │
│ • /admin          │ │ • Service Mgmt │ │ • list_     │ │   Time-    │
│                   │ │                │ │   stories   │ │   series DB│
│ Libraries:        │ │ Libraries:     │ │             │ │            │
│ • Flask           │ │ • Workflow Svc │ │ Libraries:  │ │ Alerts:    │
│ • SQLAlchemy      │ │ • Gemini API   │ │ • MCP SDK   │ │ • DLQ size │
│ • Prometheus      │ │ • ComfyUI      │ │ • HTTPx     │ │ • Workers  │
│   Client          │ │ • Kokoro TTS   │ │             │ │   down     │
│ • JSON Logger     │ │ • YouTube API  │ │             │ │ • High     │
│                   │ │                │ │             │ │   error    │
└─────────┬─────────┘ └─────┬──────────┘ └──┬──────────┘ └──┬─────────┘
          │                 │                │               │
          │                 │                │               │
          └─────────────────┴────────────────┴───────────────┘
                            │
                            │
          ┌─────────────────┴────────────────────────┐
          │                                          │
┌─────────▼─────────┐              ┌────────────────▼──────────┐
│  PostgreSQL DB    │              │  Redis Cache (Optional)    │
│                   │              │                            │
│ Database:         │              │ Use Cases:                 │
│ • ephergent_prod  │              │ • Worker Locks             │
│                   │              │ • Rate Limiting            │
│ Tables:           │              │ • Metrics Cache            │
│ • stories         │              │ • Session Storage          │
│ • story_queue     │              │                            │
│ • story_retries   │              │ Port: 6379                 │
│ • archived_stories│              │ Persistence: Append-only   │
│ • users           │              │                            │
│ • characters      │              │ Memory: ~100MB             │
│ • system_config   │              │                            │
│                   │              │                            │
│ Port: 5432        │              └────────────────────────────┘
│ Connection Pool:  │
│ • Size: 10        │
│ • Max Overflow: 20│
│ • Pre-ping: Yes   │
│                   │
│ Optimizations:    │
│ • Indexes on      │
│   workflow_step   │
│ • Indexes on      │
│   created_at      │
│ • Archiving job   │
│   (90 days)       │
└─────────┬─────────┘
          │
          │
┌─────────▼─────────┐
│  Grafana UI       │
│                   │
│ Port: 3000        │
│                   │
│ Dashboards:       │
│ • System Overview │
│ • Workflow Perf   │
│ • Error Tracking  │
│ • DLQ Monitor     │
│                   │
│ Data Source:      │
│ • Prometheus      │
│                   │
│ Auth:             │
│ • admin/admin     │
│   (change in prod)│
└───────────────────┘
```

---

## Diagram 2: Story Processing Workflow with Observability

```
┌───────────────────────────────────────────────────────────────────────┐
│                         STORY CREATION                                 │
└───────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  User submits topic  │
                     │  via API/Web/MCP     │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  Create Story record │
                     │  current_step=QUEUED │
                     └──────────┬───────────┘
                                │
                     ┌──────────┴───────────┐
                     │                      │
                     ▼                      ▼
          ┌─────────────────────┐  ┌──────────────────┐
          │ Log: Story created  │  │ Metric:          │
          │ story_id=42         │  │ stories_created  │
          │ topic="..."         │  │ _total++         │
          └─────────────────────┘  └──────────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  Add to StoryQueue   │
                     │  priority=0          │
                     └──────────┬───────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│                      BACKGROUND WORKER LOOP                            │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  Poll queue for next │
                     │  story               │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  Acquire worker lock │
                     │  worker_id=worker123 │
                     └──────────┬───────────┘
                                │
                                ▼
              ┌─────────────────────────────────────┐
              │  Determine current workflow step:   │
              │  • QUEUED                           │
              │  • STORY_GENERATION                 │
              │  • TITLE_GENERATION                 │
              │  • IMAGE_GENERATION                 │
              │  • AUDIO_GENERATION                 │
              │  • VIDEO_GENERATION                 │
              │  • YOUTUBE_UPLOAD                   │
              │  • GHOST_PUBLISHING                 │
              │  • COMPLETED                        │
              └─────────────────┬───────────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  Start timer         │
                     │  start_time = now()  │
                     └──────────┬───────────┘
                                │
                                ▼
              ┌─────────────────────────────────────┐
              │  Execute workflow step              │
              │  (e.g., call Gemini API)            │
              └─────────────────┬───────────────────┘
                                │
                     ┌──────────┴──────────┐
                     │                     │
                     ▼                     ▼
          ┌─────────────────┐   ┌─────────────────────┐
          │    SUCCESS      │   │     FAILURE         │
          └────────┬────────┘   └──────────┬──────────┘
                   │                       │
                   ▼                       ▼
    ┌──────────────────────┐   ┌────────────────────────┐
    │ Calculate duration   │   │ Classify error type:   │
    │ duration_ms = ...    │   │ • Network timeout      │
    └──────────┬───────────┘   │ • Rate limit           │
               │               │ • Validation error     │
               │               │ • API error            │
               │               └────────────┬───────────┘
               │                            │
               │                ┌───────────┴──────────┐
               │                │                      │
               │                ▼                      ▼
               │     ┌──────────────────┐  ┌──────────────────┐
               │     │  RETRYABLE       │  │  NON-RETRYABLE   │
               │     │  (timeout, rate  │  │  (validation,    │
               │     │   limit)         │  │   auth error)    │
               │     └────────┬─────────┘  └────────┬─────────┘
               │              │                     │
               │              ▼                     │
               │   ┌─────────────────────┐         │
               │   │ Check retry count:  │         │
               │   │ • count < 3?        │         │
               │   └─────────┬───────────┘         │
               │             │                     │
               │  ┌──────────┴──────────┐          │
               │  │                     │          │
               │  ▼                     ▼          │
               │ YES                   NO          │
               │  │                     │          │
               │  ▼                     │          │
               │ ┌──────────────────┐  │          │
               │ │ Increment retry  │  │          │
               │ │ Calculate backoff│  │          │
               │ │ 2^retry + jitter │  │          │
               │ │                  │  │          │
               │ │ Log: WARN        │  │          │
               │ │ Metric: retry++  │  │          │
               │ └────────┬─────────┘  │          │
               │          │             │          │
               │          ▼             │          │
               │ ┌──────────────────┐  │          │
               │ │ Release to queue │  │          │
               │ │ for retry        │  │          │
               │ └────────┬─────────┘  │          │
               │          │             │          │
               │          │             ▼          ▼
               │          │        ┌───────────────────────┐
               │          │        │ Move to Dead Letter   │
               │          │        │ Queue (DLQ)           │
               │          │        │                       │
               │          │        │ Log: ERROR            │
               │          │        │ Metric: dlq_total++   │
               │          │        │ Alert: DLQ size > 25  │
               │          │        └───────────────────────┘
               │          │
               │          │
               ▼          ▼
    ┌──────────────────────────────┐
    │  Update Story record         │
    │  • Advance to next step      │
    │  • Update workflow_data      │
    │  • Update timestamps         │
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  Log workflow step result:   │
    │  • story_id                  │
    │  • workflow_step             │
    │  • status (success/failure)  │
    │  • duration_ms               │
    │  • error_message (if failed) │
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  Record Prometheus metrics:  │
    │  • workflow_step_duration_   │
    │    seconds (histogram)       │
    │  • stories_completed_total   │
    │    (counter, if complete)    │
    │  • stories_failed_total      │
    │    (counter, if failed)      │
    └──────────┬───────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │  Is story completed?         │
    └──────────┬───────────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
     ▼                   ▼
    YES                 NO
     │                   │
     ▼                   ▼
┌────────────────┐  ┌──────────────────┐
│ Remove from    │  │ Release to queue │
│ queue          │  │ for next step    │
│                │  │                  │
│ Log: COMPLETED │  │ Log: NEXT_STEP   │
└────────────────┘  └──────────────────┘
     │                   │
     │                   │
     └───────────────────┘
             │
             ▼
┌────────────────────────────┐
│  Worker loop continues     │
│  (sleep 5s between polls)  │
└────────────────────────────┘
```

---

## Diagram 3: Monitoring & Alerting Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐     │
│  │ Flask Web    │  │ Background   │  │ MCP Server      │     │
│  │ App          │  │ Worker       │  │                 │     │
│  │              │  │              │  │                 │     │
│  │ Exposes:     │  │ Exposes:     │  │ Exposes:        │     │
│  │ /metrics     │  │ /metrics     │  │ /metrics        │     │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘     │
│         │                 │                    │              │
│         └─────────────────┴────────────────────┘              │
│                           │                                   │
└───────────────────────────┼───────────────────────────────────┘
                            │
                            │ Scrape every 10 seconds
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    PROMETHEUS SERVER                            │
│                                                                 │
│  Port: 9090                                                     │
│                                                                 │
│  Scrape Targets:                                                │
│  • ephergent-web:5000/metrics                                  │
│  • node-exporter:9100/metrics (system metrics)                 │
│  • postgres-exporter:9187/metrics (future)                     │
│                                                                 │
│  Stores:                                                        │
│  • Time-series data (15 day retention)                         │
│  • ~1GB storage per month                                      │
│                                                                 │
│  Evaluates:                                                     │
│  • Alert rules (every 30 seconds)                              │
│  • Recording rules (pre-computed queries)                      │
│                                                                 │
│  Provides:                                                      │
│  • PromQL query API                                            │
│  • Target health monitoring                                    │
│  • Alert state tracking                                        │
└────────────────┬───────────────────────┬───────────────────────┘
                 │                       │
                 │ Alerts fire           │ Query API
                 │                       │
                 ▼                       ▼
┌────────────────────────────┐  ┌────────────────────────────┐
│  ALERTMANAGER              │  │  GRAFANA                    │
│                            │  │                             │
│  Port: 9093                │  │  Port: 3000                 │
│                            │  │                             │
│  Receives alerts from:     │  │  Data Source:               │
│  • Prometheus              │  │  • Prometheus (query API)   │
│                            │  │                             │
│  Alert Types:              │  │  Dashboards:                │
│  • DLQ size > 25           │  │  1. System Overview         │
│  • No active workers       │  │     • Story processing rate │
│  • High error rate         │  │     • Success rate          │
│  • Database latency high   │  │     • Queue depth           │
│  • Connection pool         │  │     • Active workers        │
│    exhausted               │  │                             │
│                            │  │  2. Workflow Performance    │
│  Notification Channels:    │  │     • P95 latency by step   │
│  • Email                   │  │     • Success rate by step  │
│  • Slack (webhook)         │  │     • Retry rate            │
│  • PagerDuty (optional)    │  │                             │
│                            │  │  3. Error Tracking          │
│  Alert Grouping:           │  │     • Error rate            │
│  • By severity             │  │     • Error breakdown       │
│  • By service              │  │     • External API errors   │
│  • Throttling (5min)       │  │     • DLQ entries           │
│                            │  │                             │
│  Alert States:             │  │  4. DLQ Monitor             │
│  • Pending                 │  │     • DLQ size over time    │
│  • Firing                  │  │     • Stories by error type │
│  • Resolved                │  │     • Recent DLQ entries    │
└────────────────┬───────────┘  └────────────────┬───────────────┘
                 │                               │
                 ▼                               ▼
┌────────────────────────────┐  ┌────────────────────────────┐
│  NOTIFICATION RECIPIENTS   │  │  OPERATIONS TEAM           │
│                            │  │                             │
│  • DevOps team email       │  │  • View dashboards         │
│  • #ephergent-alerts Slack │  │  • Investigate alerts      │
│  • On-call engineer        │  │  • Query metrics           │
│    (PagerDuty)             │  │  • Export data             │
└────────────────────────────┘  └────────────────────────────┘
```

---

## Diagram 4: Database Schema - Phase 1 Additions

```
┌────────────────────────────────────────────────────────────────────┐
│                      EXISTING TABLES                                │
└────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  stories                                                      │
├──────────────────────────────────────────────────────────────┤
│  id (PK)                            INTEGER                  │
│  topic                              TEXT                     │
│  title                              VARCHAR(200)             │
│  content                            TEXT                     │
│  current_step (NEW INDEX)           ENUM(WorkflowStep)       │
│  workflow_data                      JSON                     │
│  error_message                      TEXT                     │
│  created_at                         DATETIME                 │
│  updated_at (NEW INDEX)             DATETIME                 │
│  completed_at (NEW INDEX)           DATETIME                 │
│  session_id                         VARCHAR(100)             │
│  narrator_character_id              VARCHAR(100)             │
│  image_paths                        JSON                     │
│  audio_path                         VARCHAR(500)             │
│  video_path                         VARCHAR(500)             │
│  youtube_video_id                   VARCHAR(100)             │
│  ghost_post_id                      VARCHAR(100)             │
└──────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  story_queue                                                  │
├──────────────────────────────────────────────────────────────┤
│  id (PK)                            INTEGER                  │
│  story_id (FK → stories.id)         INTEGER                  │
│  priority                           INTEGER                  │
│  created_at                         DATETIME                 │
│  processing_started_at              DATETIME                 │
│  worker_id                          VARCHAR(100)             │
└──────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      NEW TABLES (PHASE 1)                           │
└────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  story_retries (NEW)                                          │
├──────────────────────────────────────────────────────────────┤
│  id (PK)                            INTEGER                  │
│  story_id (FK → stories.id)         INTEGER                  │
│  workflow_step                      VARCHAR(50)              │
│  retry_count                        INTEGER (default: 0)     │
│  max_retries                        INTEGER (default: 3)     │
│  last_error                         TEXT                     │
│  last_retry_at                      DATETIME                 │
│  retry_status                       VARCHAR(20)              │
│    (pending, retrying, success, dead_letter)                 │
│  error_type                         VARCHAR(50)              │
│    (network, timeout, api_error, rate_limit, validation)     │
│  is_retryable                       BOOLEAN (default: true)  │
│  created_at                         DATETIME                 │
│  updated_at                         DATETIME                 │
│  dead_lettered_at                   DATETIME                 │
│                                                               │
│  INDEX: idx_retry_story_step (story_id, workflow_step)       │
│  INDEX: idx_retry_status (retry_status)                      │
└──────────────────────────────────────────────────────────────┘
         │
         │ Relationship: story_retries.story_id → stories.id
         │

┌──────────────────────────────────────────────────────────────┐
│  archived_stories (NEW)                                       │
├──────────────────────────────────────────────────────────────┤
│  id (PK)                            INTEGER                  │
│  original_story_id                  INTEGER                  │
│  story_data                         TEXT (JSON)              │
│  archived_at                        DATETIME                 │
│  archived_by (FK → users.id)        INTEGER                  │
│  archive_reason                     VARCHAR(100)             │
│  story_created_at                   DATETIME                 │
│  story_completed_at                 DATETIME                 │
│  delete_after                       DATETIME                 │
│                                                               │
│  INDEX: idx_archived_original_id (original_story_id)         │
│  INDEX: idx_archived_date (archived_at)                      │
└──────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                     PERFORMANCE INDEXES ADDED                       │
└────────────────────────────────────────────────────────────────────┘

stories:
  • idx_story_step_updated (current_step, updated_at)
    - Speeds up queries for stories by workflow step
  • idx_story_completed (completed_at)
    - Speeds up archiving queries for old completed stories

story_queue:
  • Existing indexes sufficient

story_retries:
  • idx_retry_story_step (story_id, workflow_step)
    - Speeds up retry lookup for specific story and step
  • idx_retry_status (retry_status)
    - Speeds up DLQ queries

archived_stories:
  • idx_archived_original_id (original_story_id)
    - Speeds up lookup of archived stories by original ID
  • idx_archived_date (archived_at)
    - Speeds up queries for archiving reports and cleanup
```

---

## Diagram 5: Retry Logic Decision Tree

```
                    ┌───────────────────────┐
                    │  Workflow Step Fails  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Classify Error Type  │
                    └───────────┬───────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
     ┌──────────────┐  ┌───────────────┐  ┌─────────────┐
     │  NETWORK     │  │  VALIDATION   │  │  RATE_LIMIT │
     │  TIMEOUT     │  │  ERROR        │  │  API_ERROR  │
     └──────┬───────┘  └───────┬───────┘  └──────┬──────┘
            │                  │                  │
            │                  │                  │
            ▼                  ▼                  ▼
     ┌──────────────┐  ┌───────────────┐  ┌─────────────┐
     │  RETRYABLE   │  │ NON-RETRYABLE │  │  RETRYABLE  │
     └──────┬───────┘  └───────┬───────┘  └──────┬──────┘
            │                  │                  │
            └──────────────────┴──────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
      ┌──────────────────┐          ┌─────────────────┐
      │  Is Retryable?   │          │  Not Retryable  │
      │  YES             │          │  (validation,   │
      └────────┬─────────┘          │   auth error)   │
               │                    └────────┬────────┘
               ▼                             │
      ┌──────────────────┐                  │
      │  Check retry     │                  │
      │  count           │                  │
      └────────┬─────────┘                  │
               │                             │
     ┌─────────┴─────────┐                  │
     │                   │                  │
     ▼                   ▼                  │
  retry_count < 3?   retry_count >= 3      │
     YES                NO                  │
     │                   │                  │
     │                   ▼                  ▼
     │          ┌─────────────────────────────────┐
     │          │  Move to Dead Letter Queue      │
     │          │                                  │
     │          │  • retry_status = 'dead_letter' │
     │          │  • dead_lettered_at = now()     │
     │          │  • Log ERROR                    │
     │          │  • Metric: dlq_total++          │
     │          │  • Alert if DLQ size > 25       │
     │          └─────────────────────────────────┘
     │                                       │
     │                                       │
     ▼                                       ▼
┌─────────────────────────────────┐  ┌──────────────────┐
│  Calculate Exponential Backoff  │  │  Manual          │
│                                  │  │  Intervention    │
│  delay = 2^retry_count + jitter │  │  Required        │
│                                  │  │                  │
│  Example:                        │  │  Options:        │
│  • Retry 1: 1s + (0-0.5s)       │  │  • Inspect error │
│  • Retry 2: 2s + (0-1s)         │  │  • Fix issue     │
│  • Retry 3: 4s + (0-2s)         │  │  • Re-queue      │
└────────────┬────────────────────┘  │  • Discard       │
             │                       └──────────────────┘
             ▼
┌─────────────────────────────────┐
│  Increment Retry Count          │
│                                  │
│  • retry_count++                │
│  • retry_status = 'retrying'    │
│  • last_retry_at = now()        │
│  • last_error = error_msg       │
│  • Log WARN                     │
│  • Metric: retry_total++        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Release Story to Queue         │
│                                  │
│  • Story will be picked up      │
│    again after backoff delay    │
│  • Worker ID cleared             │
│  • processing_started_at = NULL │
└────────────┬────────────────────┘
             │
             ▼
     ┌───────────────┐
     │  Worker Loop  │
     │  Continues    │
     └───────────────┘
```

---

## Diagram 6: Deployment Architecture (Debian VM)

```
┌────────────────────────────────────────────────────────────────────┐
│                     DEBIAN VM (10.0.0.99)                           │
│                                                                     │
│  OS: Debian 12 (Bookworm)                                          │
│  RAM: 8GB                                                           │
│  Disk: 100GB                                                        │
│  CPU: 4 cores                                                       │
│                                                                     │
├────────────────────────────────────────────────────────────────────┤
│                     SYSTEM SERVICES                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  NGINX (Port 80/443)                                      │     │
│  │  systemd: nginx.service                                   │     │
│  │  Config: /etc/nginx/sites-available/ephergent             │     │
│  │  Logs: /var/log/nginx/                                    │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Ephergent Web (Port 5000)                                │     │
│  │  systemd: ephergent-web.service                           │     │
│  │  Command: gunicorn --bind 127.0.0.1:5000 wsgi:app         │     │
│  │  Workers: 4                                                │     │
│  │  User: www-data                                            │     │
│  │  WorkingDirectory: /opt/ephergent                          │     │
│  │  Environment: /opt/ephergent/.env                          │     │
│  │  Logs: /var/log/ephergent/web.log                         │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Ephergent Worker                                          │     │
│  │  systemd: ephergent-worker.service                         │     │
│  │  Command: python worker.py --continuous                    │     │
│  │  User: www-data                                            │     │
│  │  WorkingDirectory: /opt/ephergent                          │     │
│  │  Environment: /opt/ephergent/.env                          │     │
│  │  Logs: /var/log/ephergent/worker.log                      │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  PostgreSQL (Port 5432)                                    │     │
│  │  systemd: postgresql.service                               │     │
│  │  Data: /var/lib/postgresql/15/main                         │     │
│  │  Config: /etc/postgresql/15/main/postgresql.conf           │     │
│  │  Logs: /var/log/postgresql/                                │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Prometheus (Port 9090)                      [PHASE 1]     │     │
│  │  systemd: prometheus.service                               │     │
│  │  Config: /etc/prometheus/prometheus.yml                    │     │
│  │  Rules: /etc/prometheus/rules/ephergent_alerts.yml         │     │
│  │  Data: /var/lib/prometheus/                                │     │
│  │  Retention: 15 days                                        │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Grafana (Port 3000)                         [PHASE 1]     │     │
│  │  systemd: grafana-server.service                           │     │
│  │  Config: /etc/grafana/grafana.ini                          │     │
│  │  Data: /var/lib/grafana/                                   │     │
│  │  Dashboards: /var/lib/grafana/dashboards/                  │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Redis (Port 6379)                           [Optional]    │     │
│  │  systemd: redis-server.service                             │     │
│  │  Config: /etc/redis/redis.conf                             │     │
│  │  Data: /var/lib/redis/                                     │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
├────────────────────────────────────────────────────────────────────┤
│                     FILE SYSTEM LAYOUT                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  /opt/ephergent/                    (Application root)             │
│  ├── .venv/                         (Python virtual env)           │
│  ├── ephergent_generator/           (Python package)               │
│  │   ├── api/                       (Flask blueprints)             │
│  │   ├── services/                  (Business logic)               │
│  │   ├── utils/                     (Logging, metrics)  [PHASE 1] │
│  │   └── models.py                  (Database models)              │
│  ├── migrations/                    (Alembic migrations)           │
│  ├── static/                        (Generated media)              │
│  ├── worker.py                      (Background worker)            │
│  ├── wsgi.py                        (Web app entry point)          │
│  ├── config.py                      (Configuration)                │
│  ├── .env                           (Environment variables)        │
│  └── pyproject.toml                 (Dependencies)                 │
│                                                                     │
│  /var/log/ephergent/                (Application logs)  [PHASE 1] │
│  ├── web.log                        (Flask app logs - JSON)        │
│  ├── worker.log                     (Worker logs - JSON)           │
│  ├── access.log                     (HTTP access logs)             │
│  └── error.log                      (HTTP error logs)              │
│                                                                     │
│  /var/lib/prometheus/               (Prometheus data)   [PHASE 1] │
│  └── metrics2/                      (Time-series database)         │
│                                                                     │
│  /var/lib/grafana/                  (Grafana data)      [PHASE 1] │
│  ├── dashboards/                    (Dashboard JSON files)         │
│  └── grafana.db                     (Grafana SQLite DB)            │
│                                                                     │
│  /var/backups/                      (Database backups)             │
│  └── ephergent_YYYYMMDD.sql         (PostgreSQL dumps)            │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

**Document End**

These diagrams provide visual references for:
1. Overall system architecture
2. Story processing workflow with observability
3. Monitoring and alerting flow
4. Database schema additions
5. Retry logic decision tree
6. Deployment architecture on Debian VM

Refer to `PHASE_1_ARCHITECTURE.md` for detailed implementation instructions.
