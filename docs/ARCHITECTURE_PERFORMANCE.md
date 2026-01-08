# Performance Architecture Overview

This document summarizes the performance-first architecture for MLSDM services,
including async execution, zero-overhead hot paths, and observability feedback loops.

## Async Request Path

1. **FastAPI lifespan** initializes shared async resources.
2. **Async engine** uses thread pools for CPU-bound operations.
3. **PELMAsync** handles vectorized similarity in a pool without blocking.
4. **MoralFilterV3** applies a fast-path decision with optional drift detection.

## Hot Path Optimizations

- Minimal allocations in filter decisions (`FilterDecision`).
- Pre-allocated buffers for drift detection.
- Vectorized numpy similarity scores.
- Lazy imports for logging and optional diagnostics.

## Performance Monitoring Loop

- Middleware captures request latency and error rates.
- Rolling windows calculate P50/P95/P99 and throughput.
- Metrics endpoint exposes current SLO compliance.

## CI Gates

Performance regression tests enforce P50/P95/P99 and throughput floors.
Benchmark JSON outputs are analyzed to block regressions and preserve baselines.

## Operational Guidance

- Configure worker pools according to CPU availability.
- Use SLO alerts and dashboards to detect drift early.
- Review performance baselines weekly and adjust thresholds with traceable evidence.
