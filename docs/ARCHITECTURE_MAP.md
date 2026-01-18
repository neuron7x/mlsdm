# MLSDM Architecture Map

## Architecture Type (Evidence)
- **Classification:** Monolith (single FastAPI service process).
- **Evidence:** The canonical HTTP runtime is started via `mlsdm.entrypoints.serve.serve`, which launches a single FastAPI app from `mlsdm.api.app` using Uvicorn (`src/mlsdm/entrypoints/serve.py`, `src/mlsdm/api/app.py`).

## System Map Summary

### A) API / Entrypoints + Request Lifecycle
- **Owners:**
  - `mlsdm.entrypoints.serve.get_canonical_app`, `mlsdm.entrypoints.serve.serve` (`src/mlsdm/entrypoints/serve.py`).
  - `mlsdm.api.app.app` and `mlsdm.api.app.lifespan` (`src/mlsdm/api/app.py`).
- **Inbound dependencies:** Uvicorn runtime, FastAPI router definitions.
- **Outbound dependencies:** `MemoryManager`, `NeuroCognitiveEngine`, `ConfigLoader`, health subsystem.
- **State inputs/outputs:**
  - Inputs: `CONFIG_PATH`, `LLM_BACKEND`, `RATE_LIMIT_*` env vars.
  - Outputs: `app.state.memory_manager`, `app.state.neuro_engine`, health state linkage.
- **Failure behavior:**
  - Fail-fast on missing runtime initialization (HTTP 503), explicit rate limit errors (HTTP 429).
  - Lifespan startup registers cleanup and uses system logger for startup/shutdown events.
- **Invariants:**
  - App initialization must create `MemoryManager` and `NeuroCognitiveEngine` before request handling.
  - Lifespan startup/shutdown must maintain deterministic order.

### B) Security Middleware Chain (Order + Enforcement)
- **Owners:** `SecurityHeadersMiddleware`, `RequestIDMiddleware`, `TimeoutMiddleware`, `PriorityMiddleware`, `BulkheadMiddleware` (`src/mlsdm/api/middleware.py`).
- **Inbound dependencies:** FastAPI middleware registration in `mlsdm.api.app`.
- **Outbound dependencies:** Observability logs, response headers, timeout enforcement.
- **State inputs/outputs:**
  - Input: request context headers, request lifecycle state.
  - Output: enforced timeouts, request IDs, concurrency limits.
- **Failure behavior:**
  - Fail-closed on timeouts/bulkhead capacity; explicit HTTP error responses.
- **Invariants:**
  - Middleware ordering is stable and enforced in `mlsdm.api.app`.

### C) Config Load / Validate + Schema Ownership
- **Owners:** `ConfigLoader.load_config` (`src/mlsdm/utils/config_loader.py`), `SystemConfig` schema (`src/mlsdm/utils/config_schema.py`).
- **Inbound dependencies:** CLI, API lifespan, entrypoints.
- **Outbound dependencies:** `MemoryManager` and memory subsystem configuration.
- **State inputs/outputs:**
  - Input: YAML/INI config files, env overrides.
  - Output: validated dict config passed to core subsystems.
- **Failure behavior:**
  - Fail-fast on missing config file (unless default packaged config is used).
- **Invariants:**
  - Default config path is canonicalized and must remain consistent across entrypoints.

### D) State Lifecycle (System State Store + Propagation)
- **Owners:** `MemoryManager` (`src/mlsdm/core/memory_manager.py`), `MultiLevelSynapticMemory` (`src/mlsdm/memory/multi_level_memory.py`).
- **Inbound dependencies:** Config dict from `ConfigLoader`, API request handlers.
- **Outbound dependencies:** API responses, metrics collectors, health subsystem.
- **State inputs/outputs:**
  - Input: event vectors, moral value, config defaults.
  - Output: memory state vectors, metrics, provenance entries.
- **Failure behavior:**
  - Strict mode surfaces configuration/state errors; optional LTM degrades with logs.
- **Invariants:**
  - State format versioning and required keys are enforced on load.

### E) Memory Subsystem Lifecycle (Init, Update, Persistence Hooks)
- **Owners:** `MemoryManager`, `MultiLevelSynapticMemory`, `QILM` (`src/mlsdm/memory/qilm_module.py`).
- **Inbound dependencies:** Processed event vectors from API.
- **Outbound dependencies:** metrics, state snapshots, serialization.
- **State inputs/outputs:**
  - Input: event vectors, moral filter thresholds, rhythm state.
  - Output: updated memory states and metrics.
- **Failure behavior:**
  - LTM optional: warns and degrades without crashing unless strict mode.
- **Invariants:**
  - Memory state persists under defined format version; migrations are explicit.

### F) Adapters / Providers (Factory Selection + Fallback)
- **Owners:** `build_neuro_engine_from_env` (`src/mlsdm/engine/factory.py`), adapter factory (`src/mlsdm/adapters/provider_factory.py`).
- **Inbound dependencies:** environment variables, runtime config.
- **Outbound dependencies:** `NeuroCognitiveEngine` with LLM providers.
- **State inputs/outputs:**
  - Input: `LLM_BACKEND`, `MULTI_LLM_BACKENDS` env vars.
  - Output: engine configured with selected provider/router.
- **Failure behavior:**
  - Fail-fast on invalid backend selection; fallback to stub where configured.
- **Invariants:**
  - Provider selection must be deterministic for identical env state.

### G) Observability (Logging, Metrics, Tracing)
- **Owners:** `initialize_tracing`, `shutdown_tracing` (`src/mlsdm/observability/tracing.py`), metrics exporters (`src/mlsdm/observability/metrics.py`).
- **Inbound dependencies:** API lifecycle hooks, runtime env vars.
- **Outbound dependencies:** telemetry exporters, log sinks.
- **State inputs/outputs:**
  - Input: `OTEL_*`, `LOG_LEVEL` env vars.
  - Output: spans, counters, structured logs.
- **Failure behavior:**
  - Optional tracing degrades gracefully when unavailable.
- **Invariants:**
  - Startup initializes tracing before serving requests; shutdown terminates exporters.

### H) Scripts and CI Validation Gates
- **Owners:** `Makefile`, `scripts/*`, CI workflows (`.github/workflows/ci-smoke.yml`).
- **Inbound dependencies:** local dev + CI runners.
- **Outbound dependencies:** test reports, coverage reports, contract verification.
- **Failure behavior:**
  - CI gates fail-fast on contract/script validation failures.
- **Invariants:**
  - Architecture contracts and docs must remain in sync with code.
