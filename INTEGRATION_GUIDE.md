# MLSDM Integration Guide

**Version:** 1.2.0  
**Last Updated:** December 2025

This guide helps you integrate MLSDM into your application.

## Quick Start

### Installation

```bash
git clone https://github.com/neuron7x/mlsdm.git
cd mlsdm
pip install -r requirements.txt
```

### Minimal Integration

```python
from mlsdm import NeuroCognitiveClient

# Create client with default local stub backend
client = NeuroCognitiveClient(backend="local_stub")

# Generate governed response
result = client.generate("Tell me about machine learning")
print(result["response"])
```

---

## Python API Integration

### Option 1: SDK Client (Recommended)

```python
from mlsdm import NeuroCognitiveClient

# Local testing (no API key needed)
client = NeuroCognitiveClient(backend="local_stub")

# Or with OpenAI
client = NeuroCognitiveClient(
    backend="openai",
    api_key="sk-...",
    model="gpt-4"
)

result = client.generate(
    prompt="What is consciousness?",
    max_tokens=256,
    moral_value=0.7
)
print(result["response"])
```

### Option 2: Factory Functions

```python
from mlsdm import create_neuro_engine

# Create engine with defaults
engine = create_neuro_engine()

# Generate with parameters
result = engine.generate(
    prompt="Explain quantum computing",
    max_tokens=256,
    moral_value=0.8,
    user_intent="educational",
    context_top_k=5,
)

# Check result
if result["error"] is None:
    print(f"Response: {result['response']}")
else:
    print(f"Error: {result['error']}")
```

### Option 3: LLM Wrapper (For Custom LLMs)

For direct LLM integration with cognitive governance:

```python
from mlsdm import create_llm_wrapper
import numpy as np

# With custom LLM function
def my_llm(prompt: str, max_tokens: int) -> str:
    # Your LLM call here (OpenAI, Anthropic, local model, etc.)
    return "Generated response..."

def my_embedding(text: str) -> np.ndarray:
    # Your embedding function
    return np.random.randn(384).astype(np.float32)

wrapper = create_llm_wrapper(
    llm_generate_fn=my_llm,
    embedding_fn=my_embedding,
    dim=384,
    capacity=20_000,
    wake_duration=8,
    sleep_duration=3,
    initial_moral_threshold=0.5,
)

# Generate
result = wrapper.generate(
    prompt="Hello, how are you?",
    moral_value=0.9
)

if result["accepted"]:
    print(result["response"])
else:
    print(f"Rejected: {result['note']}")
```

---

## HTTP API Integration

### Starting the Server

```bash
# Using CLI
python -m mlsdm.cli serve --port 8000

# Or directly with uvicorn
uvicorn mlsdm.api.app:app --host 0.0.0.0 --port 8000
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/health/ready` | GET | Readiness probe |
| `/generate` | POST | Generate governed response |
| `/infer` | POST | Extended inference with options |

### Example: POST /generate

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
```

---

## CLI Usage

```bash
# Show info
python -m mlsdm.cli info

# Interactive demo
python -m mlsdm.cli demo --interactive

# Start server
python -m mlsdm.cli serve --port 8000

# Check environment
python -m mlsdm.cli check
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BACKEND` | `local_stub` | Backend: `local_stub`, `openai` |
| `OPENAI_API_KEY` | - | Required for OpenAI backend |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model name |
| `DISABLE_RATE_LIMIT` | - | Set to `1` to disable rate limiting |

---

## See Also

- [README.md](README.md) - Quick start
- [SDK_USAGE.md](SDK_USAGE.md) - SDK client usage
- [API_REFERENCE.md](API_REFERENCE.md) - Complete API reference
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Detailed usage examples

---

**Version:** 1.2.0 | **Updated:** December 2025
