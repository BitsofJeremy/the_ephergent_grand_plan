# Workflow Metrics - Quick Reference

## Access Metrics

```bash
curl http://localhost:5000/metrics
```

## New Workflow Metrics (Database-Driven)

### Stories by Workflow Status
```promql
# All statuses
ephergent_stories_by_status

# Specific status
ephergent_stories_by_status{status="completed"}
ephergent_stories_by_status{status="failed"}
ephergent_stories_by_status{status="queued"}
```

### Publishing Stats
```promql
# YouTube publications
ephergent_stories_published_youtube

# Ghost publications
ephergent_stories_published_ghost{ghost_status="published"}
ephergent_stories_published_ghost{ghost_status="draft"}
```

### Media Generation Counts
```promql
# Total media generated (cumulative from database)
ephergent_media_generated_total_count{media_type="image"}
ephergent_media_generated_total_count{media_type="audio"}
ephergent_media_generated_total_count{media_type="video"}
```

### Performance Metrics
```promql
# Average time to complete a story (in minutes)
ephergent_average_workflow_duration_seconds / 60

# Workflow stage distribution (identify bottlenecks)
ephergent_workflow_step_distribution
```

## Common Queries

### Story Success Rate
```promql
ephergent_stories_by_status{status="completed"} /
(ephergent_stories_by_status{status="completed"} + ephergent_stories_by_status{status="failed"})
```

### Stories Pending in Queue
```promql
ephergent_stories_by_status{status="queued"}
```

### Total Media Generated
```promql
sum(ephergent_media_generated_total_count)
```

### Publishing Completion Rate
```promql
ephergent_stories_published_youtube / ephergent_stories_by_status{status="completed"}
```

## Grafana Panels

### Story Status (Stat)
```promql
ephergent_stories_by_status{status="completed"}
```
Label: "Completed Stories"

### Workflow Distribution (Pie Chart)
```promql
sum(ephergent_workflow_step_distribution) by (step)
```

### Average Duration (Gauge)
```promql
ephergent_average_workflow_duration_seconds / 60
```
Unit: minutes

### Media Stats (Stats Grid)
```promql
ephergent_media_generated_total_count
```
Transform: Group by media_type

## Alert Examples

### Queue Backlog
```yaml
- alert: StoryQueueBacklog
  expr: ephergent_stories_by_status{status="queued"} > 50
  for: 10m
```

### High Failure Rate
```yaml
- alert: HighFailureRate
  expr: |
    ephergent_stories_by_status{status="failed"} /
    sum(ephergent_stories_by_status) > 0.1
```

## Files Modified

- `/ephergent_generator/utils/metrics.py` - Added 6 new gauge metrics and update methods
- `/METRICS_GUIDE.md` - Complete documentation with examples
- `/METRICS_IMPLEMENTATION_SUMMARY.md` - Implementation details and testing guide

## Documentation

- **Full Guide:** [METRICS_GUIDE.md](./METRICS_GUIDE.md)
- **Implementation:** [METRICS_IMPLEMENTATION_SUMMARY.md](./METRICS_IMPLEMENTATION_SUMMARY.md)
- **This Reference:** [METRICS_QUICK_REFERENCE.md](./METRICS_QUICK_REFERENCE.md)
