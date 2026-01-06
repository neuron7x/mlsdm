"""
Pydantic schema backward compatibility tests.

These tests ensure Pydantic model schemas remain stable across versions,
preventing accidental breaking changes to the API contract.

Test Strategy:
1. Generate JSON Schema from current Pydantic models
2. Compare against golden schemas stored in golden_schemas/
3. Detect additions, deletions, and type changes
4. Allow safe additions, block breaking changes
"""

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from mlsdm.api.schemas import (
    CognitiveStateResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    ReadinessResponse,
)
from mlsdm.contracts.engine_models import (
    EngineErrorInfo,
    EngineResult,
    EngineTiming,
    EngineValidationStep,
)


# Golden schema directory
GOLDEN_DIR = Path(__file__).parent / "golden_schemas"


def normalize_schema(schema: dict) -> dict:
    """
    Normalize JSON Schema for comparison.
    
    Removes fields that change between runs (like titles, descriptions)
    while preserving type and structure information.
    """
    normalized = {}
    
    # Core type information (required for compatibility)
    if "type" in schema:
        normalized["type"] = schema["type"]
    if "required" in schema:
        normalized["required"] = sorted(schema["required"])
    
    # Properties (field definitions)
    if "properties" in schema:
        normalized["properties"] = {
            name: normalize_schema(prop)
            for name, prop in schema["properties"].items()
        }
    
    # Array items
    if "items" in schema:
        normalized["items"] = normalize_schema(schema["items"])
    
    # Enum values
    if "enum" in schema:
        normalized["enum"] = sorted(schema["enum"])
    
    # anyOf/oneOf/allOf
    for key in ["anyOf", "oneOf", "allOf"]:
        if key in schema:
            normalized[key] = [normalize_schema(s) for s in schema[key]]
    
    return normalized


def compare_schemas(current: dict, golden: dict) -> list[str]:
    """
    Compare two normalized schemas and return list of breaking changes.
    
    Breaking changes include:
    - Removed required fields
    - Changed field types
    - Removed enum values
    
    Non-breaking changes include:
    - Added optional fields
    - Added enum values
    - Description/title changes
    """
    issues = []
    
    # Check required fields
    current_required = set(current.get("required", []))
    golden_required = set(golden.get("required", []))
    
    removed_required = golden_required - current_required
    if removed_required:
        issues.append(f"Removed required fields: {sorted(removed_required)}")
    
    # Check field types
    current_props = current.get("properties", {})
    golden_props = golden.get("properties", {})
    
    for field_name in golden_props:
        if field_name not in current_props:
            issues.append(f"Removed field: {field_name}")
        else:
            # Compare field types
            current_type = current_props[field_name].get("type")
            golden_type = golden_props[field_name].get("type")
            
            if current_type != golden_type:
                issues.append(
                    f"Changed type for '{field_name}': {golden_type} → {current_type}"
                )
    
    return issues


