"""FastAPI application entry point."""
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.db import init_db
from app.api.v1.articles import router as articles_router
from app.scheduler import start_scheduler

# Logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# App
app = FastAPI(
    title="CrossBorder Tech Collector",
    description="跨境电商技术信息采集服务",
    version="1.0.0",
)


# --- API Key Auth Middleware ---

API_KEY = os.getenv("API_KEY", "")

# Paths that don't require auth
PUBLIC_PATHS = {"/api/v1/health", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    # Allow public paths
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    if not API_KEY:
        # No API key configured = no auth
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header. Use: Bearer <API_KEY>"})

    token = auth_header[7:]  # Strip "Bearer "
    if token != API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

    return await call_next(request)


# --- Startup / Shutdown ---

@app.on_event("startup")
def startup():
    logger.info("Initializing database...")
    init_db()

    # Start scheduler
    hour = int(os.getenv("COLLECT_CRON_HOUR", "6"))
    minute = int(os.getenv("COLLECT_CRON_MINUTE", "0"))
    start_scheduler(hour=hour, minute=minute)
    logger.info("Application started.")


@app.on_event("shutdown")
def shutdown():
    from app.scheduler import scheduler
    scheduler.shutdown(wait=False)
    logger.info("Application shutdown.")


# --- Routes ---

app.include_router(articles_router)
