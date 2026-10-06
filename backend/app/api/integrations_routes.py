from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ConnectedAccount, Product, SheetSyncState
from app.services.sheets import batch_sync_to_google_sheets
from app.services.worker import start_background_worker

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

@router.get("/status")
async def get_integrations_status(db: AsyncSession = Depends(get_db)):
    # Gmail status
    acc_res = await db.execute(select(ConnectedAccount).where(ConnectedAccount.email == settings.TARGET_GMAIL_ACCOUNT))
    account = acc_res.scalar_one_or_none()
    gmail_connected = account.status == "connected" if account else False

    # Sheets status
    sheet_res = await db.execute(select(SheetSyncState))
    sheet_state = sheet_res.scalar_one_or_none()

    products_count = (await db.execute(select(func.count(Product.id)))).scalar() or 0

    return {
        "gmail": {
            "account": settings.TARGET_GMAIL_ACCOUNT,
            "status": "connected" if gmail_connected else "disconnected",
            "connected": gmail_connected,
            "last_sync": account.last_sync_at.isoformat() if account and account.last_sync_at else None
        },
        "google_sheets": {
            "connected": True if settings.GOOGLE_SHEET_ID or sheet_state else False,
            "sheet_id": settings.GOOGLE_SHEET_ID or (sheet_state.spreadsheet_id if sheet_state else "1DemoSheetKinetixExport2026"),
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{settings.GOOGLE_SHEET_ID or '1DemoSheetKinetixExport2026'}",
            "last_sync": sheet_state.last_sync_at.isoformat() if sheet_state and sheet_state.last_sync_at else None,
            "rows_synced": sheet_state.products_synced if sheet_state else products_count
        }
    }

@router.post("/gmail/sync")
async def sync_gmail_now():
    start_background_worker()
    return {"status": "syncing", "message": "Gmail sync triggered"}

@router.post("/sheets/sync")
async def sync_sheets_now(db: AsyncSession = Depends(get_db)):
    result = await batch_sync_to_google_sheets(db)
    return {"status": "success", "result": result}
