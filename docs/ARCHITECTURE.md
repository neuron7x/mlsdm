# Architecture Overview (MLE 2024)

**Document Version**: 1.0.0  
**Last Updated**: 2025-12-28  
**Status**: Production  
**Readiness**: See [status/READINESS.md](status/READINESS.md)

This document provides a high-level architecture overview for machine learning engineers. For detailed specifications, see [ARCHITECTURE_SPEC.md](ARCHITECTURE_SPEC.md).

---

## System Overview

MLSDM is a **neurobiologically-grounded cognitive architecture** that wraps LLMs with:
- **Moral governance** (adaptive filtering without external training)
- **Phase-based memory** (wake/sleep cycles with distinct behaviors)
- **Bounded resources** (hard memory limits, predictable footprint)
- **Observability** (metrics, logging, tracing hooks)

### Components Under `src/mlsdm/`

```
src/mlsdm/
├── api/              # FastAPI application and HTTP endpoints
├── entrypoints/      # Service entrypoints (dev, cloud, agent, health)
├── engine/           # NeuroCognitiveEngine orchestration
├── core/             # Core cognitive components
│   ├── cognitive_controller.py    # Main coordinator
│   ├── llm_wrapper.py             # Universal LLM wrapper
│   ├── llm_pipeline.py            # Pipeline with filters
│   └── memory_manager.py          # Memory lifecycle
├── memory/           # Memory subsystems (PELM, multi-level)
├── security/         # Moral filter, guardrails, input validation
├── rhythm/           # Circadian rhythm and state machine
├── observability/    # Metrics, logging, tracing
├── router/           # LLM router and adapter factory
├── adapters/         # LLM provider adapters (OpenAI, local stub)
├── config/           # Configuration loader and schema
├── speech/           # Aphasia detection and speech governance
├── state/            # State persistence and management
└── utils/            # Shared utilities (rate limiter, metrics)
```

---

## Request/Data Flow

### HTTP Request Flow (API → Core → Memory → Output)

1. **Entrypoint** (`src/mlsdm/entrypoints/`)
   - `dev/__main__.py`: Development server with hot reload
   - `cloud/__main__.py`: Production server (multi-worker)
   - `agent/__main__.py`: Agent/API server for LLM integration
   - `health.py`: Health check utility

2. **API Layer** (`src/mlsdm/api/`)
   - FastAPI application receives HTTP requests
   - Rate limiting middleware (`src/mlsdm/utils/rate_limiter.py`)
   - Health endpoints: `/health/liveness`, `/health/readiness`, `/health/detailed`
   - Inference endpoint: `/generate` (POST)

3. **Engine Layer** (`src/mlsdm/engine/`)
   - `NeuroCognitiveEngine` (`neuro_cognitive_engine.py`) orchestrates processing
   - Routes requests through cognitive controller
   - Aggregates telemetry and metrics

4. **Core Layer** (`src/mlsdm/core/`)
   - `CognitiveController` coordinates all subsystems
   - `LLMWrapper` or `NeuroLangWrapper` wraps the LLM call
   - `LLMPipeline` applies pre-filters and post-filters
   - `MemoryManager` handles memory retrieval and storage

5. **Memory Subsystems** (`src/mlsdm/memory/`)
   - `PELM` (Phase-Entangled Lattice Memory): phase-aware retrieval
   - `MultiLevelSynapticMemory`: L1/L2/L3 memory hierarchy
   - Embedding cache (`src/mlsdm/utils/embedding_cache.py`)

6. **Security/Filters** (`src/mlsdm/security/`)
   - `MoralFilterV2` (`moral_filter_v2.py`): adaptive moral governance
   - `SecurityGuardrails` (`guardrails.py`): input/output validation
   - `RoleBoundaryController` (if applicable)

7. **Output**
   - Response returned through API
   - Metrics recorded to Prometheus
   - Logs emitted via structured logging
   - Traces sent to OpenTelemetry (if enabled)

### Direct Wrapper Flow (Python Integration)

For direct Python usage (no HTTP):

```python
from mlsdm.core.llm_wrapper import LLMWrapper

wrapper = LLMWrapper(llm_fn, config)
result = wrapper.generate(prompt)
```

Flow: `LLMWrapper` → `CognitiveController` → `LLMPipeline` → Memory → LLM → Filters → Output

---

## Configuration Model

### Priority Order (Highest to Lowest)

1. **Environment Variables** (prefixed with `MLSDM_`)
2. **Configuration File** (YAML or INI format)
3. **Default Values** (defined in schema)

