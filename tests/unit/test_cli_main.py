from __future__ import annotations

import json
import logging
import runpy
from types import SimpleNamespace

import pytest

import importlib

import mlsdm.cli as cli_package


@pytest.fixture()
def cli_main_module():
    package_main = cli_package.main
    module = importlib.import_module("mlsdm.cli.main")
    yield module
    cli_package.main = package_main


def test_json_formatter_emits_expected_fields(cli_main_module) -> None:
    formatter = cli_main_module.JSONFormatter()
    record = logging.LogRecord(
        name="mlsdm.cli",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.module = "cli"

    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["message"] == "hello"
    assert payload["module"] == "cli"
    assert "timestamp" in payload


def test_main_runs_simulation(cli_main_module, monkeypatch) -> None:
    calls = {}

    class DummyManager:
        def __init__(self, config: object) -> None:
            calls["config"] = config

        def run_simulation(self, steps: int) -> None:
            calls["steps"] = steps

    monkeypatch.setattr(cli_main_module, "MemoryManager", DummyManager)
    monkeypatch.setattr(
        cli_main_module.ConfigLoader, "load_config", lambda _path: {"ok": True}
    )
    monkeypatch.setattr(
        cli_main_module, "logger", SimpleNamespace(info=lambda *_args, **_kwargs: None)
    )
    monkeypatch.setattr("sys.argv", ["mlsdm", "--config", "config/test.yaml", "--steps", "5"])

    cli_main_module.main()

    assert calls["config"] == {"ok": True}
    assert calls["steps"] == 5


def test_cli_module_entrypoint_exits_with_code(cli_main_module, monkeypatch) -> None:
    monkeypatch.setattr(cli_main_module, "main", lambda: 0)
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("mlsdm.cli.__main__", run_name="__main__")
    assert excinfo.value.code == 0
