from types import SimpleNamespace

from scripts import security_audit


def _fake_run(stdout: str):
    return SimpleNamespace(stdout=stdout, returncode=0)


def test_check_pip_version_rejects_outdated(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return _fake_run("pip 24.0 from /usr/lib/python3/dist-packages/pip (python 3.12)")

    monkeypatch.setattr(security_audit.subprocess, "run", fake_run)

    ok, version = security_audit.check_pip_version(min_version="25.3")

    assert not ok
    assert version.startswith("24.0")


def test_check_pip_version_accepts_minimum(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return _fake_run("pip 25.3 from /usr/lib/python3/dist-packages/pip (python 3.12)")

    monkeypatch.setattr(security_audit.subprocess, "run", fake_run)

    ok, version = security_audit.check_pip_version(min_version="25.3")

    assert ok
    assert version.startswith("25.3")
