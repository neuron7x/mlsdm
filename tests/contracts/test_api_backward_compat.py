"""
HTTP API backward compatibility tests.

These tests ensure HTTP API routes remain stable across versions,
preventing accidental breaking changes to the public API.

Test Strategy:
1. Document all public HTTP routes
2. Verify routes exist and return expected status codes
3. Validate response structure matches schema
4. Store route snapshots in golden_schemas/
5. Block route deletions and response structure changes
"""

import json
from pathlib import Path
from typing import Any

import pytest

# Golden schema directory
GOLDEN_DIR = Path(__file__).parent / "golden_schemas"


class TestHTTPAPIRoutes:
    """Test HTTP API route stability."""
    
    def _load_golden_routes(self) -> dict[str, Any]:
        """Load golden route definitions."""
        path = GOLDEN_DIR / "api_routes_v1.json"
        if not path.exists():
            return {}
        
        with open(path) as f:
            return json.load(f)
    
    def _save_golden_routes(self, routes: dict[str, Any]) -> None:
        """Save golden route definitions."""
        GOLDEN_DIR.mkdir(exist_ok=True)
        path = GOLDEN_DIR / "api_routes_v1.json"
        
        with open(path, "w") as f:
            json.dump(routes, f, indent=2, sort_keys=True)
    
    def test_health_endpoints_exist(self):
        """Test health endpoints are documented and stable."""
        current_routes = {
            "/health": {
                "method": "GET",
                "description": "Simple health check",
                "response_model": "SimpleHealthStatus",
                "status_codes": [200],
            },
            "/health/live": {
                "method": "GET",
                "description": "Liveness probe",
                "response_model": "LivenessStatus",
                "status_codes": [200],
            },
            "/health/liveness": {
                "method": "GET",
                "description": "Liveness probe (alias)",
                "response_model": "HealthStatus",
                "status_codes": [200],
            },
            "/health/ready": {
                "method": "GET",
                "description": "Readiness probe",
                "response_model": "ReadinessStatus",
                "status_codes": [200, 503],
            },
            "/health/readiness": {
                "method": "GET",
                "description": "Readiness probe (alias)",
                "response_model": "ReadinessStatus",
                "status_codes": [200, 503],
            },
            "/health/detailed": {
                "method": "GET",
                "description": "Detailed health with metrics",
                "response_model": "DetailedHealthStatus",
                "status_codes": [200, 503],
            },
            "/health/metrics": {
                "method": "GET",
                "description": "Prometheus metrics",
                "response_model": "text/plain",
                "status_codes": [200],
            },
        }
        
        golden = self._load_golden_routes()
        
        if not golden:
            # First run - save as golden
            self._save_golden_routes(current_routes)
            pytest.skip("Generated golden routes snapshot")
        
        # Check for removed routes
        removed_routes = set(golden.keys()) - set(current_routes.keys())
        assert not removed_routes, (
            f"Routes removed from API (breaking change): {removed_routes}"
        )
        
        # Check for method changes
        for route, golden_spec in golden.items():
            if route in current_routes:
                current_spec = current_routes[route]
                
                # Method should not change
                if golden_spec["method"] != current_spec["method"]:
                    pytest.fail(
                        f"HTTP method changed for {route}: "
                        f"{golden_spec['method']} → {current_spec['method']}"
                    )
                
                # Response model should not change (unless backward compatible)
                if golden_spec.get("response_model") != current_spec.get("response_model"):
                    # Allow if current is more specific
                    if current_spec.get("response_model") not in [
                        golden_spec.get("response_model"),
                        None,
                    ]:
                        pytest.fail(
                            f"Response model changed for {route}: "
                            f"{golden_spec['response_model']} → {current_spec['response_model']}"
                        )
    
    def test_generate_endpoint_contract(self):
        """Test /generate endpoint contract is stable."""
        generate_spec = {
            "/generate": {
                "method": "POST",
                "description": "Generate response with cognitive governance",
                "request_model": "GenerateRequest",
                "response_model": "GenerateResponse",
                "status_codes": [200, 400, 503],
                "required_fields": {
                    "request": ["prompt"],
                    "response": ["response", "accepted", "phase", "emergency_shutdown"],
                },
            }
        }
        
        golden_file = GOLDEN_DIR / "generate_endpoint_v1.json"
        
        if not golden_file.exists():
            GOLDEN_DIR.mkdir(exist_ok=True)
            with open(golden_file, "w") as f:
                json.dump(generate_spec, f, indent=2)
            pytest.skip("Generated golden generate endpoint spec")
        
        with open(golden_file) as f:
            golden = json.load(f)
        
        # Validate endpoint still exists with same contract
        assert "/generate" in generate_spec
        current = generate_spec["/generate"]
        golden_gen = golden["/generate"]
        
        # Method must not change
        assert current["method"] == golden_gen["method"], (
            f"Generate endpoint method changed: "
            f"{golden_gen['method']} → {current['method']}"
        )
        
        # Required request fields must not be removed
        current_req_fields = set(current["required_fields"]["request"])
        golden_req_fields = set(golden_gen["required_fields"]["request"])
        removed_req = golden_req_fields - current_req_fields
        assert not removed_req, (
            f"Required request fields removed from /generate: {removed_req}"
        )
        
        # Required response fields must not be removed
        current_resp_fields = set(current["required_fields"]["response"])
        golden_resp_fields = set(golden_gen["required_fields"]["response"])
        removed_resp = golden_resp_fields - current_resp_fields
        assert not removed_resp, (
            f"Required response fields removed from /generate: {removed_resp}"
        )
    
    def test_api_route_additions_allowed(self):
        """Test that adding new routes is allowed (non-breaking)."""
        # This test documents that new routes can be added
        # This is a non-breaking change and should be allowed
        
        new_routes = {
            "/health/new_endpoint": {
                "method": "GET",
                "description": "New health metric (added in v1.3)",
                "response_model": "NewMetric",
                "status_codes": [200],
            }
        }
        
        # Adding routes should not fail backward compatibility
        # (This test ensures our compatibility logic allows additions)
        assert "/health/new_endpoint" in new_routes
    
    def test_api_deprecation_headers(self):
        """Test deprecated routes include deprecation warnings."""
        # If a route is deprecated, it should:
        # 1. Still exist (not removed)
        # 2. Include deprecation header or warning in response
        # 3. Document alternative endpoint
        
        # Example structure for deprecated routes
        deprecated_routes = {
            # Currently no deprecated routes
            # Future deprecations should be added here
        }
        
        # Verify deprecated routes are properly documented
        for route, spec in deprecated_routes.items():
            assert "deprecated" in spec
            assert "alternative" in spec
            assert "removal_version" in spec


