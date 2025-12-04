"""
MLSDM Utility modules.

Provides common utilities for the MLSDM framework including:
- Bulkhead pattern for fault isolation
- Rate limiting
- Embedding cache for performance optimization
- Array pool for numpy array reuse
- Configuration management with caching
- Error handling
- Input validation
- Security logging
"""

from .array_pool import (
    ArrayPool,
    ArrayPoolConfig,
    ArrayPoolStats,
    clear_default_pool,
    get_default_pool,
)
from .bulkhead import (
    Bulkhead,
    BulkheadCompartment,
    BulkheadConfig,
    BulkheadFullError,
    BulkheadStats,
)
from .config_loader import (
    ConfigCache,
    ConfigLoader,
    get_config_cache,
)
from .embedding_cache import (
    EmbeddingCache,
    EmbeddingCacheConfig,
    EmbeddingCacheStats,
    clear_default_cache,
    get_default_cache,
)
from .rate_limiter import RateLimiter

__all__ = [
    # Array pool
    "ArrayPool",
    "ArrayPoolConfig",
    "ArrayPoolStats",
    "get_default_pool",
    "clear_default_pool",
    # Bulkhead pattern
    "Bulkhead",
    "BulkheadCompartment",
    "BulkheadConfig",
    "BulkheadFullError",
    "BulkheadStats",
    # Config loader
    "ConfigCache",
    "ConfigLoader",
    "get_config_cache",
    # Embedding cache
    "EmbeddingCache",
    "EmbeddingCacheConfig",
    "EmbeddingCacheStats",
    "get_default_cache",
    "clear_default_cache",
    # Rate limiting
    "RateLimiter",
]
