import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine, async_session
from app.models import *  # noqa: F401,F403 — ensure all models registered
from app.models.seed import seed_retailers
from app.api.deals import router as deals_router
from app.api.products import router as products_router
from app.api.retailers import router as retailers_router
from app.api.api_keys import router as api_keys_router
from app.api.coupons import router as coupons_router
from app.api.sse import router as sse_router
from app.api.scrape_jobs import router as scrape_jobs_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DealRadar", version="1.0.0", description="Real-time deal tracking and price monitoring")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sse_router, prefix="/api")
app.include_router(deals_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(retailers_router, prefix="/api")
app.include_router(api_keys_router, prefix="/api")
app.include_router(coupons_router, prefix="/api")
app.include_router(scrape_jobs_router, prefix="/api")


@app.on_event("startup")
async def startup():
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    async with async_session() as db:
        await seed_retailers(db)

    logger.info("DealRadar API started")

    # Kick off initial scan in background — fires registered, key-free scrapers immediately
    import asyncio
    asyncio.create_task(_initial_scan())


async def _initial_scan():
    import asyncio
    await asyncio.sleep(5)  # Let workers finish starting
    try:
        from app.tasks.scrape_tasks import trigger_initial_scan
        trigger_initial_scan.delay()
        logger.info("Initial scan triggered")
    except Exception as e:
        logger.warning("Could not trigger initial scan: %s", e)


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "dealradar-api",
        "version": "1.0.0",
    }
