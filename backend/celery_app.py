from celery import Celery
from celery.schedules import crontab

from config import get_settings

settings = get_settings()

celery_app = Celery(
    "cosmo_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "cache-daily-global-transits": {
            "task": "worker.cache_daily_global_transits",
            "schedule": crontab(hour=0, minute=5),
        },
    },
)

celery_app.autodiscover_tasks(["worker"])
