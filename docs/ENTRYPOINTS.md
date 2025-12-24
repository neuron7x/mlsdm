# MLSDM Entrypoints Reference

> **Source of Truth** for all runtime entrypoints in MLSDM.

## Canonical Entrypoint

| Command | Status | Description |
|---------|--------|-------------|
| `mlsdm serve` | **Canonical** | Official user-facing CLI command. Start here. |

## All Entrypoints

### CLI Scripts

| Command / Invocation | File | Status | Notes |
|---------------------|------|--------|-------|
| `mlsdm serve` | `src/mlsdm/cli/__init__.py:cmd_serve` | **Canonical** | Official HTTP API server startup. Use `--config`, `--backend`, `--port` flags. |
| `mlsdm info` | `src/mlsdm/cli/__init__.py:cmd_info` | Canonical | Show version, status, and configuration. |
| `mlsdm check` | `src/mlsdm/cli/__init__.py:cmd_check` | Canonical | Validate environment and dependencies. |
| `mlsdm demo` | `src/mlsdm/cli/__init__.py:cmd_demo` | Canonical | Interactive demo of LLM wrapper. |
| `mlsdm eval` | `src/mlsdm/cli/__init__.py:cmd_eval` | Canonical | Run evaluation scenarios. |

### Python Module Entrypoints

| Command / Invocation | File | Status | Notes |
|---------------------|------|--------|-------|
| `python -m mlsdm.cli` | `src/mlsdm/cli/__main__.py` | Wrapper | Delegates to `mlsdm.cli.main`. Equivalent to `mlsdm` command. |
| `python -m mlsdm.entrypoints.dev` | `src/mlsdm/entrypoints/dev/__main__.py` | Supported | Development mode with hot reload. For local dev only. |
| `python -m mlsdm.entrypoints.cloud` | `src/mlsdm/entrypoints/cloud/__main__.py` | Supported | Cloud/Docker production mode. Used in `docker/Dockerfile`. |
| `python -m mlsdm.entrypoints.agent` | `src/mlsdm/entrypoints/agent/__main__.py` | Supported | Agent/API mode for LLM platform integration. |
| `python -m mlsdm.service.neuro_engine_service` | `src/mlsdm/service/neuro_engine_service.py` | Legacy | Deprecated shim. Use `mlsdm serve` or cloud entrypoint instead. |

### Docker Entrypoints

| Dockerfile | CMD | Status | Notes |
|------------|-----|--------|-------|
| `docker/Dockerfile` | `python -m mlsdm.entrypoints.cloud` | Working | Production-ready. Uses `config/production.yaml`. |
| `Dockerfile.neuro-engine-service` | `python -m mlsdm.service.neuro_engine_service` | Working | Legacy service image. Includes `config/` directory. |

### Example Scripts

| File | Status | Notes |
|------|--------|-------|
| `examples/run_neuro_service.py` | Example Only | Demonstrates direct `serve()` usage. Not for production. |

## Usage Guide

### For Users

```bash
# Recommended: Use the canonical CLI
mlsdm serve --port 8000 --config config/production.yaml

# Or with custom backend
mlsdm serve --backend openai --port 8000
```

### For Docker/Kubernetes

```bash
# Use cloud entrypoint for production containers
python -m mlsdm.entrypoints.cloud

# Environment variables control behavior:
# - HOST, PORT: Server binding
# - CONFIG_PATH: Configuration file
# - LLM_BACKEND: LLM provider (local_stub, openai)
# - MLSDM_SECURE_MODE: Enable authentication
```

### For Development

```bash
# Development mode with hot reload
python -m mlsdm.entrypoints.dev

# Or via CLI with reload
mlsdm serve --reload
```

## Configuration Priority

All entrypoints respect the same configuration priority:

1. **CLI arguments** (highest): `--config`, `--backend`, `--port`
2. **Environment variables**: `CONFIG_PATH`, `LLM_BACKEND`, `MLSDM_*`
3. **Mode defaults**: Dev/Cloud/Agent mode defaults
4. **Config file**: `config/default_config.yaml` or specified file
5. **Schema defaults** (lowest): Built-in defaults

## Health Endpoints

All entrypoints expose:

- `GET /health` - Basic health check
- `GET /health/liveness` - Kubernetes liveness probe
- `GET /health/readiness` - Kubernetes readiness probe
- `GET /health/metrics` - Prometheus metrics

## Deprecation Notes

- `src/mlsdm/cli/main.py`: Alternative CLI with different behavior. Use `mlsdm` CLI instead.
- `src/mlsdm/service/neuro_engine_service.py`: Legacy shim. Prefer `mlsdm serve` or cloud entrypoint.
