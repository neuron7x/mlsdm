"""API integration tests."""
import pytest
from fastapi.testclient import TestClient
import numpy as np

# We'll import the app dynamically to avoid config loading issues
def get_test_app():
    """Get test app with mocked config."""
    import yaml
    from io import StringIO
    from src.manager import CognitiveMemoryManager
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    test_config = """
dimension: 10
strict_mode: false
multi_level_memory:
  lambda_l1: 0.50
  lambda_l2: 0.10
  lambda_l3: 0.01
  theta_l1: 1.2
  theta_l2: 2.5
  gating12: 0.45
  gating23: 0.30
moral_filter:
  threshold: 0.50
  adapt_rate: 0.05
  min_threshold: 0.30
  max_threshold: 0.90
cognitive_rhythm:
  wake_duration: 8
  sleep_duration: 3
"""
    
    config = yaml.safe_load(StringIO(test_config))
    manager = CognitiveMemoryManager(config)
    
    app = FastAPI(title="MLSDM Test")
    
    class EventInput(BaseModel):
        event_vector: list[float]
        moral_value: float
    
    @app.post("/v1/process")
    async def process(payload: EventInput):
        try:
            state = await manager.process_event(np.array(payload.event_vector), payload.moral_value)
            return state
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app

@pytest.fixture
def client():
    """Create test client."""
    app = get_test_app()
    return TestClient(app)

def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_process_valid_event(client):
    """Test processing a valid event."""
    event_vector = np.random.randn(10).tolist()
    response = client.post(
        "/v1/process",
        json={"event_vector": event_vector, "moral_value": 0.8}
    )
    assert response.status_code == 200
    data = response.json()
    assert "norms" in data
    assert "phase" in data
    assert "moral_threshold" in data
    assert "qilm_size" in data
    assert "metrics" in data
    assert data["metrics"]["total"] == 1
    assert data["metrics"]["accepted"] == 1

def test_process_low_moral_value(client):
    """Test processing event with low moral value."""
    event_vector = np.random.randn(10).tolist()
    response = client.post(
        "/v1/process",
        json={"event_vector": event_vector, "moral_value": 0.2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["latent"] >= 1

def test_process_dimension_mismatch(client):
    """Test processing event with wrong dimension."""
    event_vector = [1.0, 2.0]  # Wrong dimension
    response = client.post(
        "/v1/process",
        json={"event_vector": event_vector, "moral_value": 0.8}
    )
    assert response.status_code == 400
    assert "Dimension mismatch" in response.json()["detail"]

def test_process_multiple_events(client):
    """Test processing multiple events."""
    for i in range(5):
        event_vector = np.random.randn(10).tolist()
        moral_value = 0.5 + 0.1 * i
        response = client.post(
            "/v1/process",
            json={"event_vector": event_vector, "moral_value": moral_value}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["total"] == i + 1
