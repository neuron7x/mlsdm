from typing import List, Dict

import logging
import os

import numpy as np
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, validator, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.utils.config_loader import ConfigLoader
from src.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

# Rate limiting configuration (5 RPS per client as per threat model)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="mlsdm-governed-cognitive-memory", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

_config_path = os.getenv("CONFIG_PATH", "config/default_config.yaml")
_manager = MemoryManager(ConfigLoader.load_config(_config_path))


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    api_key = os.getenv("API_KEY")
    if api_key and token != api_key:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return token


class EventInput(BaseModel):
    event_vector: List[float] = Field(..., min_items=1, max_items=10000)
    moral_value: float = Field(..., ge=0.0, le=1.0)
    
    @validator('event_vector')
    def validate_vector(cls, v):
        """Validate vector values for NaN, Inf, and reasonable bounds."""
        if not v:
            raise ValueError("event_vector cannot be empty")
        
        arr = np.array(v, dtype=float)
        
        # Check for NaN or Inf
        if np.any(np.isnan(arr)):
            raise ValueError("event_vector contains NaN values")
        if np.any(np.isinf(arr)):
            raise ValueError("event_vector contains Inf values")
        
        # Check for reasonable magnitude to prevent adversarial inputs
        max_magnitude = 1000.0
        if np.any(np.abs(arr) > max_magnitude):
            raise ValueError(f"event_vector values must be within [-{max_magnitude}, {max_magnitude}]")
        
        return v


class StateResponse(BaseModel):
    L1_norm: float
    L2_norm: float
    L3_norm: float
    current_phase: str
    latent_events_count: int
    accepted_events_count: int
    total_events_processed: int
    moral_filter_threshold: float


@app.post("/v1/process_event/", response_model=StateResponse)
@limiter.limit("5/second")
async def process_event(request: Request, event: EventInput, user: str = Depends(get_current_user)) -> StateResponse:
    vec = np.array(event.event_vector, dtype=float)
    if vec.shape[0] != _manager.dimension:
        raise HTTPException(status_code=400, detail="Dimension mismatch.")
    await _manager.process_event(vec, event.moral_value)
    return await get_state(user)


@app.get("/v1/state/", response_model=StateResponse)
@limiter.limit("10/second")
async def get_state(request: Request, user: str = Depends(get_current_user)) -> StateResponse:
    L1, L2, L3 = _manager.memory.get_state()
    metrics = _manager.metrics_collector.get_metrics()
    return StateResponse(
        L1_norm=float(np.linalg.norm(L1)),
        L2_norm=float(np.linalg.norm(L2)),
        L3_norm=float(np.linalg.norm(L3)),
        current_phase=_manager.rhythm.get_current_phase(),
        latent_events_count=int(metrics["latent_events_count"]),
        accepted_events_count=int(metrics["accepted_events_count"]),
        total_events_processed=int(metrics["total_events_processed"]),
        moral_filter_threshold=float(_manager.filter.threshold),
    )


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy"}
