# Getting Started with MLSDM

**15-minute onboarding guide to get MLSDM running and verified.**

**Last Updated**: 2025-12-28  
**Version**: 1.2.0

---

## Prerequisites

### Required

- **Python 3.10 or higher** (Python 3.11/3.12 recommended)
- **uv** (fast Python package manager) - preferred for development
  - Install: `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Git** for version control

### OS Notes

- **Linux/macOS**: Fully supported, recommended for production
- **Windows**: Supported via WSL2 (Windows Subsystem for Linux)
  - Native Windows: Works but not optimized for production

### Hardware

- **RAM**: Minimum 2GB available, 4GB+ recommended
- **CPU**: Any modern multi-core CPU
- **Disk**: ~500MB for dependencies + evidence snapshots

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/neuron7x/mlsdm.git
cd mlsdm
```

### Step 2: Install Dependencies (Canonical)

**Using uv (recommended for development)**:

```bash
# Install all dependencies from uv.lock
make sync
# or directly: uv sync
```

**Using pip (alternative)**:

```bash
# Install core dependencies only
pip install -e .

# OR install with all development tools
pip install -e ".[dev]"
```

**Verify installation**:

```bash
python -c "import mlsdm; print(mlsdm.__version__)"
# Expected output: 1.2.0 or similar
```

---

## Quick Verification

Run these commands to verify your installation:

### 1. Readiness Check

```bash
python scripts/readiness_check.py
```

**Expected output**: `✓ Readiness check passed` (or instructions on what to update)

### 2. Unit Tests (Fast)

```bash
make test-fast
# or directly: pytest tests/unit tests/state -m "not slow and not comprehensive" -q --tb=short
```

**Expected output**: All tests pass in <30 seconds

### 3. Evidence Snapshot (Optional)

Generate a complete evidence snapshot to verify full setup:

```bash
make evidence
```

This creates `artifacts/evidence/<date>/<sha>/` with:
- Coverage report
- Test results
- Benchmark metrics
- Memory footprint

**Verify the snapshot**:

```bash
make verify-metrics
# or directly: python scripts/evidence/verify_evidence_snapshot.py --evidence-dir <path>
```

---

## Canonical Run Entrypoints

MLSDM provides multiple entrypoints for different use cases:

### 1. Development Server (Hot Reload)

```bash
make run-dev
# or directly: python -m mlsdm.entrypoints.dev
```

**Use for**: Local development with debug logging and hot reload
**Port**: 8000 (default)
**Workers**: 1 (single-threaded for debugging)

### 2. Production Server (Multi-Worker)

```bash
make run-cloud-local
# or directly: python -m mlsdm.entrypoints.cloud
```

**Use for**: Local production-like testing with multiple workers
**Port**: 8000 (default)
**Workers**: Multiple (CPU-based)

### 3. Agent/API Server (LLM Integration)

```bash
make run-agent
# or directly: python -m mlsdm.entrypoints.agent
```

**Use for**: Agent workflows and LLM integration endpoints
**Port**: 8000 (default)

### 4. Health Check Utility

```bash
make health-check
# or directly: python -m mlsdm.entrypoints.health
```

**Use for**: Quick health verification (exits with status code)

### 5. CLI Tool

```bash
mlsdm --help
# or: python -m mlsdm.cli --help
```

**Use for**: Command-line operations (if installed with `pip install -e .`)

### Docker Container (Neuro Engine Service)

```bash
# Build
make docker-build-neuro-engine

# Run
make docker-run-neuro-engine

# Smoke test
make docker-smoke-neuro-engine
```

**See**: [Dockerfile.neuro-engine-service](../Dockerfile.neuro-engine-service)

---

## Your First MLSDM Wrapper (Python Code)

Create a file called `my_first_wrapper.py`:

```python
from mlsdm.core.llm_wrapper import LLMWrapper
import numpy as np

# 1. Define a simple LLM function (replace with your actual LLM)
def my_llm(prompt: str, max_tokens: int) -> str:
    """Simple stub LLM for testing - replace with OpenAI, Anthropic, etc."""
    return f"Echo: {prompt[:50]}..."

# 2. Define an embedding function (replace with your actual embedder)
def my_embedder(text: str) -> np.ndarray:
    """Simple stub embedder - replace with sentence-transformers, OpenAI, etc."""
    # For testing, return random embeddings
    # In production, use: sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
    return np.random.randn(384).astype(np.float32)

# 3. Create the governed wrapper
wrapper = LLMWrapper(
    llm_generate_fn=my_llm,
    embedding_fn=my_embedder,
    dim=384,                        # Embedding dimension (must match your embedder)
    capacity=20_000,                # Memory capacity
    wake_duration=8,                # Wake phase steps
    sleep_duration=3,               # Sleep phase steps
    initial_moral_threshold=0.50    # Starting moral threshold
)

# 4. Generate with governance
result = wrapper.generate(
    prompt="Explain the benefits of cognitive governance",
    moral_value=0.8  # Higher value = more stringent moral filtering
)

# 5. View the results
print(f"✓ Response: {result['response']}")
print(f"✓ Accepted: {result['accepted']}")
print(f"✓ Current Phase: {result['phase']}")
print(f"✓ Moral Threshold: {result['moral_threshold']:.2f}")
```

Run it:

