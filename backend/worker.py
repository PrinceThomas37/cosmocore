"""
Celery worker — caches geocentric global transits to PostgreSQL.
"""
from __future__ import annotations

from datetime import datetime, timezone

from celery_app import celery_app
from config import get_settings
from database import insert_global_transit
from engine import CosmoCoreMasterEngine


@celery_app.task(name="worker.cache_daily_global_transits")
def cache_daily_global_transits():
    utc_now = datetime.now(timezone.utc)
    jd = CosmoCoreMasterEngine.calculate_julian_date(utc_now)
    positions = CosmoCoreMasterEngine.calculate_true_planetary_positions(
        jd, lat=0.0, lon=0.0, is_topocentric=False
    )
    insert_global_transit(utc_now.isoformat(), positions)
    return {
        "status": "ok",
        "timestamp": utc_now.isoformat(),
        "planets": list(positions.keys()),
        "ephemeris_path": get_settings().swisseph_path,
    }