### Configuration Sources

- `config/default_config.yaml`: Development/testing defaults
- `config/production.yaml`: Production-hardened template (review READINESS.md)
- `env.example`, `env.dev.example`, `env.cloud.example`: Environment variable templates
- `pyproject.toml`: Package metadata and tool configuration

### Where Configs Merge

- **Loader**: `src/mlsdm/config/config_loader.py`
- **Schema**: `src/mlsdm/config/schema.py`
- **Validation**: `scripts/validate_policy_config.py`

Configuration is loaded once at startup and validated against the schema. Environment variables override file settings.

See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for detailed configuration options.

---

## Observability

### Metrics (Prometheus)

- **Instrumentation**: `src/mlsdm/observability/metrics.py`
- **Registry**: `src/mlsdm/utils/metrics.py`
- **Export**: `/health/metrics` endpoint
- **Key Metrics**:
  - `process_event_latency_seconds`: Event processing time
  - `total_events_processed`: Total events counter
  - `memory_usage_bytes`: Memory consumption
  - `moral_filter_threshold`: Current moral threshold
  - `cpu_usage_percent`: CPU utilization

### Logging (Structured)

- **Aphasia Logging**: `src/mlsdm/observability/aphasia_logger.py`
- **Configuration**: LOG_LEVEL environment variable
- **Format**: JSON structured logs for production
- **Tests**: `tests/observability/test_aphasia_logging.py`

### Tracing (OpenTelemetry - Optional)

- **Instrumentation**: `src/mlsdm/observability/tracing.py`
- **Dependency**: `opentelemetry-api`, `opentelemetry-sdk` (optional)
- **Enable**: Install observability extras: `pip install -e ".[observability]"`
- **Tests**: `tests/observability/test_aphasia_metrics.py`

### Observability Tests

```bash
# Run observability tests
make test-memory-obs
pytest tests/observability/ -v
```

See [OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md) for complete instrumentation details.

---

## Evidence Chain

### Artifacts and Evidence Structure

Evidence snapshots are stored in `artifacts/evidence/<date>/<sha>/`:

```
artifacts/evidence/
└── 2025-12-26/
    └── 2a6b52dd6fd4/
        ├── manifest.json                    # Snapshot metadata
        ├── coverage/
        │   └── coverage.xml                 # Coverage report
        ├── pytest/
        │   └── junit.xml                    # Test results
        ├── benchmarks/
        │   └── benchmark-metrics.json       # Performance metrics
        └── memory/
            └── memory_footprint.json        # Memory usage
```

### Capture Script

Generate evidence snapshot:

```bash
make evidence
# or directly:
uv run python scripts/evidence/capture_evidence.py
```

This script:
1. Runs test suite with coverage
2. Runs benchmarks
3. Captures memory footprint
4. Generates manifest with git SHA, timestamp, and file inventory
5. Saves to `artifacts/evidence/<date>/<short-sha>/`

### Verifier Command

Validate evidence snapshot integrity:

```bash
make verify-metrics
# or directly:
python scripts/evidence/verify_evidence_snapshot.py --evidence-dir artifacts/evidence/<date>/<sha>
```

Verifier checks:
- Required files exist (manifest.json, coverage.xml, junit.xml)
- Manifest structure is valid
- File paths in manifest resolve
- No forbidden patterns (secrets, large files)
- Per-file size limits (5MB)

**Tests**:
- `tests/unit/test_verify_evidence_snapshot.py`: Verifier script tests
- `tests/unit/test_evidence_guard.py`: Evidence safety guards (forbidden patterns, size limits)

See [METRICS_SOURCE.md](METRICS_SOURCE.md) for metrics sourced from evidence snapshots.

---

## Design Principles

1. **Truth-first**: All documentation grounded in code and evidence
2. **Reproducible**: Deterministic runs with seed control
3. **Bounded**: Hard memory limits, predictable resource usage
4. **Observable**: Comprehensive instrumentation
5. **Safe**: Moral governance without external training
6. **Testable**: High coverage with property-based tests

---

## Related Documentation

- **Detailed Architecture**: [ARCHITECTURE_SPEC.md](ARCHITECTURE_SPEC.md)
- **Configuration**: [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
- **Evaluation**: [EVALUATION.md](EVALUATION.md)
- **Runbook**: [RUNBOOK.md](RUNBOOK.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)

---

**Navigation**: [← Back to Documentation Index](README.md)