```bash
python my_first_wrapper.py
```

## Using Real LLMs

### With OpenAI

```python
from openai import OpenAI
from mlsdm.core.llm_wrapper import LLMWrapper
import numpy as np

client = OpenAI(api_key="your-api-key")

def openai_generate(prompt: str, max_tokens: int) -> str:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def openai_embed(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

wrapper = LLMWrapper(
    llm_generate_fn=openai_generate,
    embedding_fn=openai_embed,
    dim=1536  # Ada embedding dimension
)
```

### With Local Models (Hugging Face)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer
from mlsdm.core.llm_wrapper import LLMWrapper
import numpy as np

# Load local models
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def local_generate(prompt: str, max_tokens: int) -> str:
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=max_tokens)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def local_embed(text: str) -> np.ndarray:
    return embedder.encode(text).astype(np.float32)

wrapper = LLMWrapper(
    llm_generate_fn=local_generate,
    embedding_fn=local_embed,
    dim=384
)
```

## Running Tests

Verify your installation works:

```bash
# Run a simple test
pytest tests/unit/test_llm_wrapper.py -v

# Run all tests (may take several minutes)
pytest tests/ -v
```

## Common Configuration Options

### Disable Rate Limiting (for development)

```bash
export DISABLE_RATE_LIMIT=1
```

### Configure Memory Capacity

```python
wrapper = LLMWrapper(
    llm_generate_fn=my_llm,
    embedding_fn=my_embedder,
    dim=384,
    capacity=50_000,  # Increase memory capacity
)
```

### Adjust Moral Filtering

```python
# More permissive (threshold range: 0.30 - 0.90)
wrapper = LLMWrapper(
    llm_generate_fn=my_llm,
    embedding_fn=my_embedder,
    dim=384,
    initial_moral_threshold=0.35  # Lower = more permissive
)
```

## Optional Features

### OpenTelemetry Distributed Tracing

If you want distributed tracing capabilities, install the observability extras:

```bash
pip install ".[observability]"
# OR
pip install opentelemetry-api opentelemetry-sdk
```

Then configure tracing:

```python
import os
os.environ["OTEL_EXPORTER_TYPE"] = "console"  # or "otlp" for production
os.environ["OTEL_SERVICE_NAME"] = "my-mlsdm-app"
```

**Note:** If OpenTelemetry is not installed, MLSDM will work perfectly fine without it - tracing will simply be disabled.

### Aphasia Detection (Speech Quality)

For speech quality detection and repair, install the neurolang extension:

```bash
pip install -r requirements-neurolang.txt
```

Then use `NeuroLangWrapper` instead of `LLMWrapper`:

```python
from mlsdm.extensions.neuro_lang_extension import NeuroLangWrapper

wrapper = NeuroLangWrapper(
    llm_generate_fn=my_llm,
    embedding_fn=my_embedder,
    dim=384
)
```

## Running as a Service

Start MLSDM as a FastAPI service:

```bash
# Development mode (with hot reload)
python -m mlsdm.entrypoints.dev

# OR use make
make run-dev
```

Then access the API at `http://localhost:8000`:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world", "moral_value": 0.8}'
```

## Additional Development Commands

### Testing & Quality

```bash
# Run all tests
make test

# Run fast unit tests only (< 30 seconds)
make test-fast

# Run with coverage report
make cov

# Run coverage gate (CI threshold: 75%)
make coverage-gate

# Run linter
make lint

# Run type checker
make type
```

### Performance & Benchmarks

```bash
# Run performance benchmarks
make bench

# Check benchmark drift against baseline
make bench-drift
```

### Evaluation Suites

```bash
# Moral filter evaluation
make eval-moral_filter

# Observability tests
make test-memory-obs
```

### Package Building

```bash
# Build wheel and sdist
make build-package

# Test package installation
make test-package
```

---

## Next Steps

Now that you have MLSDM running:

1. **Understand the Architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
2. **Configure the System**: See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for configuration options
3. **Explore the API**: Check [API_REFERENCE.md](API_REFERENCE.md) for HTTP endpoints
4. **Review Evaluation Criteria**: See [EVALUATION.md](EVALUATION.md) for quality measures
5. **Contribute**: Read [CONTRIBUTING.md](../CONTRIBUTING.md) for development workflow

---

## Common Issues & Solutions

### Import Error: No module named 'opentelemetry'

**Solution**: OpenTelemetry is optional. Either install it with `pip install ".[observability]"` or ignore it - MLSDM will work without tracing.

### Import Error: No module named 'sentence_transformers'

**Solution**: Install sentence-transformers: `pip install sentence-transformers`

### Rate Limit Errors in Development

**Solution**: Disable rate limiting: `export DISABLE_RATE_LIMIT=1`

### Readiness Check Fails

**Solution**: If you modified code/tests/config/workflows, update `docs/status/READINESS.md`:
```bash
make readiness-preview TITLE="Your change description"
make readiness-apply TITLE="Your change description"
```

---

## Getting Help

- **Documentation Index**: [docs/README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/neuron7x/mlsdm/issues)
- **Contributing Guide**: [../CONTRIBUTING.md](../CONTRIBUTING.md)
- **Runbook**: [RUNBOOK.md](RUNBOOK.md) for troubleshooting

---

**Navigation**: [← Back to Documentation Index](README.md)
