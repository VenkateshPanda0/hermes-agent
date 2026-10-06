"""A blank ``TERMINAL_CONTAINER_PERSISTENT=`` means "unset", so persistence stays at its default (on).

The terminal tool reads it through ``_tenv_bool`` which already treats blank as the default; doctor,
status and the gateway's docker-sandbox lookup must agree with it instead of reporting/acting as off."""

from types import SimpleNamespace

import pytest

from gateway.platforms import base
from hermes_cli import doctor_tools, status


@pytest.fixture
def vercel_ready(monkeypatch):
    monkeypatch.setenv("TERMINAL_VERCEL_RUNTIME", "node24")
    monkeypatch.delenv("TERMINAL_CONTAINER_DISK", raising=False)
    auth = SimpleNamespace(ok=True, label="token", detail_lines=[])
    monkeypatch.setattr(doctor_tools, "describe_vercel_auth", lambda: auth)
    monkeypatch.setattr(status, "describe_vercel_auth", lambda: auth)


@pytest.mark.parametrize("raw, persistent", [
    (None, True), ("", True), ("  ", True), ("on", True), ("YES", True), ("false", False), ("0", False), ("off", False),
])
def test_doctor_vercel_persistence(monkeypatch, capsys, vercel_ready, raw, persistent):
    if raw is None:
        monkeypatch.delenv("TERMINAL_CONTAINER_PERSISTENT", raising=False)
    else:
        monkeypatch.setenv("TERMINAL_CONTAINER_PERSISTENT", raw)
    doctor_tools._check_vercel_backend([])
    out = capsys.readouterr().out
    assert ("snapshot filesystem" in out) is persistent
    assert ("ephemeral filesystem" in out) is (not persistent)


@pytest.mark.parametrize("raw, cfg, persistent", [
    (None, True, True), (None, False, False), ("", True, True), ("", False, False), (" ", True, True),
    ("on", False, True), ("off", True, False),
])
def test_status_vercel_persistence(monkeypatch, capsys, vercel_ready, raw, cfg, persistent):
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    if raw is None:
        monkeypatch.delenv("TERMINAL_CONTAINER_PERSISTENT", raising=False)
    else:
        monkeypatch.setenv("TERMINAL_CONTAINER_PERSISTENT", raw)
    ctx = SimpleNamespace(config={"terminal": {"backend": "vercel_sandbox", "container_persistent": cfg}})
    status._render_terminal(ctx)
    out = capsys.readouterr().out
    assert ("snapshot filesystem" in out) is persistent


@pytest.mark.parametrize("raw, persistent", [
    ("", True), ("  ", True), ("true", True), ("on", True), ("false", False), ("0", False),
])
def test_gateway_docker_persistent_active(monkeypatch, raw, persistent):
    values = {"TERMINAL_ENV": "docker", "TERMINAL_CONTAINER_PERSISTENT": raw}
    monkeypatch.setattr(base, "_tenv", lambda name, default="": values.get(name, default))
    assert base._docker_persistent_active() is persistent
