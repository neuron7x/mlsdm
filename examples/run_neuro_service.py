#!/usr/bin/env python3
"""
EXAMPLE ONLY: Run NeuroCognitiveEngine HTTP API Service.

╔══════════════════════════════════════════════════════════════════════╗
║  This is an EXAMPLE script demonstrating direct use of serve().     ║
║  For production or normal usage, use the canonical CLI:             ║
║                                                                      ║
║      mlsdm serve --port 8000                                        ║
║      mlsdm serve --config config/production.yaml --backend openai   ║
║                                                                      ║
║  See 'mlsdm serve --help' for all options.                          ║
╚══════════════════════════════════════════════════════════════════════╝

This script demonstrates how to programmatically start the MLSDM HTTP server.
It is useful for:
- Understanding how the server is started
- Custom integrations that need to embed the server
- Development and testing scenarios

Usage:
    # Using local stub backend (default, no API key needed)
    python examples/run_neuro_service.py

    # Using OpenAI backend
    export OPENAI_API_KEY="sk-..."
    export LLM_BACKEND="openai"
    python examples/run_neuro_service.py

    # Custom host and port
    export HOST="127.0.0.1"
    export PORT="8080"
    python examples/run_neuro_service.py

    # Disable FSLGS governance
    export ENABLE_FSLGS="false"
    python examples/run_neuro_service.py
"""

import os
import sys

if __name__ == "__main__":
    # Add src to path only when running as script
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from mlsdm.entrypoints.serve import serve

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  NOTE: This is an example script. For production, use:              ║")
    print("║        mlsdm serve --port 8000                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("🚀 Starting NeuroCognitiveEngine HTTP API Service...")
    print(f"   Backend: {os.environ.get('LLM_BACKEND', 'local_stub')}")
    print(f"   Host: {os.environ.get('HOST', '0.0.0.0')}")
    print(f"   Port: {os.environ.get('PORT', '8000')}")
    print(f"   FSLGS: {os.environ.get('ENABLE_FSLGS', 'true')}")
    print(f"   Metrics: {os.environ.get('ENABLE_METRICS', 'true')}")
    print()
    print("API endpoints:")
    print("  - POST http://localhost:8000/generate")
    print("  - POST http://localhost:8000/infer")
    print("  - GET  http://localhost:8000/health")
    print("  - GET  http://localhost:8000/health/metrics")
    print("  - GET  http://localhost:8000/docs (Swagger UI)")
    print()

    serve(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")))
