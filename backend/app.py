"""
CosmoCore Production API — FastAPI gateway.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import get_settings
from database import get_profile, latest_global_transit, save_user_and_profile
from engine import CosmoCoreMasterEngine

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app = FastAPI(
    title="CosmoCore Production API",
    version="1.0.0",
    description="Dual-engine astrology platform (Western tropical + Vedic sidereal)",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BirthProfilePayload(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: str = Field(..., description="HH:MM or HH:MM:SS")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone_id: str = Field(..., description="IANA timezone, e.g. America/New_York")
    current_age: float = Field(25.0, ge=0, le=120)
    is_nocturnal: bool = False
    persist: bool = True


def _parse_birth_datetime(birth_date: str, birth_time: str, timezone_id: str) -> datetime:
    try:
        ZoneInfo(timezone_id)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid timezone_id: {timezone_id}") from exc

    date_fmt = "%Y-%m-%d"
    for time_fmt in ("%H:%M:%S", "%H:%M"):
        try:
            local_dt = datetime.strptime(f"{birth_date} {birth_time}", f"{date_fmt} {time_fmt}")
            break
        except ValueError:
            continue
    else:
        raise HTTPException(status_code=400, detail="birth_time must be HH:MM or HH:MM:SS")

    return local_dt.replace(tzinfo=ZoneInfo(timezone_id)).astimezone(ZoneInfo("UTC"))


@app.get("/health")
async def health():
    return {"status": "ok", "ephemeris_path": settings.swisseph_path}


@app.post("/api/v1/chart/compute")
async def compute_master_chart(payload: BirthProfilePayload):
    try:
        utc_dt = _parse_birth_datetime(payload.birth_date, payload.birth_time, payload.timezone_id)
        chart = CosmoCoreMasterEngine.build_full_chart(
            utc_dt,
            payload.latitude,
            payload.longitude,
            payload.current_age,
            payload.is_nocturnal,
        )

        user_id = str(uuid.uuid4())
        if payload.persist:
            try:
                save_user_and_profile(
                    user_id,
                    payload.display_name,
                    payload.birth_date,
                    payload.birth_time[:8],
                    payload.latitude,
                    payload.longitude,
                    payload.timezone_id,
                    chart,
                )
            except Exception as db_err:
                raise HTTPException(
                    status_code=503,
                    detail=f"Chart computed but database save failed: {db_err}",
                ) from db_err

        return {
            "user_id": user_id,
            "display_name": payload.display_name,
            "utc_time": chart["utc_time"],
            "julian_date": chart["julian_date"],
            "western": chart["western"],
            "vedic": chart["vedic"],
            "firdaria": chart["firdaria"],
            "astrocartography": chart["astrocartography"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/profile/{user_id}")
async def get_user_profile(user_id: str):
    try:
        row = get_profile(user_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return row


@app.get("/api/v1/transits/global/latest")
async def get_latest_global_transits():
    try:
        row = latest_global_transit()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=404, detail="No global transit cache yet")
    return row


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=settings.api_host, port=settings.api_port, reload=True)
