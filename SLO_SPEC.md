SLO Spec

SLI1: Latency = histogram_quantile(0.95, event_processing_time_seconds)
SLO: P95 < 100ms, 99.9% of requests

SLI2: Error Rate = sum(errors) / sum(requests)
SLO: < 0.1%

SLI3: Accept Rate = accepted / total_events
SLO: > 90%

Error Budget: 0.1% errors/month.
If burn rate > 1 → alert, > 5 → freeze releases.
