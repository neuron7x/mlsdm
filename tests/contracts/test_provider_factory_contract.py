from __future__ import annotations

import warnings

from mlsdm.adapters.llm_provider import LocalStubProvider
from mlsdm.adapters.provider_factory import build_multiple_providers_from_env


def test_provider_factory_warns_and_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("MULTI_LLM_BACKENDS", "invalid_backend")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        providers = build_multiple_providers_from_env()

    assert any("Failed to build provider" in str(w.message) for w in caught)
    assert "default" in providers
    assert isinstance(providers["default"], LocalStubProvider)
