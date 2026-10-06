"""BROWSERBASE_* switches: 0/no/off disable, 1/yes/on enable, blank or unset keeps the documented default."""

import pytest

from plugins.browser.browserbase import provider as bb


class _Resp:
    status_code = 200

    def json(self):
        return {"id": "sess-1", "connectUrl": "wss://example.invalid"}


@pytest.fixture
def sent(monkeypatch):
    calls = []
    p = bb.BrowserbaseBrowserProvider()
    monkeypatch.setattr(p, "_get_config", lambda: {"api_key": "k", "project_id": "proj", "base_url": "https://bb.invalid"})
    monkeypatch.setattr(p, "_post_create", lambda url, headers, body: calls.append(dict(body)) or _Resp())
    monkeypatch.setattr(p, "_check_created", lambda response: None)
    for name in ("BROWSERBASE_PROXIES", "BROWSERBASE_ADVANCED_STEALTH", "BROWSERBASE_KEEP_ALIVE", "BROWSERBASE_SESSION_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)

    def create(**env):
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        result = p.create_session("task")
        return calls[-1], result["features"]
    return create


def test_defaults_when_unset(sent):
    body, features = sent()
    assert body.get("proxies") is True and body.get("keepAlive") is True
    assert "browserSettings" not in body
    assert features["proxies"] and features["keep_alive"] and not features["advanced_stealth"]


@pytest.mark.parametrize("raw", ["", "  "])
def test_blank_keeps_defaults(sent, raw):
    body, _ = sent(BROWSERBASE_PROXIES=raw, BROWSERBASE_KEEP_ALIVE=raw, BROWSERBASE_ADVANCED_STEALTH=raw)
    assert body.get("proxies") is True and body.get("keepAlive") is True
    assert "browserSettings" not in body


@pytest.mark.parametrize("raw", ["false", "0", "no", "off", "OFF"])
def test_falsy_values_disable(sent, raw):
    body, features = sent(BROWSERBASE_PROXIES=raw, BROWSERBASE_KEEP_ALIVE=raw)
    assert "proxies" not in body and "keepAlive" not in body
    assert not features["proxies"] and not features["keep_alive"]


@pytest.mark.parametrize("raw", ["true", "1", "yes", "on", " True "])
def test_truthy_values_enable_advanced_stealth(sent, raw):
    body, features = sent(BROWSERBASE_ADVANCED_STEALTH=raw)
    assert body.get("browserSettings") == {"advancedStealth": True}
    assert features["advanced_stealth"]
