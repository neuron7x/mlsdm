# API Contract Testing for MLSDM

## Overview

This directory contains contract tests that ensure API backward compatibility across versions. Contract tests validate that schemas, routes, and response structures remain stable, preventing breaking changes.

**Goal**: Zero breaking changes to public APIs without major version bump.

## What is Contract Testing?

Contract testing validates:
1. **Schema Stability**: Pydantic model structure unchanged
2. **Route Stability**: HTTP endpoints remain accessible
3. **Response Structure**: Required fields always present
4. **Type Stability**: Field types don't change unexpectedly

## Test Categories

### 1. Pydantic Schema Compatibility (`test_pydantic_schema_compat.py`)

**Purpose**: Ensure Pydantic models maintain their structure.

**Models Tested**:
- `GenerateRequest` - `/generate` endpoint input
- `GenerateResponse` - `/generate` endpoint output
- `HealthResponse` - Health check responses
- `ReadinessResponse` - Readiness probe responses
- `CognitiveStateResponse` - Cognitive state snapshot
- `EngineResult` - Engine output contract
- `EngineTiming` - Performance timing model
- `EngineValidationStep` - Validation step results
- `EngineErrorInfo` - Error information model

**Golden Schemas**: Stored in `golden_schemas/` directory
- `generate_request_v1.json`
- `generate_response_v1.json`
- `health_response_v1.json`
- `engine_result_v1.json`
- etc.

**Breaking Changes Detected**:
- ❌ Removed required fields
- ❌ Changed field types
- ❌ Removed enum values
- ✅ Added optional fields (allowed)
- ✅ Added enum values (allowed)

### 2. EngineResult Contract Validation (`test_engine_result_compat.py`)

**Purpose**: Validate the primary engine output contract.

**EngineResult is Critical**: It's the return type for `NeuroCognitiveEngine.generate()`

**Tests**:
- Success case serialization/deserialization
- Error case handling
- Partial data handling (optional fields)
- `from_dict()` backward compatibility
- All nested models (Timing, ValidationStep, ErrorInfo)

### 3. HTTP API Backward Compatibility (`test_api_backward_compat.py`)

**Purpose**: Ensure HTTP routes remain stable.

**Routes Tested**:
- `GET /health` - Simple health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /health/detailed` - Detailed health
- `GET /health/metrics` - Prometheus metrics
- `POST /generate` - Generate endpoint

**Route Snapshot**: Stored in `golden_schemas/api_routes_v1.json`

**Breaking Changes Detected**:
- ❌ Removed routes
- ❌ Changed HTTP methods
- ❌ Changed response models
- ❌ Removed required fields
- ✅ Added new routes (allowed)
- ✅ Added optional fields (allowed)

## Golden Schema Generation

Golden schemas are generated automatically on first test run:

```bash
# First run - generates golden schemas
pytest tests/contracts/test_pydantic_schema_compat.py -v

# Subsequent runs - validates against golden
pytest tests/contracts/test_pydantic_schema_compat.py -v
```

**When to Regenerate**:
- **Never** unless making intentional breaking change
- Requires major version bump (1.x → 2.0)
- Requires deprecation notice and migration guide

## Running Contract Tests

### Run All Contract Tests
```bash
pytest tests/contracts/ -v
```

### Run Specific Test Category
```bash
# Schema compatibility
pytest tests/contracts/test_pydantic_schema_compat.py -v

# Engine contract
pytest tests/contracts/test_engine_result_compat.py -v

# API routes
pytest tests/contracts/test_api_backward_compat.py -v
```

### Run with Coverage
```bash
pytest tests/contracts/ --cov=src/mlsdm --cov-report=term
```

## CI Integration

Contract tests run on **every PR** as a **blocking check**:
- Prevents accidental breaking changes
- Fast execution (~10 seconds)
- Fails CI if breaking changes detected

Configured in `.github/workflows/ci-neuro-cognitive-engine.yml`:
```yaml
- name: Contract Tests
  run: pytest tests/contracts/ -v --strict-markers
```

## Backward Compatibility Policy

### Allowed Changes (Non-Breaking)
✅ Add optional fields to models
✅ Add new HTTP routes
✅ Add new enum values
✅ Add optional query parameters
✅ Expand valid value ranges (e.g., max_tokens: 2048 → 4096)

### Blocked Changes (Breaking)
❌ Remove required fields
❌ Remove HTTP routes
❌ Change field types (str → int)
❌ Remove enum values
❌ Change HTTP methods (GET → POST)
❌ Tighten validations (max_tokens: 4096 → 2048)

### Making Breaking Changes
If breaking change is necessary:
1. **Major version bump** (v1.x → v2.0)
2. **Deprecation period** (6 months minimum)
3. **Migration guide** in CHANGELOG.md
4. **Deprecation headers** in responses
5. **Update golden schemas** after version bump

## Schema Evolution Examples

### Safe Evolution (Non-Breaking)
```python
# Before
class GenerateRequest(BaseModel):
    prompt: str

# After (safe - added optional field)
class GenerateRequest(BaseModel):
    prompt: str
    temperature: float | None = None  # ✅ Optional field
```

### Unsafe Evolution (Breaking)
```python
# Before
class GenerateRequest(BaseModel):
    prompt: str

# After (breaking - removed field)
class GenerateRequest(BaseModel):
    # ❌ 'prompt' removed - would fail contract test
    input_text: str
```

## Troubleshooting

### Test Fails with "Breaking changes detected"
1. Review the specific change reported
2. Determine if change is intentional
3. If unintentional: revert the change
4. If intentional: follow breaking change process

### Golden Schema Mismatch
If golden schema is out of date (e.g., after git merge):
```bash
# Don't regenerate unless making breaking change!
# Instead, review the change and revert if unintentional

# Only regenerate if breaking change is approved:
rm tests/contracts/golden_schemas/*.json
pytest tests/contracts/test_pydantic_schema_compat.py -v
git add tests/contracts/golden_schemas/
```

### New Model Needs Contract Test
Add test to `test_pydantic_schema_compat.py`:
```python
def test_new_model_schema_compat(self):
    """Test NewModel schema backward compatibility."""
    current = self._get_model_schema(NewModel)
    
    try:
        golden = self._load_golden_schema("new_model_v1.json")
        issues = compare_schemas(current, golden)
        assert not issues, f"Breaking changes: {issues}"
    except pytest.skip.Exception:
        self._save_golden_schema(current, "new_model_v1.json")
        pytest.skip("Generated golden schema")
```

## References

- `docs/API_CONTRACT.md` - API contract documentation
- `docs/API_REFERENCE.md` - Full API reference
- `src/mlsdm/api/schemas.py` - API schema definitions
- `src/mlsdm/contracts/engine_models.py` - Engine contract models
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Consumer-Driven Contracts](https://martinfowler.com/articles/consumerDrivenContracts.html)

## Support

For questions about contract testing:
1. Review this README
2. Check existing contract tests for examples
3. Consult API_CONTRACT.md for policy
4. Open issue with `[contract-test]` tag
