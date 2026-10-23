import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ConnectedAccount, SheetSyncState
from app.services.auth import get_valid_credentials
from app.services.sheets import batch_sync_to_google_sheets
from app.services.worker import start_background_worker

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_integrations_status(db: AsyncSession = Depends(get_db)):
    # Gmail status
    acc_res = await db.execute(select(ConnectedAccount).where(ConnectedAccount.email == settings.TARGET_GMAIL_ACCOUNT))
    account = acc_res.scalar_one_or_none()
    gmail_connected = account.status == "connected" if account else False

    # A spreadsheet is connected only after a verified Google API write.
    sheet_res = await db.execute(select(SheetSyncState))
    sheet_state = sheet_res.scalar_one_or_none()
    has_sheet = bool(
        sheet_state
        and sheet_state.status == "complete"
        and sheet_state.spreadsheet_id
    )

    return {
        "gmail": {
            "account": settings.TARGET_GMAIL_ACCOUNT,
            "status": "connected" if gmail_connected else "disconnected",
            "connected": gmail_connected,
            "last_sync": account.last_sync_at.isoformat() if account and account.last_sync_at else None,
        },
        "google_sheets": {
            "connected": has_sheet,
            "sheet_id": sheet_state.spreadsheet_id if has_sheet else None,
            "sheet_url": sheet_state.spreadsheet_url if has_sheet else None,
            "last_sync": (
                sheet_state.last_sync_at.isoformat()
                if has_sheet and sheet_state.last_sync_at else None
            ),
            "rows_synced": sheet_state.products_synced if has_sheet else 0,
        },
    }

@router.post("/gmail/sync")
async def sync_gmail_now():
    start_background_worker()
    return {"status": "syncing", "message": "Gmail sync triggered"}

@router.post("/sheets/sync")
async def sync_sheets_now(db: AsyncSession = Depends(get_db)):
    account_query = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.email == settings.TARGET_GMAIL_ACCOUNT,
            ConnectedAccount.status == "connected",
        )
    )
    account = account_query.scalar_one_or_none()
    creds = await get_valid_credentials(account, db) if account else None
    if not creds or not creds.valid:
        raise HTTPException(
            status_code=503,
            detail="Connect your authorized Google account before syncing Sheets.",
        )
    try:
        result = await batch_sync_to_google_sheets(db, creds=creds)
    except Exception:
        logger.exception("Google Sheets API sync failed")
        raise HTTPException(
            status_code=502,
            detail="Google Sheets API write failed. Check the integration and retry.",
        ) from None
    return {"status": "success", "result": result}
