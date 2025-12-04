<div align="center">

# 🧠 MLSDM

### Multi-Level Synaptic Dynamic Memory

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/mlsdm-hero.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/mlsdm-hero.svg">
  <img src="assets/mlsdm-hero.svg" alt="MLSDM Neural Architecture Visualization" width="100%" style="max-width: 1200px;">
</picture>

**A cognitive wrapper for LLMs with memory bounds, moral filtering, and wake/sleep cycles**

[![CI](https://img.shields.io/github/actions/workflow/status/neuron7x/mlsdm/ci-neuro-cognitive-engine.yml?style=for-the-badge&logo=github-actions&logoColor=white&label=CI)](https://github.com/neuron7x/mlsdm/actions/workflows/ci-neuro-cognitive-engine.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/neuron7x/mlsdm/property-tests.yml?style=for-the-badge&logo=pytest&logoColor=white&label=Tests)](https://github.com/neuron7x/mlsdm/actions/workflows/property-tests.yml)
[![Python](https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-orange?style=for-the-badge)](CHANGELOG.md)

[Quick Start](#-quick-start) •
[Public API](#-public-api) •
[Documentation](#-documentation) •
[Contributing](#-contributing)

</div>

---

## What is MLSDM?

**MLSDM** wraps any LLM with a cognitive layer that enforces:

- **Fixed memory footprint** (~30 MB, pre-allocated)
- **Adaptive moral filtering** (EMA-based threshold adjustment)
- **Wake/sleep cycles** (8 wake + 3 sleep steps by default)

It is designed for applications where you need bounded resource usage and content filtering without RLHF.

> **Status:** Beta. The core API is stable, but breaking changes may occur before v2.0.

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/neuron7x/mlsdm.git
cd mlsdm
pip install -r requirements.txt
```

### Minimal Example

```python
from mlsdm import NeuroCognitiveClient

# Create client (uses local stub backend by default)
client = NeuroCognitiveClient(backend="local_stub")

# Generate a governed response
result = client.generate("Hello, world!")
print(result["response"])
```

### Using the LLM Wrapper Directly

```python
from mlsdm import create_llm_wrapper

# Create wrapper with defaults
wrapper = create_llm_wrapper()

# Generate with moral value (0.0-1.0)
result = wrapper.generate(prompt="Explain AI safety", moral_value=0.8)

if result["accepted"]:
    print(result["response"])
else:
    print(f"Rejected: {result['note']}")
```

---

## 📦 Public API

The minimal public API consists of:

| Export | Description |
|--------|-------------|
| `NeuroCognitiveClient` | SDK client for generating governed responses |
| `create_llm_wrapper` | Factory for creating LLMWrapper instances |
| `create_neuro_engine` | Factory for creating NeuroCognitiveEngine instances |
| `__version__` | Package version string |

### Python SDK

```python
from mlsdm import NeuroCognitiveClient

client = NeuroCognitiveClient(backend="local_stub")
result = client.generate("Your prompt here")
```

See [SDK_USAGE.md](SDK_USAGE.md) for complete SDK documentation.

### HTTP API

Start the server:

```bash
python -m mlsdm.cli serve --port 8000
```

Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/health/ready` | GET | Readiness probe |
| `/generate` | POST | Generate governed response |
| `/infer` | POST | Extended inference with options |

See [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation.

### CLI

```bash
# Show info
python -m mlsdm.cli info

# Interactive demo
python -m mlsdm.cli demo --interactive

# Start server
python -m mlsdm.cli serve --port 8000
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [API_REFERENCE.md](API_REFERENCE.md) | HTTP API and Python API reference |
| [SDK_USAGE.md](SDK_USAGE.md) | SDK client usage guide |
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | Integration patterns |
| [USAGE_GUIDE.md](USAGE_GUIDE.md) | Detailed usage examples |
| [ARCHITECTURE_SPEC.md](ARCHITECTURE_SPEC.md) | System architecture |
| [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | Testing approach |

For the complete documentation index, see [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md).

---
## Architecture Overview

```text
┌─────────────────────────┐
│      Your LLM           │
│  (OpenAI, Anthropic,    │
│   Local, Custom...)     │
└───────────┬─────────────┘
            │
    ┌───────▼───────┐
    │    MLSDM      │
    │   Wrapper     │
    │               │
    │ • Memory      │
    │ • Moral       │
    │ • Rhythm      │
    └───────┬───────┘
            │
    ┌───────▼───────┐
    │   Governed    │
    │   Response    │
    └───────────────┘
```

See [ARCHITECTURE_SPEC.md](ARCHITECTURE_SPEC.md) for details.

---

## Known Limitations

- **No hallucination prevention** — wraps LLM but cannot improve factual accuracy
- **Imperfect moral filtering** — some content may pass or be incorrectly rejected
- **Beta status** — core API is stable but breaking changes may occur

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

```bash
# Run tests
pytest tests/ -v

# Check linting  
ruff check src/
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

[↑ Back to Top](#-mlsdm)

</div>
