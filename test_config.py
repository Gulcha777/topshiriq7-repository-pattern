from app.config import DEFAULT_DATABASE_URL, DEFAULT_REDIS_URL, get_settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///x.db")
    monkeypatch.setenv("REDIS_URL", "redis://example:6380/1")
    s = get_settings()
    assert (s.database_url, s.redis_url) == ("sqlite:///x.db", "redis://example:6380/1")


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    s = get_settings()
    assert (s.database_url, s.redis_url) == (DEFAULT_DATABASE_URL, DEFAULT_REDIS_URL)
