import base64
import logging

import httpx
from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

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
    try:
        f = _get_fernet()
        return f.decrypt(token_encrypted.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to decrypt OAuth token: {e}")
        return ""

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email"
]

def is_oauth_configured() -> bool:
    """
    Returns True only if valid non-empty, non-dummy Google OAuth credentials are provided.
    """
    cid = (settings.GOOGLE_CLIENT_ID or "").strip()
    csec = (settings.GOOGLE_CLIENT_SECRET or "").strip()
    if not cid or not csec:
        return False
    if "dummy" in cid.lower() or "dummy" in csec.lower():
        return False
    return True

def get_google_oauth_flow(redirect_uri: str = None):
    if not is_oauth_configured():
        raise ValueError(
            "Google OAuth is not configured. Real GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
            "must be supplied in the environment or secrets configuration."
        )
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID.strip(),
            "client_secret": settings.GOOGLE_CLIENT_SECRET.strip(),
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

async def get_valid_credentials(account, db: AsyncSession = None) -> Credentials | None:
    """
    Retrieves decrypted credentials for a ConnectedAccount, refreshing access token if expired.
    """
    if not account or not account.access_token_encrypted:
        return None

    access_token = decrypt_token(account.access_token_encrypted)
    refresh_token = decrypt_token(account.refresh_token_encrypted) if account.refresh_token_encrypted else None

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=account.token_uri or "https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            if db:
                account.access_token_encrypted = encrypt_token(creds.token)
                await db.commit()
            logger.info(f"Successfully refreshed Google OAuth token for {account.email}")
        except Exception as e:
            logger.error(f"Failed to refresh Google OAuth token for {account.email}: {e}")
            return None

    return creds

async def revoke_google_token(token: str) -> bool:
    if not token:
        return True
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": token},
                headers={"content-type": "application/x-www-form-urlencoded"}
            )
            return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Google token revocation request error: {e}")
        return False

