# Metrics Guide - Ephergent Story Generator

This guide provides comprehensive documentation for the Prometheus metrics exposed by the Ephergent story generation system.

## Table of Contents

1. [Overview](#overview)
2. [Accessing Metrics](#accessing-metrics)
3. [Workflow-Specific Metrics](#workflow-specific-metrics)
4. [Business Metrics](#business-metrics)
5. [Media Generation Metrics](#media-generation-metrics)
6. [External Service Metrics](#external-service-metrics)
7. [Infrastructure Metrics](#infrastructure-metrics)
8. [Example Prometheus Queries](#example-prometheus-queries)
9. [Grafana Dashboard Examples](#grafana-dashboard-examples)

## Overview

The metrics system uses Prometheus client library to expose metrics in a format compatible with Prometheus scraping. All metrics are automatically updated when the `/metrics` endpoint is accessed, ensuring real-time accuracy.

**Key Features:**
- Database-driven workflow metrics (real-time state from database)
- Event-driven counters and histograms (tracked as events occur)
- Automatic HTTP request tracking
- External service health monitoring
- Worker process tracking

## Accessing Metrics

### Endpoint
```
GET http://localhost:5000/metrics
```

### Response Format
Metrics are returned in Prometheus exposition format:

```
# HELP ephergent_stories_by_status Total number of stories by workflow status
# TYPE ephergent_stories_by_status gauge
ephergent_stories_by_status{status="completed"} 42.0
ephergent_stories_by_status{status="failed"} 3.0
ephergent_stories_by_status{status="queued"} 5.0
```

### Prometheus Scrape Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'ephergent_generator'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Workflow-Specific Metrics

These metrics are **database-driven** and reflect the current state of stories in the system. They are updated each time the `/metrics` endpoint is scraped.

### `ephergent_stories_by_status`
**Type:** Gauge
**Labels:** `status` (workflow step name)
**Description:** Total number of stories currently at each workflow status.

**Values:**
- `queued` - Stories waiting to start processing
- `story_generation` - Stories generating content
- `title_generation` - Stories generating titles
- `image_generation` - Stories generating images
- `audio_generation` - Stories generating audio
- `video_generation` - Stories generating video
- `youtube_upload` - Stories uploading to YouTube
- `ghost_publishing` - Stories publishing to Ghost blog
- `completed` - Successfully completed stories
- `failed` - Stories that encountered errors

**Example:**
```promql
ephergent_stories_by_status{status="completed"}
ephergent_stories_by_status{status="failed"}
```

### `ephergent_workflow_step_distribution`
**Type:** Gauge
**Labels:** `step` (workflow step name)
**Description:** Number of stories currently at each workflow step. Similar to `stories_by_status` but provides a clearer name for dashboard visualization.

### `ephergent_average_workflow_duration_seconds`
**Type:** Gauge
**Description:** Average time in seconds from story creation to completion, calculated across all completed stories.

**Example:**
```promql
ephergent_average_workflow_duration_seconds / 60  # Convert to minutes
```

### `ephergent_stories_published_youtube`
**Type:** Gauge
**Description:** Total number of stories that have been published to YouTube (have a YouTube video ID).

### `ephergent_stories_published_ghost`
**Type:** Gauge
**Labels:** `ghost_status` (draft, published)
**Description:** Total number of stories published to Ghost blog, broken down by status.

**Example:**
```promql
ephergent_stories_published_ghost{ghost_status="published"}
ephergent_stories_published_ghost{ghost_status="draft"}
```

### `ephergent_media_generated_total_count`
**Type:** Gauge
**Labels:** `media_type` (image, audio, video)
**Description:** Cumulative count of media items generated, based on database state.

**Example:**
```promql
ephergent_media_generated_total_count{media_type="image"}
ephergent_media_generated_total_count{media_type="audio"}
ephergent_media_generated_total_count{media_type="video"}
```

## Business Metrics

These metrics are **event-driven counters** that increment as events occur in the system.

### `ephergent_stories_created_total`
**Type:** Counter
**Labels:** `source` (web_ui, api, mcp_server)
**Description:** Total number of stories created since application start.

**Example:**
```promql
rate(ephergent_stories_created_total[5m])  # Stories created per second
```

### `ephergent_workflow_steps_completed_total`
**Type:** Counter
**Labels:** `step` (workflow step name)
**Description:** Total number of workflow steps completed successfully.

**Example:**
```promql
rate(ephergent_workflow_steps_completed_total{step="image_generation"}[5m])
```

### `ephergent_workflow_steps_failed_total`
**Type:** Counter
**Labels:** `step`, `error_type`
**Description:** Total number of workflow steps that failed.

**Example:**
```promql
sum(rate(ephergent_workflow_steps_failed_total[1h])) by (step)
```

### `ephergent_workflow_step_duration_seconds`
**Type:** Histogram
**Labels:** `step`
**Buckets:** 1s, 5s, 10s, 30s, 60s, 120s, 300s, 600s, 1800s, 3600s
**Description:** Duration of each workflow step execution.

**Example:**
```promql
# 95th percentile duration for image generation
histogram_quantile(0.95, rate(ephergent_workflow_step_duration_seconds_bucket{step="image_generation"}[5m]))

# Average duration
rate(ephergent_workflow_step_duration_seconds_sum{step="story_generation"}[5m]) /
rate(ephergent_workflow_step_duration_seconds_count{step="story_generation"}[5m])
```

### `ephergent_stories_completed_total`
**Type:** Counter
**Description:** Total number of stories that completed all workflow steps.

### `ephergent_story_processing_time_seconds`
**Type:** Summary
**Description:** Total time from story creation to completion (end-to-end).

## Media Generation Metrics

### `ephergent_images_generated_total`
**Type:** Counter
**Labels:** `character`
**Description:** Total number of images generated, labeled by character.

**Example:**
```promql
sum(rate(ephergent_images_generated_total[1h])) by (character)
```

### `ephergent_audio_generated_total`
**Type:** Counter
**Labels:** `voice_model`
**Description:** Total number of audio files generated.

### `ephergent_videos_generated_total`
**Type:** Counter
**Description:** Total number of videos generated.

### `ephergent_media_generation_errors_total`
**Type:** Counter
**Labels:** `media_type`, `error_type`
**Description:** Total number of media generation errors.

**Example:**
```promql
sum(rate(ephergent_media_generation_errors_total[1h])) by (media_type)
```

## External Service Metrics

### `ephergent_external_api_requests_total`
**Type:** Counter
**Labels:** `service`, `endpoint`, `status_code`
**Description:** Total external API requests made.

**Example:**
```promql
# Request rate by service
sum(rate(ephergent_external_api_requests_total[5m])) by (service)

# Error rate for Gemini API
sum(rate(ephergent_external_api_requests_total{service="gemini",status_code=~"5.."}[5m])) /
sum(rate(ephergent_external_api_requests_total{service="gemini"}[5m]))
```

### `ephergent_external_api_duration_seconds`
**Type:** Histogram
**Labels:** `service`, `endpoint`
**Buckets:** 0.1s, 0.5s, 1s, 2s, 5s, 10s, 30s
**Description:** Duration of external API calls.

**Example:**
```promql
# 99th percentile latency for ComfyUI
histogram_quantile(0.99, rate(ephergent_external_api_duration_seconds_bucket{service="comfyui"}[5m]))
```

### `ephergent_external_service_available`
**Type:** Gauge
**Labels:** `service`
**Description:** Service availability status (1=up, 0=down).

**Example:**
```promql
ephergent_external_service_available{service="gemini"}
```

## Infrastructure Metrics

### HTTP Requests

#### `ephergent_http_requests_total`
**Type:** Counter
**Labels:** `method`, `endpoint`, `status_code`
**Description:** Total HTTP requests received.

**Example:**
```promql
# Request rate by endpoint
sum(rate(ephergent_http_requests_total[5m])) by (endpoint)

# Error rate
sum(rate(ephergent_http_requests_total{status_code=~"5.."}[5m])) /
sum(rate(ephergent_http_requests_total[5m]))
```

#### `ephergent_http_request_duration_seconds`
**Type:** Histogram
**Labels:** `method`, `endpoint`
**Description:** HTTP request latency.

**Example:**
```promql
# 95th percentile response time
histogram_quantile(0.95, rate(ephergent_http_request_duration_seconds_bucket[5m]))
```

#### `ephergent_http_requests_in_progress`
**Type:** Gauge
**Labels:** `method`, `endpoint`
**Description:** Number of HTTP requests currently being processed.

### Database Metrics

#### `ephergent_database_connections_active`
**Type:** Gauge
**Description:** Number of active database connections.

#### `ephergent_database_query_duration_seconds`
**Type:** Histogram
**Labels:** `query_type` (select, insert, update, delete)
**Description:** Duration of database queries.

#### `ephergent_database_errors_total`
**Type:** Counter
**Labels:** `error_type`
**Description:** Total number of database errors.

### Worker Metrics

#### `ephergent_worker_heartbeat_timestamp`
**Type:** Gauge
**Labels:** `worker_id`
**Description:** Unix timestamp of last worker heartbeat.

**Example:**
```promql
# Check if worker is alive (heartbeat within last 60 seconds)
time() - ephergent_worker_heartbeat_timestamp < 60
```

#### `ephergent_worker_tasks_processed_total`
**Type:** Counter
**Labels:** `worker_id`, `task_type`
**Description:** Total tasks processed by worker.

#### `ephergent_worker_task_duration_seconds`
**Type:** Histogram
**Labels:** `task_type`
**Description:** Duration of worker task processing.

### Story Queue Metrics

#### `ephergent_story_queue_size`
**Type:** Gauge
**Labels:** `status` (pending, processing, failed)
**Description:** Current number of stories in the processing queue.

**Example:**
```promql
ephergent_story_queue_size{status="pending"}
ephergent_story_queue_size{status="processing"}
```

## Example Prometheus Queries

### Story Processing Performance

```promql
# Stories completed per hour
increase(ephergent_stories_completed_total[1h])

# Current backlog of stories waiting to be processed
ephergent_story_queue_size{status="pending"}

# Average time to complete a story (in minutes)
ephergent_average_workflow_duration_seconds / 60

# Success rate for workflow steps
sum(rate(ephergent_workflow_steps_completed_total[1h])) /
(sum(rate(ephergent_workflow_steps_completed_total[1h])) + sum(rate(ephergent_workflow_steps_failed_total[1h])))
```

### Media Generation Analytics

```promql
# Total images in system
ephergent_media_generated_total_count{media_type="image"}

# Image generation rate (images per minute)
rate(ephergent_images_generated_total[5m]) * 60

# Most used character for image generation
topk(5, sum(ephergent_images_generated_total) by (character))

# Media generation error rate
sum(rate(ephergent_media_generation_errors_total[1h])) by (media_type)
```

### Publishing Metrics

```promql
# Total YouTube publications
ephergent_stories_published_youtube

# Ghost publishing breakdown
sum(ephergent_stories_published_ghost) by (ghost_status)

# Publishing completion rate
ephergent_stories_published_youtube / ephergent_stories_by_status{status="completed"}
```

### Workflow Stage Analysis

```promql
# Stories at each workflow stage
sum(ephergent_workflow_step_distribution) by (step)

# Failed stories percentage
ephergent_stories_by_status{status="failed"} / sum(ephergent_stories_by_status)

# Longest workflow step (95th percentile)
histogram_quantile(0.95,
  sum(rate(ephergent_workflow_step_duration_seconds_bucket[1h])) by (le, step)
)
```

### External Service Health

```promql
# Services currently down
count(ephergent_external_service_available == 0) by (service)

# Gemini API error rate
sum(rate(ephergent_external_api_requests_total{service="gemini",status_code=~"5.."}[5m])) /
sum(rate(ephergent_external_api_requests_total{service="gemini"}[5m]))

# Average API response time by service
avg(rate(ephergent_external_api_duration_seconds_sum[5m]) /
    rate(ephergent_external_api_duration_seconds_count[5m])) by (service)
```

### System Performance

```promql
# Request rate
sum(rate(ephergent_http_requests_total[5m]))

# Average response time
avg(rate(ephergent_http_request_duration_seconds_sum[5m]) /
    rate(ephergent_http_request_duration_seconds_count[5m]))

# Requests in flight
sum(ephergent_http_requests_in_progress)

# Database connection utilization
ephergent_database_connections_active
```

## Grafana Dashboard Examples

### Story Generation Overview Panel

```json
{
  "title": "Story Generation Overview",
  "panels": [
    {
      "title": "Stories by Status",
      "type": "stat",
      "targets": [
        {
          "expr": "ephergent_stories_by_status{status=\"completed\"}"
        },
        {
          "expr": "ephergent_stories_by_status{status=\"failed\"}"
        },
        {
          "expr": "ephergent_stories_by_status{status=\"queued\"}"
        }
      ]
    },
    {
      "title": "Workflow Stage Distribution",
      "type": "piechart",
      "targets": [
        {
          "expr": "sum(ephergent_workflow_step_distribution) by (step)"
        }
      ]
    },
    {
      "title": "Average Story Completion Time",
      "type": "gauge",
      "targets": [
        {
          "expr": "ephergent_average_workflow_duration_seconds / 60"
        }
      ]
    }
  ]
}
```

### Media Generation Dashboard

```promql
# Panel 1: Total Media Generated
ephergent_media_generated_total_count

# Panel 2: Media Generation Rate
rate(ephergent_images_generated_total[5m]) * 3600  # per hour
rate(ephergent_audio_generated_total[5m]) * 3600
rate(ephergent_videos_generated_total[5m]) * 3600

# Panel 3: Media Errors
sum(rate(ephergent_media_generation_errors_total[1h])) by (media_type)
```

### Publishing Status Dashboard

```promql
# Panel 1: YouTube Publications
ephergent_stories_published_youtube

# Panel 2: Ghost Publications
sum(ephergent_stories_published_ghost) by (ghost_status)

# Panel 3: Publishing Success Rate
(ephergent_stories_published_youtube + sum(ephergent_stories_published_ghost{ghost_status="published"})) /
ephergent_stories_by_status{status="completed"} * 100
```

### Alerting Rules

Example Prometheus alerting rules:

```yaml
groups:
  - name: ephergent_alerts
    interval: 30s
    rules:
      # Alert when story queue is backing up
      - alert: StoryQueueBacklog
        expr: ephergent_story_queue_size{status="pending"} > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Story queue has significant backlog"
          description: "{{ $value }} stories pending in queue for over 5 minutes"

      # Alert when workflow steps are failing
      - alert: HighWorkflowFailureRate
        expr: |
          sum(rate(ephergent_workflow_steps_failed_total[5m])) /
          (sum(rate(ephergent_workflow_steps_completed_total[5m])) +
           sum(rate(ephergent_workflow_steps_failed_total[5m]))) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High workflow failure rate detected"
          description: "More than 10% of workflow steps are failing"

      # Alert when external services are down
      - alert: ExternalServiceDown
        expr: ephergent_external_service_available == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "External service {{ $labels.service }} is down"
          description: "Service has been unavailable for 2 minutes"

      # Alert when worker hasn't reported heartbeat
      - alert: WorkerUnresponsive
        expr: time() - ephergent_worker_heartbeat_timestamp > 300
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Worker {{ $labels.worker_id }} is unresponsive"
          description: "No heartbeat received in 5 minutes"

      # Alert on high API error rate
      - alert: HighAPIErrorRate
        expr: |
          sum(rate(ephergent_external_api_requests_total{status_code=~"5.."}[5m])) /
          sum(rate(ephergent_external_api_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High external API error rate"
          description: "More than 5% of API requests are failing"
```

## Best Practices

1. **Scrape Interval**: Set Prometheus scrape interval to 15-30 seconds for good balance between freshness and load.

2. **Dashboard Design**: Use a mix of gauges (current state) and graphs (trends over time) for best visibility.

3. **Alerting**: Set up alerts for:
   - Queue backlog
   - High failure rates
   - Service availability
   - Worker health

4. **Query Performance**: Use recording rules for complex queries that are frequently accessed:

```yaml
groups:
  - name: ephergent_recording_rules
    interval: 30s
    rules:
      - record: job:ephergent_workflow_success_rate:5m
        expr: |
          sum(rate(ephergent_workflow_steps_completed_total[5m])) /
          (sum(rate(ephergent_workflow_steps_completed_total[5m])) +
           sum(rate(ephergent_workflow_steps_failed_total[5m])))

      - record: job:ephergent_story_completion_rate:1h
        expr: increase(ephergent_stories_completed_total[1h])
```

5. **Retention**: Configure appropriate retention in Prometheus based on your needs (default is 15 days).

## Troubleshooting

### Metrics Not Updating

If workflow-specific metrics aren't updating:
1. Check that `/metrics` endpoint is accessible
2. Verify database connection is healthy
3. Check application logs for errors in `update_workflow_metrics()`

### High Cardinality

If you see high cardinality warnings:
1. Review character labels on image generation metrics
2. Consider aggregating less common labels
3. Use Prometheus recording rules to pre-aggregate

### Missing Historical Data

Event-driven counters (like `ephergent_stories_created_total`) reset on application restart. This is expected behavior. Use database-driven gauges for persistent counts.
