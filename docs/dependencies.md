# MLSDM Dependency Management Guide

This document provides comprehensive information about managing dependencies for the MLSDM (Machine Learning State-of-the-art Decision Making) Governed Cognitive Memory project.

## Table of Contents

- [Overview](#overview)
- [Core Dependencies](#core-dependencies)
- [Optional Dependencies](#optional-dependencies)
- [Installation Scenarios](#installation-scenarios)
- [Development Environment](#development-environment)
- [Security Considerations](#security-considerations)
- [Dependency Auditing](#dependency-auditing)
- [Troubleshooting](#troubleshooting)

## Overview

MLSDM uses a modular dependency structure defined in `pyproject.toml` with clear separation between:

- **Core runtime dependencies**: Minimal dependencies needed to use MLSDM as a library
- **Optional feature dependencies**: Additional packages for specific features (observability, neural language processing, LLM providers, etc.)
- **Development dependencies**: Tools for development, testing, and quality assurance

### Python Version Support

MLSDM requires Python 3.10 or later, with tested support for:
- Python 3.10
- Python 3.11
- Python 3.12 (best supported)

## Core Dependencies

The core runtime dependencies are installed automatically with the base package:

```bash
pip install mlsdm-governed-cognitive-memory
```

### Core Runtime Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | ≥2.0.0, <3.0.0 | Numerical computing for embeddings and memory operations |
| `fastapi` | ≥0.110.0, <1.0.0 | Web framework for API endpoints |
| `uvicorn` | ≥0.29.0, <1.0.0 | ASGI server for running the service |
| `starlette` | ≥0.37.0, <1.0.0 | Core web toolkit (FastAPI dependency) |
| `pydantic` | ≥2.0.0, <3.0.0 | Data validation and configuration management |
| `pyyaml` | ≥6.0.1, <7.0.0 | YAML configuration file parsing |
| `prometheus-client` | ≥0.20.0, <1.0.0 | Metrics and observability |
| `tenacity` | ≥8.2.3, <9.0.0 | Retry logic and resilience patterns |
| `psutil` | ≥5.9.0, <6.0.0 | System and process utilities |
| `requests` | ≥2.32.3, <3.0.0 | HTTP client for LLM adapters and webhooks |
| `typing-extensions` | ≥4.0.0, <5.0.0 | Type hints compatibility |

## Optional Dependencies

Optional dependencies are organized into logical groups (extras) that can be installed as needed.

### Observability

Distributed tracing and telemetry with OpenTelemetry:

```bash
pip install "mlsdm-governed-cognitive-memory[observability]"
```

**Packages:**
- `opentelemetry-api` ≥1.24.0, <2.0.0
- `opentelemetry-sdk` ≥1.24.0, <2.0.0

**Use case:** Production deployments requiring distributed tracing, span collection, and observability integration.

### Neural Language Processing (NeuroLang)

PyTorch-based neural language processing extension (Aphasia-Broca):

```bash
pip install "mlsdm-governed-cognitive-memory[neurolang]"
```

**Packages:**
- `torch` ≥2.0.0, <3.0.0

**Use case:** Enables the NeuroLang extension for advanced language processing features. Note: PyTorch is a large dependency (~2GB+).

### LLM Provider Integrations

Optional integrations with external LLM providers:

```bash
pip install "mlsdm-governed-cognitive-memory[llm-providers]"
```

**Packages:**
- `openai` ≥1.0.0, <2.0.0 - OpenAI API integration
- `anthropic` ≥0.30.0, <1.0.0 - Anthropic Claude API integration

**Use case:** When using OpenAI or Anthropic as LLM backends instead of local stubs.

### Storage Backends

Optional cache and storage backend support:

```bash
pip install "mlsdm-governed-cognitive-memory[storage]"
```

**Packages:**
- `redis` ≥5.0.0, <6.0.0

**Use case:** Distributed caching with Redis instead of in-memory cache.

### Authentication

Optional JWT/OIDC authentication support:

```bash
pip install "mlsdm-governed-cognitive-memory[auth]"
```

**Packages:**
- `pyjwt` ≥2.8.0, <3.0.0

**Use case:** OIDC token validation for secure API endpoints.

### Embeddings

Optional semantic embeddings with sentence-transformers:

```bash
pip install "mlsdm-governed-cognitive-memory[embeddings]"
```

**Packages:**
- `sentence-transformers` ≥3.0.0, <4.0.0

**Use case:** Real semantic embeddings instead of stub embeddings. Note: Large dependency with ML models.

### Testing

Test framework and tools:

```bash
pip install "mlsdm-governed-cognitive-memory[test]"
```

**Packages:**
- `pytest` ≥8.0.0, <9.0.0
- `pytest-asyncio` ≥0.23.0, <1.0.0
- `pytest-cov` ≥4.1.0, <5.0.0
- `hypothesis` ≥6.98.3, <7.0.0
- `httpx` ≥0.27.0, <1.0.0

**Use case:** Running the test suite.

### Development Tools

Linting, type checking, and code quality tools:

```bash
pip install "mlsdm-governed-cognitive-memory[dev]"
```

**Packages:**
- `ruff` ≥0.4.10, <1.0.0 - Fast Python linter and formatter
- `mypy` ≥1.10.0, <2.0.0 - Static type checker
- `types-PyYAML` ≥6.0.0, <7.0.0 - Type stubs for PyYAML
- `types-requests` ≥2.31.0, <3.0.0 - Type stubs for requests

**Use case:** Development environment with code quality tools.

### Performance Testing

Load and performance testing tools:

```bash
pip install "mlsdm-governed-cognitive-memory[profiling]"
```

**Packages:**
- `locust` ≥2.29.1, <3.0.0

**Use case:** Running load tests and performance benchmarks.

### Security Auditing

Dependency vulnerability scanning and analysis:

```bash
pip install "mlsdm-governed-cognitive-memory[security-audit]"
```

**Packages:**
- `pip-audit` ≥2.6.0, <3.0.0 - Vulnerability scanner
- `deptry` ≥0.12.0, <1.0.0 - Dependency analyzer

**Use case:** Security audits and dependency health checks.

### Documentation

Documentation generation tools:

```bash
pip install "mlsdm-governed-cognitive-memory[docs]"
```

**Packages:**
- `sphinx` ≥7.0.0, <8.0.0
- `sphinx-rtd-theme` ≥2.0.0, <3.0.0

**Use case:** Building documentation.

### Visualization

Data visualization and analysis tools:

```bash
pip install "mlsdm-governed-cognitive-memory[visualization]"
```

**Packages:**
- `matplotlib` ≥3.8.4, <4.0.0
- `jupyter` ≥1.0.0, <2.0.0

**Use case:** Creating plots, graphs, and running notebooks for analysis.

### Examples

Dependencies needed to run example scripts:

```bash
pip install "mlsdm-governed-cognitive-memory[examples]"
```

**Packages:**
- `matplotlib` ≥3.8.4, <4.0.0

**Use case:** Running example scripts and demos.

### Complete Development Environment

Install all development tools and test dependencies:

```bash
pip install "mlsdm-governed-cognitive-memory[all-dev]"
```

This meta-extra includes: test, dev, profiling, and security-audit dependencies.

## Installation Scenarios

### Scenario 1: Library Usage Only

Minimal installation for using MLSDM as a library:

```bash
pip install mlsdm-governed-cognitive-memory
```

### Scenario 2: Production Deployment

Production deployment with observability:

```bash
pip install "mlsdm-governed-cognitive-memory[observability]"
```

With additional providers and storage:

```bash
pip install "mlsdm-governed-cognitive-memory[observability,llm-providers,storage,auth]"
```

### Scenario 3: Full Development Environment

Complete development setup with all tools:

```bash
# Clone the repository
git clone https://github.com/neuron7x/mlsdm.git
cd mlsdm

# Install in editable mode with all dev dependencies
pip install -e ".[all-dev,observability]"
```

Or using the provided requirements.txt:

```bash
pip install -r requirements.txt
```

### Scenario 4: Neural Language Processing Development

Development with NeuroLang extension:

```bash
pip install -e ".[all-dev,neurolang,observability]"
```

Or using the NeuroLang requirements file:

```bash
pip install -r requirements.txt
pip install -r requirements-neurolang.txt
```

## Development Environment

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/neuron7x/mlsdm.git
   cd mlsdm
   ```

2. **Create a virtual environment:**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[all-dev,observability]"
   ```

4. **Verify installation:**
   ```bash
   pip check
   pytest --collect-only
   ```

### Development Workflow Commands

**Linting and formatting:**
```bash
ruff check src tests
ruff format src tests
```

**Type checking:**
```bash
mypy src/mlsdm
```

**Running tests:**
```bash
# Run all tests except load tests
pytest -q --ignore=tests/load

# Run only unit tests
pytest tests/unit -v

# Run with coverage
pytest --cov=src --cov-report=html
```

**Dependency auditing:**
```bash
# Check for vulnerabilities
pip-audit

# Check for unused/missing dependencies
deptry src
```

## Security Considerations

### Security Pins

The `requirements.txt` file includes security pins for transitive dependencies with known vulnerabilities:

```
certifi>=2024.7.4
cryptography>=43.0.1
jinja2>=3.1.6
urllib3>=2.2.2
setuptools>=78.1.1
idna>=3.7
```

These pins ensure that installations use secure versions even if transitive dependencies specify older versions.

### Vulnerability Scanning

Regular vulnerability scanning is recommended:

```bash
# Install security audit tools
pip install ".[security-audit]"

# Run pip-audit
pip-audit --strict

# Check dependency health
deptry src
```

### Best Practices

1. **Pin versions in production**: Use exact versions or narrow ranges for production deployments
2. **Regular updates**: Keep dependencies updated, especially security patches
3. **Audit before deployment**: Run `pip-audit` before deploying to production
4. **Minimal dependencies**: Only install extras that are actually needed
5. **Review transitive dependencies**: Use `pip list` to review all installed packages

## Dependency Auditing

### Using deptry

`deptry` checks for:
- Missing dependencies (imported but not declared)
- Unused dependencies (declared but not imported)
- Transitive dependencies (imported but only available transitively)

Configuration is in `pyproject.toml` under `[tool.deptry]`.

**Run deptry:**
```bash
deptry src
```

### Using pip-audit

`pip-audit` scans for known vulnerabilities in installed packages:

```bash
# Basic scan
pip-audit

# Strict mode (fail on any vulnerability)
pip-audit --strict

# Scan without spinner (for CI)
pip-audit --progress-spinner=off
```

## Troubleshooting

### Common Issues

**Issue: Import errors after installation**

Solution: Ensure you installed the correct extras:
```bash
# Check what's installed
pip list

# Install missing extras
pip install ".[test,observability]"
```

**Issue: Dependency conflicts**

Solution: Check for conflicts and resolve:
```bash
pip check

# If conflicts exist, try upgrading
pip install --upgrade -e ".[all-dev]"
```

**Issue: PyTorch installation issues**

PyTorch is large and platform-specific. For CPU-only installation:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Issue: Tests fail with missing dependencies**

Some tests require specific extras. Install test dependencies:
```bash
pip install ".[test,observability]"
```

### Environment Verification

Verify your environment is correctly set up:

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Verify no broken dependencies
pip check

# Test import
python -c "import mlsdm; print(mlsdm.__version__)"

# Run basic test
pytest tests/unit/test_config.py -v
```

## Additional Resources

- **Main README**: [README.md](../README.md)
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **API Reference**: [API_REFERENCE.md](../API_REFERENCE.md)
- **Security Policy**: [SECURITY_POLICY.md](../SECURITY_POLICY.md)
- **Testing Guide**: [TESTING_GUIDE.md](../TESTING_GUIDE.md)

## Questions or Issues?

If you encounter dependency-related issues:

1. Check this documentation first
2. Review closed issues on GitHub: https://github.com/neuron7x/mlsdm/issues
3. Open a new issue with:
   - Output of `pip list`
   - Output of `pip check`
   - Error messages and tracebacks
   - Python version and OS
