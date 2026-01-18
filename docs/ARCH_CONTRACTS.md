# MLSDM Architecture Contracts

## Purpose
This ledger defines the explicit module contracts and invariants required to keep MLSDM deterministic, safe, and auditable. It also records architectural issues discovered by evidence, including their resolution status.

## Module Contracts (Explicit Boundaries)

### API Boundary (FastAPI Runtime)
- **Owner:** `mlsdm.api.app` (`src/mlsdm/api/app.py`).
- **Contract:**
  - Requests must pass through the middleware chain in the order registered (`SecurityHeaders`, `RequestID`, `Timeout`, `Priority`, `Bulkhead`).
  - Runtime state (`memory_manager`, `neuro_engine`) must be initialized before request handling.
  - Authentication and rate limiting must fail-closed with explicit HTTP errors.
- **Post-conditions:**
  - Responses include stable contract fields for `/generate` and `/infer` endpoints.

### Config Boundary
- **Owner:** `ConfigLoader.load_config` (`src/mlsdm/utils/config_loader.py`).
- **Contract:**
  - Config path resolution is deterministic and validated.
  - The canonical default config path is shared across entrypoints.
- **Post-conditions:**
  - Returns a validated configuration dict or fails fast with actionable error.

### Memory Boundary
- **Owner:** `MemoryManager` (`src/mlsdm/core/memory_manager.py`).
- **Contract:**
  - Memory state schema includes required keys and explicit format versioning.
  - Optional LTM storage degrades with structured logging when unavailable.
- **Post-conditions:**
  - State mutations are versioned and metrics are updated per event.

### Adapter / Provider Boundary
- **Owner:** `build_neuro_engine_from_env` (`src/mlsdm/engine/factory.py`).
- **Contract:**
  - LLM backend selection is deterministic for a given environment.
  - Invalid provider configuration fails fast with explicit error.
- **Post-conditions:**
  - Engine instance is fully constructed with embedding function and provider routing.

### Observability Boundary
- **Owner:** `mlsdm.observability.tracing` (`src/mlsdm/observability/tracing.py`).
- **Contract:**
  - Tracing initialization occurs before request handling.
  - Optional tracing must degrade gracefully when exporters are unavailable.
- **Post-conditions:**
  - Tracing shutdown is invoked during app shutdown.

## Architectural Invariants
- **I1 – Explicit boundaries:** Each module interface exposes stable signatures and validates input at boundary.
- **I2 – Deterministic initialization:** Startup order must remain: config validation → dependency construction → middleware wiring → runtime ready.
- **I3 – Deterministic state propagation:** Shared state is initialized once and validated before use.
- **I4 – Consistent error semantics:** Protected flows fail-closed; optional subsystems degrade with logs.
- **I5 – One source of truth for shared defaults:** Canonical defaults are centralized and reused.
- **I6 – Docs are executable truth:** Documentation contracts must match code defaults and verified by gates/tests.

## Contract Ledger (Evidence-Only)

### P1 — Canonical default config path drift
- **Evidence:** Default config path literal duplicated across API, CLI, entrypoints (`src/mlsdm/api/app.py`, `src/mlsdm/cli/__init__.py`, `src/mlsdm/entrypoints/health.py`).
- **Invariant impacted:** I5 (one source of truth).
- **Failure scenario:** A future change updates one default but not the others, leading to inconsistent runtime behavior and documentation drift.
- **Minimal fix strategy:** Introduce a canonical default constant and replace duplicate literals.

### P1 — Rate limit default mismatch across modules
- **Evidence:** App defaults in `src/mlsdm/api/app.py` differ from runtime config defaults in `src/mlsdm/config/runtime.py` and security rate limiter defaults in `src/mlsdm/security/rate_limit.py`.
- **Invariant impacted:** I5 (one source of truth), I6 (docs must match code).
- **Failure scenario:** Running with missing env vars yields different rate limits depending on module entrypoint, causing unexpected enforcement.
- **Minimal fix strategy:** Centralize defaults in `mlsdm.config.defaults` and use them across API, runtime config, and security modules.

### P2 — Security policy docs drift on rate-limit defaults
- **Evidence:** `docs/SECURITY_POLICY.md` lists defaults that do not match runtime enforcement.
- **Invariant impacted:** I6 (docs are executable truth).
- **Failure scenario:** Operators provision incorrect rate-limit settings based on documentation.
- **Minimal fix strategy:** Align security policy defaults with canonical code defaults and gate via script/test.

## Overrides / Exceptions
- **Testing:** `DISABLE_RATE_LIMIT=1` may bypass runtime rate limiting for test suites and CI.
- **Deployment:** External rate limiting can supersede in-memory token bucket enforcement for multi-instance deployments.
