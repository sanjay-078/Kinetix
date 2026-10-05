from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import ConnectedAccount
from app.services.auth import get_google_oauth_flow, encrypt_token, decrypt_token
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.get("/status")
async def get_auth_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConnectedAccount).where(ConnectedAccount.email == settings.TARGET_GMAIL_ACCOUNT))
    account = result.scalar_one_or_none()
    if account and account.status == "connected":
        return {
            "connected": True,
            "email": account.email,
            "status": "connected",
            "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None
        }
    return {
        "connected": False,
        "email": settings.TARGET_GMAIL_ACCOUNT,
        "status": "disconnected"
    }

@router.get("/login")
async def login_google():
    flow = get_google_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return {"authorization_url": authorization_url}

@router.get("/callback")
async def auth_callback(code: str = None, state: str = None, db: AsyncSession = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")
    try:
        flow = get_google_oauth_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Get connected user email
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {creds.token}"}
            )
            user_info = resp.json()
            email = user_info.get("email", settings.TARGET_GMAIL_ACCOUNT)

        result = await db.execute(select(ConnectedAccount).where(ConnectedAccount.email == email))
        account = result.scalar_one_or_none()

        if not account:
            account = ConnectedAccount(email=email)
            db.add(account)

        account.access_token_encrypted = encrypt_token(creds.token)
        account.refresh_token_encrypted = encrypt_token(creds.refresh_token or "")
        account.status = "connected"
        await db.commit()

        return RedirectResponse(url="/integrations?status=connected")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")

@router.post("/disconnect")
async def disconnect_account(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConnectedAccount).where(ConnectedAccount.email == settings.TARGET_GMAIL_ACCOUNT))
    account = result.scalar_one_or_none()
    if account:
        account.status = "disconnected"
        account.access_token_encrypted = ""
        account.refresh_token_encrypted = ""
        await db.commit()
    return {"status": "disconnected"}
