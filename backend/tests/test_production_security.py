"""Security regression tests for production-private data and OAuth CSRF."""

import httpx
import pytest

from app.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_production_denies_anonymous_private_data(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    private_routes = (
        "/api/products",
        "/api/suppliers",
        "/api/emails",
        "/api/catalogues",
        "/api/review",
        "/api/integrations/status",
        "/api/dashboard/stats",
        "/api/diagnostics",
        "/api/auth/disconnect",
        "/media/private.pdf",
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        for path in private_routes:
            result = await client.get(path)
            assert result.status_code == 401, path
        public_health = await client.get("/api/health")
        assert public_health.status_code == 200


@pytest.mark.asyncio
async def test_google_oauth_callback_rejects_unbound_state_before_token_exchange():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/auth/callback?code=fake&state=forged")
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid Google OAuth session state"


@pytest.mark.asyncio
async def test_production_rejects_default_encryption_secrets(monkeypatch):
    from app.main import lifespan

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(
        settings, "SESSION_SECRET", "kinetix-production-secret-key-32charsmin!"
    )
    with pytest.raises(RuntimeError, match="unique SESSION_SECRET"):
        async with lifespan(app):
            pass


@pytest.mark.asyncio
async def test_production_rejects_ephemeral_sqlite_database(monkeypatch):
    from app.main import lifespan

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "SESSION_SECRET", "test-session-" + "s" * 40)
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "test-encryption-" + "e" * 40)
    monkeypatch.setattr(
        settings, "DATABASE_URL", "sqlite+aiosqlite:///./nonpersistent.db"
    )
    with pytest.raises(RuntimeError, match="durable PostgreSQL"):
        async with lifespan(app):
            pass
