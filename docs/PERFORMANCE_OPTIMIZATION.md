# Performance Optimization Guide

## Architecture Overview

### Async-First Design
- All I/O operations are async
- CPU-bound operations use thread pools
- Zero-blocking calls in request path

### Zero-Allocation Hot Path
- Moral filter uses fast path (single comparison)
- PELM uses vectorized numpy operations
- Minimal object creation per request

### Connection Pooling
- Shared thread pool for CPU operations
- Async PELM with non-blocking operations
- FastAPI lifespan for resource management

## Performance Targets

| Metric | Target | CI Tolerance | Production |
|--------|--------|--------------|------------|
| P50 Latency | 30ms | 36ms | 25ms |
| P95 Latency | 120ms | 150ms | 100ms |
| P99 Latency | 200ms | 250ms | 180ms |
| Throughput | 100 RPS | 80 RPS | 200+ RPS |
| Error Rate | <1% | <2% | <0.5% |

## Optimization Checklist

### Code Level
- [ ] Use `__slots__` for frequently instantiated classes
- [ ] Use `dataclass(frozen=True, slots=True)` for DTOs
- [ ] Avoid logging in hot paths
- [ ] Use numpy for vectorized operations
- [ ] Lazy import expensive modules

### Architecture Level
- [ ] All I/O is async
- [ ] CPU-bound work in thread pools
- [ ] Connection pooling for external services
- [ ] Caching where appropriate
- [ ] Batch operations when possible

### Infrastructure Level
- [ ] Use production ASGI server (uvicorn/gunicorn)
- [ ] Enable HTTP/2
- [ ] Configure worker processes = CPU cores
- [ ] Use fast JSON serializer (orjson)
- [ ] Enable response compression

## Profiling

### CPU Profiling
```bash
python -m cProfile -o profile.stats script.py
python -m pstats profile.stats
```

### Memory Profiling
```bash
python -m memory_profiler script.py
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Monitoring

### Key Metrics
- Request latency (P50, P95, P99)
- Throughput (requests per second)
- Error rate (percentage)
- Memory usage (MB)
- CPU usage (percentage)

### Alerting Thresholds
- P95 latency > 150ms for 5 minutes
- Error rate > 2% for 5 minutes
- Memory growth > 100MB in 10 minutes

## Troubleshooting

### High Latency
1. Check CPU usage (top/htop)
2. Profile hot paths (cProfile)
3. Check database query times
4. Review async/await usage
5. Check thread pool saturation

### High Memory Usage
1. Profile memory (memory_profiler)
2. Check for memory leaks (gc.collect())
3. Review caching strategies
4. Check PELM capacity settings

### Low Throughput
1. Check worker process count
2. Review connection pool size
3. Check for blocking I/O
4. Profile request handlers
5. Check network saturation
