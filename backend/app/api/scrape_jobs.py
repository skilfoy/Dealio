from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.scrape_job import ScrapeJob
from app.models.retailer import Retailer
from app.api.schemas import ScrapeJobResponse

router = APIRouter(tags=["scrape-jobs"])


@router.get("/scrape-jobs", response_model=list[ScrapeJobResponse])
async def list_scrape_jobs(
    retailer_slug: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ScrapeJob, Retailer)
        .join(Retailer, ScrapeJob.retailer_id == Retailer.id)
        .order_by(desc(ScrapeJob.created_at))
        .limit(limit)
    )
    if retailer_slug:
        query = query.where(Retailer.slug == retailer_slug)

    result = await db.execute(query)
    jobs = []
    for job, retailer in result.all():
        jobs.append(
            ScrapeJobResponse(
                id=job.id,
                retailer_id=job.retailer_id,
                status=job.status,
                items_found=job.items_found,
                deals_found=job.deals_found,
                error_message=job.error_message,
                started_at=job.started_at,
                completed_at=job.completed_at,
                created_at=job.created_at,
                retailer_name=retailer.name,
            )
        )
    return jobs
