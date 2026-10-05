import json
import base64
from cryptography.fernet import Fernet
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import settings

def _get_fernet():
    # Generate a deterministic Fernet key from settings.ENCRYPTION_KEY (padded to 32 bytes)
    key_bytes = settings.ENCRYPTION_KEY.encode('utf-8').ljust(32, b'0')[:32]
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

def encrypt_token(token: str) -> str:
    if not token:
        return ""
    f = _get_fernet()
    return f.encrypt(token.encode('utf-8')).decode('utf-8')

def decrypt_token(token_encrypted: str) -> str:
    if not token_encrypted:
        return ""
    f = _get_fernet()
    return f.decrypt(token_encrypted.encode('utf-8')).decode('utf-8')

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email"
]

def get_google_oauth_flow(redirect_uri: str = None):
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID or "dummy-client-id.apps.googleusercontent.com",
            "client_secret": settings.GOOGLE_CLIENT_SECRET or "dummy-client-secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri or settings.GOOGLE_REDIRECT_URI
    )
    return flow

def credentials_from_dict(info: dict) -> Credentials:
    return Credentials(
        token=info.get("token"),
        refresh_token=info.get("refresh_token"),
        token_uri=info.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=info.get("client_id", settings.GOOGLE_CLIENT_ID),
        client_secret=info.get("client_secret", settings.GOOGLE_CLIENT_SECRET),
        scopes=info.get("scopes", SCOPES)
    )
