from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.retailer import Retailer
from app.api.schemas import RetailerResponse, RetailerUpdate

router = APIRouter(tags=["retailers"])


@router.get("/retailers", response_model=list[RetailerResponse])
async def list_retailers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Retailer).order_by(Retailer.tier, Retailer.name))
    return [RetailerResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/retailers/{slug}", response_model=RetailerResponse)
async def get_retailer(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Retailer).where(Retailer.slug == slug))
    retailer = result.scalars().first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    return RetailerResponse.model_validate(retailer)


@router.patch("/retailers/{slug}", response_model=RetailerResponse)
async def update_retailer(slug: str, update: RetailerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Retailer).where(Retailer.slug == slug))
    retailer = result.scalars().first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(retailer, field, value)
    await db.commit()
    await db.refresh(retailer)
    return RetailerResponse.model_validate(retailer)


@router.post("/retailers/scrape-all")
async def scrape_all_available(db: AsyncSession = Depends(get_db)):
    """Queue scrape jobs for all enabled retailers that have a registered scraper and need no API key."""
    from app.scrapers.registry import get_all_scrapers
    from app.tasks.scrape_tasks import scrape_retailer

    registered = get_all_scrapers()
    result = await db.execute(
        select(Retailer).where(Retailer.is_enabled == True, Retailer.requires_api_key == False)
    )
    retailers = result.scalars().all()

    queued = [r.slug for r in retailers if r.slug in registered]
    for slug in queued:
        scrape_retailer.delay(slug)

    return {"status": "queued", "count": len(queued), "retailers": queued}


@router.post("/retailers/{slug}/scrape")
async def trigger_scrape(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Retailer).where(Retailer.slug == slug))
    retailer = result.scalars().first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")

    from app.tasks.scrape_tasks import scrape_retailer
    scrape_retailer.delay(slug)
    return {"status": "queued", "retailer": slug}
