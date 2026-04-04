from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "dealradar",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 min max per task
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.scrape_tasks.*": {"queue": "scrapers"},
    },
    beat_schedule={
        # Tier 1 scrapers: every 15 minutes
        "scrape-tier1": {
            "task": "app.tasks.scrape_tasks.scrape_tier",
            "schedule": 900,  # 15 minutes
            "args": (1,),
        },
        # Tier 2 scrapers: every 2 hours
        "scrape-tier2": {
            "task": "app.tasks.scrape_tasks.scrape_tier",
            "schedule": 7200,
            "args": (2,),
        },
        # Tier 3 scrapers: every 4 hours
        "scrape-tier3": {
            "task": "app.tasks.scrape_tasks.scrape_tier",
            "schedule": 14400,
            "args": (3,),
        },
        # Expire old deals: every 6 hours
        "expire-deals": {
            "task": "app.tasks.maintenance_tasks.expire_old_deals",
            "schedule": 21600,
        },
        # Cleanup old price history: weekly Sunday 3am
        "cleanup-history": {
            "task": "app.tasks.maintenance_tasks.cleanup_price_history",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
