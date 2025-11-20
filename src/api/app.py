from typing import List, Dict, Optional
import uuid

import logging
import os

import numpy as np
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
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


# Middleware for request correlation IDs
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests for traceability."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    # Add to logging context
    logger.info(f"Request started", extra={
        "correlation_id": correlation_id,
        "method": request.method,
        "path": request.url.path
    })
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    logger.info(f"Request completed", extra={
        "correlation_id": correlation_id,
        "status_code": response.status_code
    })
    
    return response


# Enhanced error response model
class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error: str
    message: str
    correlation_id: str
    details: Optional[Dict] = None


# Custom exception handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with correlation IDs."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            message=str(exc.detail),
            correlation_id=correlation_id,
            details={"status_code": exc.status_code}
        ).dict()
    )


# Generic exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with logging."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error(f"Unexpected error: {str(exc)}", extra={
        "correlation_id": correlation_id,
        "exception_type": type(exc).__name__
    })
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred",
            correlation_id=correlation_id,
            details={"exception_type": type(exc).__name__}
        ).dict()
    )


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


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    checks: Dict[str, str]
    correlation_id: str


@app.get("/health", response_model=HealthResponse)
async def health_shallow(request: Request) -> HealthResponse:
    """
    Shallow health check - fast response for load balancers.
    
    Returns basic service status without checking dependencies.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        checks={"api": "ok"},
        correlation_id=correlation_id
    )


@app.get("/health/deep", response_model=HealthResponse)
async def health_deep(request: Request) -> HealthResponse:
    """
    Deep health check - validates all system components.
    
    Checks:
    - Memory systems operational
    - Configuration loaded
    - Moral filter functional
    - Rhythm system active
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    checks = {
        "api": "ok",
        "memory_manager": "ok",
        "config": "ok"
    }
    
    try:
        # Check memory system
        L1, L2, L3 = _manager.memory.get_state()
        checks["memory_l1"] = "ok" if L1 is not None else "error"
        checks["memory_l2"] = "ok" if L2 is not None else "error"
        checks["memory_l3"] = "ok" if L3 is not None else "error"
        
        # Check moral filter
        threshold = _manager.filter.threshold
        checks["moral_filter"] = "ok" if 0.1 <= threshold <= 0.9 else "error"
        
        # Check rhythm
        phase = _manager.rhythm.get_current_phase()
        checks["rhythm"] = "ok" if phase in ["wake", "sleep"] else "error"
        
        # Determine overall status
        status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
        
        return HealthResponse(
            status=status,
            version="1.0.0",
            checks=checks,
            correlation_id=correlation_id
        )
        
    except Exception as e:
        logger.error(f"Deep health check failed: {str(e)}", extra={
            "correlation_id": correlation_id
        })
        
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            checks={**checks, "error": str(e)},
            correlation_id=correlation_id
        )