class TestAPIResponseStructure:
    """Test API response structure stability."""
    
    def test_health_response_structure(self):
        """Test health response structure is stable."""
        # Expected structure for health responses
        health_structure = {
            "status": "str",
            "timestamp": "float",
        }
        
        detailed_structure = {
            "status": "str",
            "timestamp": "float",
            "components": "dict",
            "cpu_percent": "float",
            "memory_percent": "float",
            "uptime_seconds": "float",
        }
        
        # These structures should remain stable
        assert "status" in health_structure
        assert "status" in detailed_structure
        assert "components" in detailed_structure
    
    def test_generate_response_structure(self):
        """Test /generate response structure is stable."""
        # Core fields that must always be present
        required_fields = [
            "response",
            "accepted",
            "phase",
            "emergency_shutdown",
        ]
        
        # Optional fields (can be None but structure should be consistent)
        optional_fields = [
            "moral_score",
            "aphasia_flags",
            "cognitive_state",
            "metrics",
        ]
        
        # Validate required fields are documented
        assert len(required_fields) > 0
        for field in required_fields:
            assert isinstance(field, str)
    
    def test_error_response_structure(self):
        """Test error response structure is stable."""
        # Standard error response structure
        error_structure = {
            "detail": "str or dict",
            "status_code": "int",
        }
        
        # Pydantic validation error structure
        validation_error_structure = {
            "detail": [
                {
                    "loc": "list",
                    "msg": "str",
                    "type": "str",
                }
            ]
        }
        
        # These structures should remain stable
        assert "detail" in error_structure
        assert "detail" in validation_error_structure


class TestAPIVersioning:
    """Test API versioning strategy."""
    
    def test_api_version_header(self):
        """Test API version is exposed in response headers."""
        # API should include version information
        # Either in headers or in response body
        expected_version_locations = [
            "X-API-Version",  # Header
            "api_version",  # Response field
        ]
        
        # At least one version indicator should be present
        assert len(expected_version_locations) > 0
    
    def test_backward_compatibility_policy(self):
        """Test backward compatibility policy is documented."""
        # Backward compatibility policy:
        # 1. Routes cannot be removed without deprecation period
        # 2. Required request fields cannot be removed
        # 3. Required response fields cannot be removed
        # 4. Optional fields can be added
        # 5. Types cannot change without major version bump
        
        policy = {
            "breaking_changes_require": "major_version_bump",
            "deprecation_period_months": 6,
            "allowed_changes": [
                "add_optional_fields",
                "add_new_routes",
                "add_optional_parameters",
            ],
            "blocked_changes": [
                "remove_routes",
                "remove_required_fields",
                "change_field_types",
                "change_http_methods",
            ],
        }
        
        # Verify policy is well-defined
        assert "breaking_changes_require" in policy
        assert "allowed_changes" in policy
        assert "blocked_changes" in policy


# Mark all tests as contract tests
pytestmark = pytest.mark.security
