import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth_routes import router as auth_router
from app.api.catalogues_routes import router as catalogues_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.diagnostics_routes import router as diagnostics_router
from app.api.emails_routes import router as emails_router
from app.api.integrations_routes import router as integrations_router
from app.api.products_routes import router as products_router
from app.api.review_routes import router as review_router
from app.api.suppliers_routes import router as suppliers_router
from app.config import settings
from app.database import Base, engine
from app.services.pdf_guardrail import MEDIA_DIR
from app.services.worker import start_background_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Never run a production deployment with shared secrets or ephemeral SQLite.
    if settings.APP_ENV.lower() == "production":
        if (
            settings.SESSION_SECRET == "kinetix-production-secret-key-32charsmin!"
            or settings.ENCRYPTION_KEY == "kinetix-token-encryption-secret-key32!"
            or len(settings.SESSION_SECRET) < 32
            or len(settings.ENCRYPTION_KEY) < 32
        ):
            raise RuntimeError(
                "Production requires unique SESSION_SECRET and ENCRYPTION_KEY values"
            )
        if settings.DATABASE_URL.startswith("sqlite"):
            raise RuntimeError("Production requires a durable PostgreSQL DATABASE_URL")
    # Initialize DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Only authorized real Gmail accounts can initiate mailbox scanning.
    start_background_worker()
    yield

app = FastAPI(
    title="Kinetix API",
    description="Mailbox Ingestion & Product Extraction Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for production & frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kinetix-app.onrender.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(products_router)
app.include_router(suppliers_router)
app.include_router(emails_router)
app.include_router(catalogues_router)
app.include_router(review_router)
app.include_router(integrations_router)
app.include_router(diagnostics_router)

# Sensitive supplier/email data is private even if someone knows the URL.
# In development automated fixtures can still exercise the API without OAuth.
@app.middleware("http")
async def owner_session_guard(request: Request, call_next):
    path = request.url.path
    private_prefixes = (
        "/api/products",
        "/api/suppliers",
        "/api/emails",
        "/api/catalogues",
        "/api/review",
        "/api/integrations",
        "/api/dashboard",
        "/api/diagnostics",
        "/api/auth/disconnect",
        "/media/",
    )
    if settings.APP_ENV.lower() == "production" and path.startswith(private_prefixes):
        if request.session.get("owner_email") != settings.TARGET_GMAIL_ACCOUNT:
            return JSONResponse(
                {"detail": "Owner authentication required"}, status_code=401
            )
    return await call_next(request)


# Mount media directory for PDF downloads
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "kinetix-backend", "version": "1.0.0"}

# Serve built frontend SPA static files safely without interfering with /api/ routes
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.middleware("http")
    async def spa_middleware(request: Request, call_next):
        response = await call_next(request)
        if response.status_code == 404 and not request.url.path.startswith("/api"):
            file_path = os.path.join(FRONTEND_DIST, request.url.path.lstrip("/"))
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
        return response


# Session middleware must be the outermost middleware, so the guard can
# validate the signed cookie before any private endpoint is dispatched.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie="kinetix_session",
    same_site="lax",
    https_only=settings.APP_ENV.lower() == "production",
    max_age=12 * 60 * 60,
)
