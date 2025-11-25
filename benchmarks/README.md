# MLSDM Benchmarks

Performance benchmark suite for the MLSDM NeuroCognitiveEngine. These benchmarks measure latency, throughput, and memory usage of the core engine components.

## Overview

The benchmark suite provides:
- **Pre-flight latency measurement**: Moral precheck latency
- **End-to-end latency**: Full generation pipeline with varying token counts
- **Throughput metrics**: Operations per second under different loads
- **Memory usage tracking**: Memory delta during benchmark execution
- **SLO compliance verification**: Automated checks against defined thresholds

## Available Benchmarks

### 1. `test_neuro_engine_performance.py`

Core NeuroCognitiveEngine performance benchmarks.

**Metrics Measured:**
| Metric | Description | SLO Threshold |
|--------|-------------|---------------|
| Pre-flight P95 | Moral precheck latency | < 20ms |
| End-to-End P95 | Full generation latency | < 500ms |
| Throughput | Operations per second | Informational |
| Memory Delta | Memory change during test | Informational |

**Scenarios:**
- **Pre-flight Latency**: Measures moral precheck timing (single-thread, warmup included)
- **Small Load**: 50 tokens generation with moderate prompts
- **Heavy Load**: Variable token counts (100, 250, 500, 1000 tokens)

## Quick Start

### Run via CLI (Recommended)

```bash
# Run with default settings (console output)
python benchmarks/test_neuro_engine_performance.py

# Run with JSON output (saves to benchmarks/results/)
python benchmarks/test_neuro_engine_performance.py --output json

# Run with Markdown table output
python benchmarks/test_neuro_engine_performance.py --output table

# Run with custom iterations and seed
python benchmarks/test_neuro_engine_performance.py --iterations 50 --seed 12345

# Full options
python benchmarks/test_neuro_engine_performance.py --help
```

### Run via pytest

```bash
# Run all benchmarks with pytest
pytest benchmarks/test_neuro_engine_performance.py -v -s -m benchmark

# Run specific benchmark
pytest benchmarks/test_neuro_engine_performance.py::test_benchmark_pre_flight_latency -v -s
```

### Run via Makefile

```bash
# Run all benchmarks
make benchmark

# Run with JSON output
make benchmark-json
```

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--iterations` | `-n` | Base number of iterations | 100 |
| `--output` | `-o` | Output format: console, json, table | console |
| `--output-dir` | | Directory for JSON results | benchmarks/results |
| `--seed` | `-s` | Random seed for reproducibility | 42 |

## Output Formats

### Console Output

```
======================================================================
BENCHMARK SUMMARY
======================================================================

Pre-flight Latency:
  P50: 0.001ms | P95: 0.002ms
  Throughput: 5000.0 ops/sec

Small Load (50 tokens):
  P50: 0.015ms | P95: 0.025ms
  Throughput: 4000.0 ops/sec

Heavy Load (varying tokens):
  100 tokens: P50=0.020ms, P95=0.030ms
  250 tokens: P50=0.025ms, P95=0.040ms
  500 tokens: P50=0.030ms, P95=0.050ms
  1000 tokens: P50=0.040ms, P95=0.060ms

SLO Compliance:
  ✓ All SLOs PASSED
======================================================================
```

### JSON Output

Results are saved to `benchmarks/results/neuro_engine_benchmark_<timestamp>.json`:

```json
{
  "metadata": {
    "timestamp": "2025-01-01T00:00:00+00:00",
    "seed": 42,
    "iterations_base": 100,
    "slo_pre_flight_p95_ms": 20.0,
    "slo_end_to_end_p95_ms": 500.0
  },
  "pre_flight": {
    "p50": 0.001,
    "p95": 0.002,
    "p99": 0.003,
    "min": 0.0005,
    "max": 0.005,
    "mean": 0.0015,
    "count": 1000,
    "throughput_ops_sec": 5000.0,
    "memory_delta_mb": 0.5,
    "scenario": "pre_flight_latency"
  },
  "small_load": { ... },
  "heavy_load": {
    "tokens_100": { ... },
    "tokens_250": { ... },
    "tokens_500": { ... },
    "tokens_1000": { ... }
  },
  "slo_compliance": {
    "all_passed": true,
    "checks": {
      "pre_flight_p95": true,
      "small_load_p95": true,
      "heavy_load_tokens_100_p95": true,
      ...
    }
  }
}
```

### Markdown Table Output

```markdown
| Benchmark | P50 (ms) | P95 (ms) | P99 (ms) | Throughput (ops/s) | SLO Status |
|-----------|----------|----------|----------|-------------------|------------|
| Pre-flight Latency | 0.001 | 0.002 | 0.003 | 5000.0 | ✓ PASS |
| End-to-End (50 tokens) | 0.015 | 0.025 | 0.035 | 4000.0 | ✓ PASS |
| End-to-End (100 tokens) | 0.020 | 0.030 | 0.040 | 3500.0 | ✓ PASS |
...
```

## Reproducibility

All benchmarks are designed for reproducible results:

1. **Fixed Random Seeds**: Use `--seed` to control randomness (default: 42)
2. **Stub LLM Backend**: Uses deterministic stub functions instead of real LLM calls
3. **No External Dependencies**: Benchmarks run locally without network calls
4. **Deterministic Embeddings**: Hash-based embeddings for consistent results

## Interpreting Results

### What is "Normal"?

On a typical development machine (CPU-only):

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| Pre-flight P95 | < 5ms | Very fast moral precheck |
| Small Load P95 | < 100ms | With stub LLM backend |
| Heavy Load P95 | < 200ms | Varies by token count |
| Throughput | 1000-10000 ops/s | Depends on system load |

### SLO Thresholds

| SLO | Threshold | Rationale |
|-----|-----------|-----------|
| Pre-flight P95 | 20ms | Fast enough for interactive use |
| End-to-End P95 | 500ms | Acceptable latency for LLM operations |

### Troubleshooting

- **High Latency**: Check system load, reduce iterations
- **Memory Issues**: Monitor `memory_delta_mb` for leaks
- **Inconsistent Results**: Ensure fixed seed, minimize background processes
- **SLO Failures**: Review specific failed checks in output

## Baseline Comparison

For comparing MLSDM against baseline implementations, see:
- `tests/benchmarks/compare_baselines.py` - Compares MLSDM vs Simple RAG, Vector DB, Stateless modes
- `tests/benchmarks/README.md` - Detailed comparison methodology

## Directory Structure

```
benchmarks/
├── README.md                        # This file
├── __init__.py                      # Package initialization
├── test_neuro_engine_performance.py # Main benchmark script
└── results/                         # JSON output directory
    └── .gitkeep
```

## Development

### Adding New Benchmarks

1. Create a function `benchmark_<name>()` that returns a dict with statistics
2. Add a pytest test function `test_benchmark_<name>()`
3. Update `run_all_benchmarks()` to include the new benchmark
4. Update this README with the new benchmark description

### Running Linting

```bash
ruff check benchmarks/
```

## Dependencies

The benchmarks use only standard project dependencies:
- `numpy` - Statistical calculations
- `psutil` - Memory usage measurement (optional)
- `pytest` - Test framework (optional for CLI mode)

No additional heavy dependencies are required.
