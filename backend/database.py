import json
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import psycopg2
from psycopg2.extras import RealDictCursor

from config import get_settings


@contextmanager
def get_connection():
    conn = psycopg2.connect(get_settings().database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_user_and_profile(
    user_id: str,
    display_name: str,
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone_id: str,
    chart: dict[str, Any],
) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, display_name, birth_date, birth_time, latitude, longitude, timezone_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    birth_date = EXCLUDED.birth_date,
                    birth_time = EXCLUDED.birth_time,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    timezone_id = EXCLUDED.timezone_id
                """,
                (user_id, display_name, birth_date, birth_time, latitude, longitude, timezone_id),
            )
            cur.execute(
                """
                INSERT INTO astrology_profiles (
                    profile_id, western_planets, western_houses, western_aspects,
                    vedic_d1, vedic_d9, vedic_dashas, firdaria_timeline, astrocartography
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (profile_id) DO UPDATE SET
                    western_planets = EXCLUDED.western_planets,
                    western_houses = EXCLUDED.western_houses,
                    western_aspects = EXCLUDED.western_aspects,
                    vedic_d1 = EXCLUDED.vedic_d1,
                    vedic_d9 = EXCLUDED.vedic_d9,
                    vedic_dashas = EXCLUDED.vedic_dashas,
                    firdaria_timeline = EXCLUDED.firdaria_timeline,
                    astrocartography = EXCLUDED.astrocartography,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    json.dumps(chart["western"]["planets"]),
                    json.dumps(chart["western"]["houses"]),
                    json.dumps(chart["western"]["aspects"]),
                    json.dumps(chart["vedic"]["d1"]),
                    json.dumps(chart["vedic"]["d9"]),
                    json.dumps(chart["vedic"].get("dashas", {})),
                    json.dumps(chart["firdaria"]),
                    json.dumps(chart["astrocartography"]),
                ),
            )
    return user_id


def get_profile(user_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT u.*, p.western_planets, p.western_houses, p.western_aspects,
                       p.vedic_d1, p.vedic_d9, p.vedic_dashas, p.firdaria_timeline, p.astrocartography
                FROM users u
                JOIN astrology_profiles p ON p.profile_id = u.id
                WHERE u.id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return dict(row)


def insert_global_transit(timestamp_iso: str, positions: dict[str, Any]) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO global_transit_cache (calculation_timestamp, planet_positions_json)
                VALUES (%s, %s)
                ON CONFLICT (calculation_timestamp) DO UPDATE SET
                    planet_positions_json = EXCLUDED.planet_positions_json
                """,
                (timestamp_iso, json.dumps(positions)),
            )


def latest_global_transit() -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT calculation_timestamp, planet_positions_json
                FROM global_transit_cache
                ORDER BY calculation_timestamp DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            return dict(row) if row else None


def parse_uuid(value: str) -> UUID:
    return UUID(value)
