"""
CosmoCore Master Engine — Swiss Ephemeris (pyswisseph) calculations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import swisseph as swe

from config import get_settings

# Initialize ephemeris path once at import
_ephe = get_settings().swisseph_path
swe.set_ephe_path(_ephe)


class CosmoCoreMasterEngine:
    PLANETS: dict[str, int] = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Uranus": swe.URANUS,
        "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO,
        "North Node": swe.TRUE_NODE,
        "Chiron": swe.CHIRON,
    }

    ZODIAC_SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]

    NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
        "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
    ]

    ASPECTS: dict[str, tuple[int, float]] = {
        "Conjunction": (0, 8),
        "Sextile": (60, 6),
        "Square": (90, 6),
        "Trine": (120, 8),
        "Opposition": (180, 8),
    }

    FIRDARIA_DIURNAL = [
        {"planet": "Sun", "years": 10},
        {"planet": "Venus", "years": 8},
        {"planet": "Mercury", "years": 13},
        {"planet": "Moon", "years": 9},
        {"planet": "Saturn", "years": 11},
        {"planet": "Jupiter", "years": 12},
        {"planet": "Mars", "years": 7},
    ]

    # Vimshottari: years per planet (total 120)
    VIMSHOTTARI = [
        ("Ketu", 7),
        ("Venus", 20),
        ("Sun", 6),
        ("Moon", 10),
        ("Mars", 7),
        ("Rahu", 18),
        ("Jupiter", 16),
        ("Saturn", 19),
        ("Mercury", 17),
    ]

    @classmethod
    def calculate_julian_date(cls, utc_dt: datetime) -> float:
        utc_dt = utc_dt.astimezone(timezone.utc)
        hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)

    @classmethod
    def get_lahiri_ayanamsa(cls, jd: float) -> float:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.get_ayanamsa(jd)

    @classmethod
    def calculate_true_planetary_positions(
        cls,
        jd: float,
        lat: float,
        lon: float,
        is_topocentric: bool = False,
    ) -> dict[str, dict[str, Any]]:
        flag = swe.FLG_SWIEPH | swe.FLG_SPEED
        if is_topocentric:
            swe.set_topo(lon, lat, 0)
            flag |= swe.FLG_TOPOCTR

        positions: dict[str, dict[str, Any]] = {}
        for name, planet_id in cls.PLANETS.items():
            calc = cls._calc_ut_position(jd, planet_id, flag)
            if calc is None:
                continue
            longitude = calc[0] % 360
            declination = calc[1]
            distance = calc[2] if len(calc) > 2 else 0.0
            speed = calc[3] if len(calc) > 3 else 0.0
            positions[name] = {
                "absolute_long": round(longitude, 6),
                "declination": round(declination, 6),
                "distance_au": round(distance, 6),
                "speed": round(speed, 6),
                "is_retrograde": speed < 0,
                "is_out_of_bounds": abs(declination) > 23.439,
            }

        # South node = North node + 180°
        if "North Node" in positions:
            nn = positions["North Node"]["absolute_long"]
            positions["South Node"] = {
                **positions["North Node"],
                "absolute_long": round((nn + 180) % 360, 6),
            }
        return positions

    @classmethod
    def calculate_houses(
        cls,
        jd: float,
        lat: float,
        lon: float,
        house_system: str | None = None,
    ) -> dict[str, Any]:
        hs = house_system or get_settings().house_system
        hs_bytes = hs.encode() if isinstance(hs, str) else hs
        try:
            cusps, ascmc = swe.houses(jd, lat, lon, hs_bytes)
        except Exception:
            cusps, ascmc = swe.houses(jd, lat, lon, b"O")
        if not ascmc or len(ascmc) < 2:
            raise ValueError("House calculation failed for this location")
        house_cusps = []
        if len(cusps) >= 13:
            house_indices = range(1, 13)
        else:
            house_indices = range(min(12, len(cusps)))
        for house_num, i in enumerate(house_indices, start=1):
            cusp_long = cusps[i] % 360
            house_cusps.append({
                "house": house_num,
                **cls.extract_coordinate_sign_data(cusp_long),
            })
        angles = {
            "ASC": cls.extract_coordinate_sign_data(ascmc[0]),
            "MC": cls.extract_coordinate_sign_data(ascmc[1]),
            "DSC": cls.extract_coordinate_sign_data((ascmc[0] + 180) % 360),
            "IC": cls.extract_coordinate_sign_data((ascmc[1] + 180) % 360),
        }
        return {"system": hs, "cusps": house_cusps, "angles": angles}

    @classmethod
    def extract_coordinate_sign_data(cls, longitude: float) -> dict[str, Any]:
        long_norm = longitude % 360
        idx = int(long_norm // 30) % 12
        return {
            "sign": cls.ZODIAC_SIGNS[idx],
            "degree": round(long_norm % 30, 4),
            "absolute_long": round(long_norm, 4),
        }

    @classmethod
    def calculate_aspect_matrix(cls, planets_data: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        detected: list[dict[str, Any]] = []
        names = [n for n in planets_data if "absolute_long" in planets_data[n]]
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                p1, p2 = names[i], names[j]
                lon1 = planets_data[p1]["absolute_long"]
                lon2 = planets_data[p2]["absolute_long"]
                diff = abs(lon1 - lon2)
                shortest = diff if diff <= 180 else 360 - diff
                for aspect, (angle, orb) in cls.ASPECTS.items():
                    separation = abs(shortest - angle)
                    if separation <= orb:
                        detected.append({
                            "p1": p1,
                            "p2": p2,
                            "aspect": aspect,
                            "orb": round(separation, 2),
                            "exact_angle": angle,
                        })
        return detected

    @classmethod
    def calculate_nakshatra(cls, sidereal_long: float) -> dict[str, Any]:
        sidereal_long = sidereal_long % 360
        nak_width = 360.0 / 27.0
        idx = min(int(sidereal_long // nak_width), 26)
        remainder = sidereal_long % nak_width
        pada = min(int(remainder // (nak_width / 4.0)) + 1, 4)
        return {"name": cls.NAKSHATRAS[idx], "pada": pada, "index": idx + 1}

    @classmethod
    def calculate_d9_navamsha(cls, sidereal_long: float) -> dict[str, Any]:
        sidereal_long = sidereal_long % 360
        sign_index = int(sidereal_long // 30)
        degree_in_sign = sidereal_long % 30
        nav_sign = (sign_index * 9 + int(degree_in_sign // (30 / 9))) % 12
        nav_degree = (degree_in_sign % (30 / 9)) * 9
        d9_abs = nav_sign * 30.0 + nav_degree
        return cls.extract_coordinate_sign_data(d9_abs)

    @classmethod
    def generate_firdaria_timeline(cls, age: float, is_nocturnal: bool = False) -> dict[str, Any]:
        sequence = list(cls.FIRDARIA_DIURNAL)
        if is_nocturnal:
            sequence = [sequence[3], sequence[2], sequence[1], sequence[0]] + sequence[4:]
        accumulated = 0.0
        for period in sequence:
            end = accumulated + period["years"]
            if accumulated <= age < end:
                sub_years = period["years"] / 7.0
                sub_index = min(int((age - accumulated) // sub_years), 6)
                major_idx = sequence.index(period)
                sub_planet = sequence[(major_idx + sub_index) % len(sequence)]["planet"]
                progress = ((age - accumulated) / period["years"]) * 100
                return {
                    "major": period["planet"],
                    "sub": sub_planet,
                    "progress": round(progress, 1),
                    "years_in_major": round(age - accumulated, 2),
                }
            accumulated = end
        return {"major": "Sun", "sub": "Sun", "progress": 0.0, "years_in_major": 0.0}

    @classmethod
    def _nakshatra_lord_index(cls, sidereal_moon_long: float) -> int:
        nak = cls.calculate_nakshatra(sidereal_moon_long)
        lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
        return (nak["index"] - 1) % 9

    @classmethod
    def generate_vimshottari_dasha(
        cls,
        birth_jd: float,
        moon_sidereal_long: float,
        query_jd: float | None = None,
    ) -> dict[str, Any]:
        """Mahadasha at birth + current period at query_jd (default: now)."""
        if query_jd is None:
            query_jd = cls.calculate_julian_date(datetime.now(timezone.utc))

        nak_width = 360.0 / 27.0
        sid = moon_sidereal_long % 360
        lord_idx = cls._nakshatra_lord_index(sid)
        portion_elapsed = (sid % nak_width) / nak_width
        balance_years = cls.VIMSHOTTARI[lord_idx][1] * (1 - portion_elapsed)

        # Build full cycle from birth lord
        order = [(lord_idx + i) % 9 for i in range(9)]
        timeline: list[dict[str, Any]] = []
        start_jd = birth_jd
        years_left = balance_years
        for i, idx in enumerate(order):
            planet, total_years = cls.VIMSHOTTARI[idx]
            dur = years_left if i == 0 else float(total_years)
            end_jd = start_jd + dur * 365.25
            timeline.append({
                "planet": planet,
                "start_jd": start_jd,
                "end_jd": end_jd,
                "years": round(dur, 4),
            })
            start_jd = end_jd
            years_left = float(total_years)

        current = timeline[0]
        for period in timeline:
            if period["start_jd"] <= query_jd < period["end_jd"]:
                current = period
                break

        return {
            "birth_balance_lord": cls.VIMSHOTTARI[lord_idx][0],
            "balance_years_at_birth": round(balance_years, 4),
            "current_mahadasha": current["planet"],
            "mahadasha_timeline": timeline[:9],
        }

    @classmethod
    def calculate_astrocartography_lines(
        cls,
        planet_long: float,
        declination: float,
        body_name: str = "Sun",
    ) -> dict[str, Any]:
        """Sample MC/ASC-related line points (simplified Jim Lewis style)."""
        vectors = []
        for hour in range(0, 24, 3):
            lon = (planet_long - hour * 15.0) % 360
            if lon > 180:
                lon -= 360
            vectors.append({
                "hour_meridian": hour,
                "lat": round(declination, 4),
                "lon": round(lon, 4),
            })
        return {"body": body_name, "vectors": vectors}

    @classmethod
    def build_full_chart(
        cls,
        utc_dt: datetime,
        lat: float,
        lon: float,
        current_age: float,
        is_nocturnal: bool = False,
    ) -> dict[str, Any]:
        jd = cls.calculate_julian_date(utc_dt)
        raw = cls.calculate_true_planetary_positions(jd, lat, lon, is_topocentric=True)
        if "Moon" not in raw or "Sun" not in raw:
            raise ValueError(
                "Could not calculate Sun/Moon positions. Ephemeris data may be missing on the server."
            )
        ayanamsa = cls.get_lahiri_ayanamsa(jd)
        houses = cls.calculate_houses(jd, lat, lon)

        western_planets: dict[str, Any] = {}
        for name, data in raw.items():
            western_planets[name] = {
                **cls.extract_coordinate_sign_data(data["absolute_long"]),
                "declination": data["declination"],
                "is_retrograde": data["is_retrograde"],
                "is_out_of_bounds": data["is_out_of_bounds"],
            }

        western_aspects = cls.calculate_aspect_matrix(western_planets)

        vedic_d1: dict[str, Any] = {}
        vedic_d9: dict[str, Any] = {}
        for name, data in raw.items():
            sidereal = (data["absolute_long"] - ayanamsa) % 360
            vedic_d1[name] = {
                **cls.extract_coordinate_sign_data(sidereal),
                "nakshatra": cls.calculate_nakshatra(sidereal),
            }
            vedic_d9[name] = cls.calculate_d9_navamsha(sidereal)

        moon_sid = (raw["Moon"]["absolute_long"] - ayanamsa) % 360
        dashas = cls.generate_vimshottari_dasha(jd, moon_sid)

        firdaria = cls.generate_firdaria_timeline(current_age, is_nocturnal)

        acg: dict[str, Any] = {}
        for body in ("Sun", "Moon", "Venus", "Mars", "Jupiter", "Saturn"):
            if body in raw:
                acg[body] = cls.calculate_astrocartography_lines(
                    raw[body]["absolute_long"],
                    raw[body]["declination"],
                    body,
                )

        return {
            "julian_date": jd,
            "utc_time": utc_dt.isoformat(),
            "ayanamsa": round(ayanamsa, 6),
            "western": {
                "planets": western_planets,
                "houses": houses,
                "aspects": western_aspects,
            },
            "vedic": {
                "d1": vedic_d1,
                "d9": vedic_d9,
                "dashas": dashas,
                "ayanamsa": round(ayanamsa, 6),
            },
            "firdaria": firdaria,
            "astrocartography": acg,
        }
