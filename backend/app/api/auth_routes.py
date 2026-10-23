import hmac

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ConnectedAccount
from app.services.auth import (
    decrypt_token,
    encrypt_token,
    get_google_oauth_flow,
    is_oauth_configured,
    revoke_google_token,
)
from app.services.worker import start_background_worker

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.get("/status")
async def get_auth_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConnectedAccount).where(ConnectedAccount.email == settings.TARGET_GMAIL_ACCOUNT))
    account = result.scalar_one_or_none()
    is_connected = bool(account and account.status == "connected" and account.access_token_encrypted)
    return {
        "oauth_configured": is_oauth_configured(),
        "connected": is_connected,
        "email": settings.TARGET_GMAIL_ACCOUNT,
        "status": "connected" if is_connected else "disconnected",
        "last_sync_at": account.last_sync_at.isoformat() if account and account.last_sync_at else None,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI
    }

@router.get("/login")
async def login_google(request: Request):
    if not is_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Google OAuth is not configured on the server. "
                "Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the environment variables."
            )
        )
    try:
        flow = get_google_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        request.session.clear()
        request.session["oauth_state"] = state
        return {"authorization_url": authorization_url, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate OAuth URL: {e!s}")

@router.get("/callback")
async def auth_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_db),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter from OAuth response")
    expected = request.session.pop("oauth_state", "")
    if not expected or not state or not hmac.compare_digest(expected, state):
        raise HTTPException(status_code=403, detail="Invalid Google OAuth session state")
    try:
        flow = get_google_oauth_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Verify connected email via Google userinfo
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {creds.token}"}
            )
            resp.raise_for_status()
            user_info = resp.json()
            email = str(user_info.get("email") or "").lower().strip()
            if not email or email != settings.TARGET_GMAIL_ACCOUNT.lower():
                raise HTTPException(
                    status_code=403,
                    detail="Only the configured mailbox owner may connect Gmail",
                )

        result = await db.execute(select(ConnectedAccount).where(ConnectedAccount.email == email))
        account = result.scalar_one_or_none()

        if not account:
            account = ConnectedAccount(email=email)
            db.add(account)

        account.access_token_encrypted = encrypt_token(creds.token)
        if creds.refresh_token:
            account.refresh_token_encrypted = encrypt_token(creds.refresh_token)
        account.token_uri = creds.token_uri or "https://oauth2.googleapis.com/token"
        account.client_id = settings.GOOGLE_CLIENT_ID
        account.status = "connected"
        await db.commit()

        request.session["owner_email"] = email

        # Trigger initial discovery sync
        start_background_worker(account_email=email)

        return RedirectResponse(url="/integrations?status=connected")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Google authorization could not be completed. Please retry.",
        ) from None

@router.post("/disconnect")
async def disconnect_account(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConnectedAccount).where(ConnectedAccount.email == settings.TARGET_GMAIL_ACCOUNT))
    account = result.scalar_one_or_none()
    if account:
        if account.access_token_encrypted:
            raw_token = decrypt_token(account.access_token_encrypted)
            await revoke_google_token(raw_token)
        account.status = "disconnected"
        account.access_token_encrypted = ""
        account.refresh_token_encrypted = ""
        await db.commit()
    request.session.clear()
    return {"status": "disconnected", "email": settings.TARGET_GMAIL_ACCOUNT}