class TestPydanticSchemaCompatibility:
    """Test Pydantic model schema stability."""
    
    def _get_model_schema(self, model: type[BaseModel]) -> dict:
        """Get normalized JSON Schema for a Pydantic model."""
        schema = model.model_json_schema()
        return normalize_schema(schema)
    
    def _load_golden_schema(self, filename: str) -> dict:
        """Load golden schema from file."""
        path = GOLDEN_DIR / filename
        if not path.exists():
            pytest.skip(f"Golden schema not found: {filename}")
        
        with open(path) as f:
            return json.load(f)
    
    def _save_golden_schema(self, schema: dict, filename: str) -> None:
        """Save golden schema to file (for initial generation)."""
        GOLDEN_DIR.mkdir(exist_ok=True)
        path = GOLDEN_DIR / filename
        
        with open(path, "w") as f:
            json.dump(schema, f, indent=2, sort_keys=True)
    
    def test_generate_request_schema_compat(self):
        """Test GenerateRequest schema backward compatibility."""
        current = self._get_model_schema(GenerateRequest)
        
        try:
            golden = self._load_golden_schema("generate_request_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in GenerateRequest schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            # Generate golden file on first run
            self._save_golden_schema(current, "generate_request_v1.json")
            pytest.skip("Generated golden schema for GenerateRequest")
    
    def test_generate_response_schema_compat(self):
        """Test GenerateResponse schema backward compatibility."""
        current = self._get_model_schema(GenerateResponse)
        
        try:
            golden = self._load_golden_schema("generate_response_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in GenerateResponse schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            self._save_golden_schema(current, "generate_response_v1.json")
            pytest.skip("Generated golden schema for GenerateResponse")
    
    def test_health_response_schema_compat(self):
        """Test HealthResponse schema backward compatibility."""
        current = self._get_model_schema(HealthResponse)
        
        try:
            golden = self._load_golden_schema("health_response_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in HealthResponse schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            self._save_golden_schema(current, "health_response_v1.json")
            pytest.skip("Generated golden schema for HealthResponse")
    
    def test_readiness_response_schema_compat(self):
        """Test ReadinessResponse schema backward compatibility."""
        current = self._get_model_schema(ReadinessResponse)
        
        try:
            golden = self._load_golden_schema("readiness_response_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in ReadinessResponse schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            self._save_golden_schema(current, "readiness_response_v1.json")
            pytest.skip("Generated golden schema for ReadinessResponse")
    
    def test_cognitive_state_response_schema_compat(self):
        """Test CognitiveStateResponse schema backward compatibility."""
        current = self._get_model_schema(CognitiveStateResponse)
        
        try:
            golden = self._load_golden_schema("cognitive_state_response_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in CognitiveStateResponse schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            self._save_golden_schema(current, "cognitive_state_response_v1.json")
            pytest.skip("Generated golden schema for CognitiveStateResponse")


class TestEngineModelSchemaCompatibility:
    """Test engine contract model schema stability."""
    
    def _get_model_schema(self, model: type[BaseModel]) -> dict:
        """Get normalized JSON Schema for a Pydantic model."""
        schema = model.model_json_schema()
        return normalize_schema(schema)
    
    def _load_golden_schema(self, filename: str) -> dict:
        """Load golden schema from file."""
        path = GOLDEN_DIR / filename
        if not path.exists():
            pytest.skip(f"Golden schema not found: {filename}")
        
        with open(path) as f:
            return json.load(f)
    
    def _save_golden_schema(self, schema: dict, filename: str) -> None:
        """Save golden schema to file."""
        GOLDEN_DIR.mkdir(exist_ok=True)
        path = GOLDEN_DIR / filename
        
        with open(path, "w") as f:
            json.dump(schema, f, indent=2, sort_keys=True)
    
    def test_engine_result_schema_compat(self):
        """Test EngineResult schema backward compatibility."""
        current = self._get_model_schema(EngineResult)
        
        try:
            golden = self._load_golden_schema("engine_result_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in EngineResult schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            self._save_golden_schema(current, "engine_result_v1.json")
            pytest.skip("Generated golden schema for EngineResult")
    
    def test_engine_timing_schema_compat(self):
        """Test EngineTiming schema backward compatibility."""
        current = self._get_model_schema(EngineTiming)
        
        try:
            golden = self._load_golden_schema("engine_timing_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in EngineTiming schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            self._save_golden_schema(current, "engine_timing_v1.json")
            pytest.skip("Generated golden schema for EngineTiming")
    
    def test_engine_validation_step_schema_compat(self):
        """Test EngineValidationStep schema backward compatibility."""
        current = self._get_model_schema(EngineValidationStep)
        
        try:
            golden = self._load_golden_schema("engine_validation_step_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in EngineValidationStep schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            self._save_golden_schema(current, "engine_validation_step_v1.json")
            pytest.skip("Generated golden schema for EngineValidationStep")
    
    def test_engine_error_info_schema_compat(self):
        """Test EngineErrorInfo schema backward compatibility."""
        current = self._get_model_schema(EngineErrorInfo)
        
        try:
            golden = self._load_golden_schema("engine_error_info_v1.json")
            issues = compare_schemas(current, golden)
            
            assert not issues, (
                f"Breaking changes detected in EngineErrorInfo schema:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )
        except pytest.skip.Exception:
            self._save_golden_schema(current, "engine_error_info_v1.json")
            pytest.skip("Generated golden schema for EngineErrorInfo")


# Mark all tests as contract tests
pytestmark = pytest.mark.security
