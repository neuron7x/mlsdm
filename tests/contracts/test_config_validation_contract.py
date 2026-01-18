from __future__ import annotations

from mlsdm.utils.config_loader import ConfigLoader


def test_config_loader_validates_by_default(tmp_path) -> None:
    invalid_config = tmp_path / "invalid.yaml"
    invalid_config.write_text("unknown_key: 1\n", encoding="utf-8")

    try:
        ConfigLoader.load_config(str(invalid_config))
    except ValueError as exc:
        assert "unknown top-level keys" in str(exc)
    else:
        raise AssertionError("Expected config validation error for unknown_key")
