import pytest

from app.config import settings
from app.services.auth import (
    decrypt_token,
    encrypt_token,
    get_google_oauth_flow,
    is_oauth_configured,
)


def test_oauth_configuration_validator():
    # Should detect dummy or empty credentials
    orig_id = settings.GOOGLE_CLIENT_ID
    orig_secret = settings.GOOGLE_CLIENT_SECRET
    try:
        settings.GOOGLE_CLIENT_ID = ""
        settings.GOOGLE_CLIENT_SECRET = ""
        assert is_oauth_configured() is False

        settings.GOOGLE_CLIENT_ID = "dummy-client-id.apps.googleusercontent.com"
        settings.GOOGLE_CLIENT_SECRET = "dummy-client-secret"
        assert is_oauth_configured() is False

        settings.GOOGLE_CLIENT_ID = "1234567890-validclientid.apps.googleusercontent.com"
        settings.GOOGLE_CLIENT_SECRET = "GOCSPX-validsecretkey123"
        assert is_oauth_configured() is True
    finally:
        settings.GOOGLE_CLIENT_ID = orig_id
        settings.GOOGLE_CLIENT_SECRET = orig_secret

def test_unconfigured_oauth_raises_clear_error():
    orig_id = settings.GOOGLE_CLIENT_ID
    orig_secret = settings.GOOGLE_CLIENT_SECRET
    try:
        settings.GOOGLE_CLIENT_ID = ""
        settings.GOOGLE_CLIENT_SECRET = ""
        with pytest.raises(ValueError) as excinfo:
            get_google_oauth_flow()
        assert "Google OAuth is not configured" in str(excinfo.value)
    finally:
        settings.GOOGLE_CLIENT_ID = orig_id
        settings.GOOGLE_CLIENT_SECRET = orig_secret

def test_token_encryption_and_decryption():
    sample_token = "ya29.a0AfH6SMD_SampleAccessToken_123456789"
    encrypted = encrypt_token(sample_token)
    assert encrypted != sample_token
    assert len(encrypted) > 20

    decrypted = decrypt_token(encrypted)
    assert decrypted == sample_token

def test_empty_token_encryption():
    assert encrypt_token("") == ""
    assert decrypt_token("") == ""
