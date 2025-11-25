"""Benchmarks for NeuroCognitiveEngine performance testing.

This package contains performance benchmarks that measure:
- Pre-flight check latency (moral precheck)
- End-to-end latency under various loads
- Throughput (operations per second)
- Memory usage during benchmarks

Usage:
    # Run via CLI
    python benchmarks/test_neuro_engine_performance.py --help

    # Run via pytest
    pytest benchmarks/ -v -s -m benchmark

    # Run via Makefile
    make benchmark

See benchmarks/README.md for detailed documentation.
"""
