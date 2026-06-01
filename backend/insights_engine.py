"""
CosmoCore Insights — rule-based readings from natal chart + short-term transits.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from engine import CosmoCoreMasterEngine

# Plain-language tone for non-astrologers
SIGN_THEMES: dict[str, dict[str, str]] = {
    "Aries": {"tone": "direct and energetic", "gift": "courage to start fresh"},
    "Taurus": {"tone": "steady and grounded", "gift": "patience and loyalty"},
    "Gemini": {"tone": "curious and quick", "gift": "adaptability and wit"},
    "Cancer": {"tone": "caring and protective", "gift": "emotional depth and nurture"},
    "Leo": {"tone": "warm and expressive", "gift": "confidence and generosity"},
    "Virgo": {"tone": "practical and thoughtful", "gift": "discernment and service"},
    "Libra": {"tone": "harmonious and fair", "gift": "diplomacy and partnership"},
    "Scorpio": {"tone": "intense and loyal", "gift": "focus and transformation"},
    "Sagittarius": {"tone": "open and hopeful", "gift": "vision and honesty"},
    "Capricorn": {"tone": "disciplined and ambitious", "gift": "structure and endurance"},
    "Aquarius": {"tone": "independent and original", "gift": "innovation and community"},
    "Pisces": {"tone": "gentle and imaginative", "gift": "compassion and intuition"},
}

PLANET_TOPICS: dict[str, str] = {
    "Sun": "identity and purpose",
    "Moon": "emotions and comfort",
    "Mercury": "thinking and communication",
    "Venus": "love and values",
    "Mars": "drive and boundaries",
    "Jupiter": "growth and opportunity",
    "Saturn": "responsibility and lessons",
}

FIRDARIA_MEANINGS: dict[str, str] = {
    "Sun": "visibility, leadership, and stepping into your own light",
    "Moon": "home, feelings, and inner security",
    "Mercury": "learning, messages, contracts, and busy mental energy",
    "Venus": "relationships, pleasure, creativity, and what you attract",
    "Mars": "action, courage, competition, and pushing through blocks",
    "Jupiter": "expansion, travel, study, and fortunate openings",
    "Saturn": "maturity, boundaries, long-term work, and paying dues",
}

INSIGHT_CATEGORIES = ("today", "tomorrow", "relationships", "money", "family", "kids")


def _planet_longitudes(chart: dict[str, Any]) -> dict[str, float]:
    planets = chart.get("western", {}).get("planets", {})
    return {
        name: float(data["absolute_long"])
        for name, data in planets.items()
        if isinstance(data, dict) and "absolute_long" in data
    }


def _house_of_planet(planet_long: float, cusps: list[dict[str, Any]]) -> int | None:
    if not cusps:
        return None
    ordered = sorted(cusps, key=lambda c: c.get("house", 0))
    longs = [float(c["absolute_long"]) for c in ordered]
    p = planet_long % 360
    for i in range(12):
        start = longs[i]
        end = longs[(i + 1) % 12]
        if start <= end:
            if start <= p < end:
                return ordered[i].get("house", i + 1)
        else:
            if p >= start or p < end:
                return ordered[i].get("house", i + 1)
    return ordered[0].get("house", 1)


def _cusp_sign(chart: dict[str, Any], house_num: int) -> str | None:
    cusps = chart.get("western", {}).get("houses", {}).get("cusps", [])
    for c in cusps:
        if c.get("house") == house_num:
            return c.get("sign")
    return None


def _natal_aspects(chart: dict[str, Any]) -> list[dict[str, Any]]:
    return chart.get("western", {}).get("aspects", []) or []


def _find_aspects(
    longs_a: dict[str, float], longs_b: dict[str, float], orb: float = 6.0
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for p1, l1 in longs_a.items():
        for p2, l2 in longs_b.items():
            diff = abs(l1 - l2)
            shortest = diff if diff <= 180 else 360 - diff
            for aspect, (angle, _) in CosmoCoreMasterEngine.ASPECTS.items():
                separation = abs(shortest - angle)
                if separation <= orb:
                    hits.append(
                        {
                            "p1": p1,
                            "p2": p2,
                            "aspect": aspect,
                            "orb": round(separation, 2),
                        }
                    )
    return hits


def _transit_positions(utc_dt: datetime, lat: float, lon: float) -> dict[str, dict[str, Any]]:
    jd = CosmoCoreMasterEngine.calculate_julian_date(utc_dt)
    raw = CosmoCoreMasterEngine.calculate_true_planetary_positions(jd, lat, lon, False)
    out: dict[str, dict[str, Any]] = {}
    for name, data in raw.items():
        out[name] = CosmoCoreMasterEngine.extract_coordinate_sign_data(data["absolute_long"])
    return out


def _sign_line(sign: str | None) -> str:
    if not sign:
        return "your chart"
    theme = SIGN_THEMES.get(sign, {})
    return f"{sign} ({theme.get('tone', 'distinct energy')})"


def _planet_in_sign(planets: dict[str, Any], name: str) -> str | None:
    body = planets.get(name)
    return body.get("sign") if isinstance(body, dict) else None


def _bullets(items: list[str], limit: int = 4) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
        if len(out) >= limit:
            break
    return out


class CosmoCoreInsightsEngine:
    @classmethod
    def generate(
        cls,
        chart: dict[str, Any],
        *,
        lat: float,
        lon: float,
        timezone_id: str,
    ) -> dict[str, Any]:
        try:
            tz = timezone.utc
            from zoneinfo import ZoneInfo

            tz = ZoneInfo(timezone_id)
        except Exception:
            tz = timezone.utc

        now_local = datetime.now(tz)
        tomorrow_local = now_local + timedelta(days=1)

        natal_planets = chart.get("western", {}).get("planets", {})
        natal_longs = _planet_longitudes(chart)
        cusps = chart.get("western", {}).get("houses", {}).get("cusps", [])
        angles = chart.get("western", {}).get("houses", {}).get("angles", {})
        firdaria = chart.get("firdaria", {})
        dasha = chart.get("vedic", {}).get("dashas", {})

        insights: dict[str, Any] = {}
        for key in INSIGHT_CATEGORIES:
            insights[key] = cls._build_category(
                key,
                chart=chart,
                natal_planets=natal_planets,
                natal_longs=natal_longs,
                cusps=cusps,
                angles=angles,
                firdaria=firdaria,
                dasha=dasha,
                lat=lat,
                lon=lon,
                now_local=now_local,
                tomorrow_local=tomorrow_local,
            )

        insights["_meta"] = {
            "disclaimer": (
                "These readings are for reflection and self-awareness, not medical, legal, "
                "or financial advice."
            ),
            "generated_at": now_local.isoformat(),
        }
        return insights

    @classmethod
    def _build_category(
        cls,
        category: str,
        *,
        chart: dict[str, Any],
        natal_planets: dict[str, Any],
        natal_longs: dict[str, float],
        cusps: list[dict[str, Any]],
        angles: dict[str, Any],
        firdaria: dict[str, Any],
        dasha: dict[str, Any],
        lat: float,
        lon: float,
        now_local: datetime,
        tomorrow_local: datetime,
    ) -> dict[str, Any]:
        builders = {
            "today": cls._today,
            "tomorrow": cls._tomorrow,
            "relationships": cls._relationships,
            "money": cls._money,
            "family": cls._family,
            "kids": cls._kids,
        }
        return builders[category](
            chart=chart,
            natal_planets=natal_planets,
            natal_longs=natal_longs,
            cusps=cusps,
            angles=angles,
            firdaria=firdaria,
            dasha=dasha,
            lat=lat,
            lon=lon,
            now_local=now_local,
            tomorrow_local=tomorrow_local,
        )

    @classmethod
    def _today(
        cls,
        *,
        natal_planets: dict[str, Any],
        natal_longs: dict[str, float],
        firdaria: dict[str, Any],
        lat: float,
        lon: float,
        now_local: datetime,
        **_: Any,
    ) -> dict[str, Any]:
        utc_now = now_local.astimezone(timezone.utc)
        transits = _transit_positions(utc_now, lat, lon)
        transit_longs = {
            k: float(v["absolute_long"]) for k, v in transits.items() if "absolute_long" in v
        }
        hits = _find_aspects(transit_longs, natal_longs, orb=5.0)

        moon_sign = transits.get("Moon", {}).get("sign")
        mercury_sign = transits.get("Mercury", {}).get("sign")
        bullets: list[str] = []

        if moon_sign:
            theme = SIGN_THEMES.get(moon_sign, {})
            bullets.append(
                f"The Moon in {moon_sign} colors your mood: you may feel more {theme.get('tone', 'sensitive')} today."
            )
        if mercury_sign:
            bullets.append(
                f"Mercury in {mercury_sign} shapes conversations — think before you send important messages."
            )

        for hit in hits[:3]:
            bullets.append(
                cls._aspect_plain(hit, prefix="Today's sky")
            )

        major = firdaria.get("major", "your current")
        sub = firdaria.get("sub", "")
        summary = (
            f"Your day carries {FIRDARIA_MEANINGS.get(major, 'steady life rhythm')} "
            f"with a {sub.lower() if sub else 'supporting'} undertone from your current life chapter."
        )

        return {
            "title": "How your day looks",
            "summary": summary,
            "bullets": _bullets(bullets),
            "mood": moon_sign or "balanced",
        }

    @classmethod
    def _tomorrow(
        cls,
        *,
        natal_longs: dict[str, float],
        lat: float,
        lon: float,
        tomorrow_local: datetime,
        **_: Any,
    ) -> dict[str, Any]:
        utc = tomorrow_local.replace(hour=12, minute=0, second=0).astimezone(timezone.utc)
        transits = _transit_positions(utc, lat, lon)
        transit_longs = {
            k: float(v["absolute_long"]) for k, v in transits.items() if "absolute_long" in v
        }
        hits = _find_aspects(transit_longs, natal_longs, orb=5.0)

        bullets: list[str] = []
        for hit in hits[:4]:
            bullets.append(cls._aspect_plain(hit, prefix="Tomorrow"))

        venus = transits.get("Venus", {}).get("sign")
        mars = transits.get("Mars", {}).get("sign")
        if venus:
            bullets.append(f"Venus in {venus} highlights what you appreciate — plan something that feels good.")
        if mars:
            bullets.append(f"Mars in {mars} shows where to take action — avoid rushing arguments.")

        summary = (
            "Tomorrow favors preparation over pressure: notice what repeats in your thoughts tonight "
            "and set one clear intention for the morning."
        )
        return {
            "title": "Tomorrow's energy",
            "summary": summary,
            "bullets": _bullets(bullets),
            "mood": transits.get("Moon", {}).get("sign", "shifting"),
        }

    @classmethod
    def _relationships(
        cls,
        *,
        chart: dict[str, Any],
        natal_planets: dict[str, Any],
        cusps: list[dict[str, Any]],
        angles: dict[str, Any],
        firdaria: dict[str, Any],
        dasha: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        venus_sign = _planet_in_sign(natal_planets, "Venus")
        mars_sign = _planet_in_sign(natal_planets, "Mars")
        moon_sign = _planet_in_sign(natal_planets, "Moon")
        seventh = _cusp_sign({"western": {"houses": {"cusps": cusps}}}, 7)
        asc = angles.get("ASC", {}).get("sign")

        bullets: list[str] = []
        if venus_sign:
            bullets.append(
                f"Venus in {venus_sign}: you attract through {_sign_line(venus_sign)} — "
                f"your gift is {SIGN_THEMES.get(venus_sign, {}).get('gift', 'heart-led choices')}."
            )
        if mars_sign:
            bullets.append(
                f"Mars in {mars_sign}: you assert yourself in a {SIGN_THEMES.get(mars_sign, {}).get('tone', 'direct')} way in love."
            )
        if moon_sign:
            bullets.append(
                f"Moon in {moon_sign}: emotional safety comes when you feel {SIGN_THEMES.get(moon_sign, {}).get('tone', 'understood')}."
            )
        if seventh:
            bullets.append(f"Partnership style (7th house in {seventh}): you grow through {_sign_line(seventh)}.")

        for asp in _natal_aspects(chart):
            if asp["p1"] in ("Venus", "Mars", "Moon") or asp["p2"] in ("Venus", "Mars", "Moon"):
                bullets.append(cls._aspect_plain(asp, prefix="In your birth chart"))

        sub = firdaria.get("sub", "")
        if sub in ("Venus", "Mars", "Moon"):
            bullets.append(
                f"Right now your life chapter emphasizes {FIRDARIA_MEANINGS.get(sub, 'relationship themes')}."
            )
        if dasha.get("current_mahadasha"):
            bullets.append(
                f"Vedic timing (Mahadasha {dasha['current_mahadasha']}): longer cycles support "
                f"{PLANET_TOPICS.get(dasha['current_mahadasha'], 'relationship growth')}."
            )

        summary = (
            f"With {asc or 'your'} rising, you meet others as someone {_sign_line(asc)}. "
            "Love works best when words and actions match."
        )
        return {
            "title": "Relationships & love",
            "summary": summary,
            "bullets": _bullets(bullets),
        }

    @classmethod
    def _money(
        cls,
        *,
        natal_planets: dict[str, Any],
        natal_longs: dict[str, float],
        cusps: list[dict[str, Any]],
        firdaria: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        second = _cusp_sign({"western": {"houses": {"cusps": cusps}}}, 2)
        tenth = _cusp_sign({"western": {"houses": {"cusps": cusps}}}, 10)
        jupiter_sign = _planet_in_sign(natal_planets, "Jupiter")
        saturn_sign = _planet_in_sign(natal_planets, "Saturn")
        venus_sign = _planet_in_sign(natal_planets, "Venus")

        j_house = _house_of_planet(natal_longs.get("Jupiter", 0), cusps)
        bullets: list[str] = []

        if second:
            bullets.append(f"Money habits (2nd house {second}): income grows through {_sign_line(second)}.")
        if tenth:
            bullets.append(f"Career path (10th house {tenth}): public success leans {_sign_line(tenth)}.")
        if jupiter_sign:
            bullets.append(
                f"Jupiter in {jupiter_sign} expands opportunity when you trust {SIGN_THEMES.get(jupiter_sign, {}).get('gift', 'growth')}."
            )
        if saturn_sign:
            bullets.append(
                f"Saturn in {saturn_sign}: wealth builds slowly through discipline — shortcuts rarely stick."
            )
        if venus_sign:
            bullets.append(f"Venus in {venus_sign}: you value comfort and quality; spending should feel aligned.")

        major = firdaria.get("major", "")
        if major in ("Jupiter", "Venus", "Mercury", "Saturn"):
            bullets.append(
                f"Current chapter ({major}): focus on {FIRDARIA_MEANINGS.get(major, 'material stability')}."
            )
        if j_house:
            bullets.append(f"Jupiter in your house {j_house} points to luck through that life area.")

        summary = "Your chart suggests money follows clarity: name what security means to you, then price your time accordingly."
        return {"title": "Money & work", "summary": summary, "bullets": _bullets(bullets)}

    @classmethod
    def _family(
        cls,
        *,
        chart: dict[str, Any],
        natal_planets: dict[str, Any],
        cusps: list[dict[str, Any]],
        dasha: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        fourth = _cusp_sign({"western": {"houses": {"cusps": cusps}}}, 4)
        moon_sign = _planet_in_sign(natal_planets, "Moon")
        sun_sign = _planet_in_sign(natal_planets, "Sun")

        bullets: list[str] = []
        if fourth:
            bullets.append(f"Home & roots (4th house {fourth}): family life feels {_sign_line(fourth)}.")
        if moon_sign:
            bullets.append(
                f"Moon in {moon_sign}: you recharge through {SIGN_THEMES.get(moon_sign, {}).get('gift', 'emotional honesty')}."
            )
        if sun_sign:
            bullets.append(
                f"Sun in {sun_sign}: your role in the family is to express {SIGN_THEMES.get(sun_sign, {}).get('gift', 'authenticity')}."
            )

        for asp in _natal_aspects(chart):
            if asp["p1"] in ("Moon", "Sun", "Saturn") or asp["p2"] in ("Moon", "Sun", "Saturn"):
                bullets.append(cls._aspect_plain(asp, prefix="Family pattern"))

        if dasha.get("current_mahadasha") in ("Moon", "Sun", "Saturn"):
            bullets.append(
                f"Long-term Vedic cycle ({dasha['current_mahadasha']}): family themes are especially active now."
            )

        summary = "Family is both anchor and mirror — your chart asks for honest conversations, not perfect harmony."
        return {"title": "Family & home", "summary": summary, "bullets": _bullets(bullets)}

    @classmethod
    def _kids(
        cls,
        *,
        natal_planets: dict[str, Any],
        natal_longs: dict[str, float],
        cusps: list[dict[str, Any]],
        **_: Any,
    ) -> dict[str, Any]:
        fifth = _cusp_sign({"western": {"houses": {"cusps": cusps}}}, 5)
        jupiter_sign = _planet_in_sign(natal_planets, "Jupiter")
        moon_sign = _planet_in_sign(natal_planets, "Moon")

        j_house = _house_of_planet(natal_longs.get("Jupiter", 0), cusps)
        bullets: list[str] = []

        if fifth:
            bullets.append(
                f"Children & creativity (5th house {fifth}): parenting/creative joy is {_sign_line(fifth)}."
            )
        if jupiter_sign:
            bullets.append(
                f"Jupiter in {jupiter_sign}: with children or projects you teach through {SIGN_THEMES.get(jupiter_sign, {}).get('gift', 'optimism')}."
            )
        if moon_sign:
            bullets.append(
                f"Moon in {moon_sign}: your nurturing style is {SIGN_THEMES.get(moon_sign, {}).get('tone', 'caring')} — kids feel your mood quickly."
            )
        if j_house == 5:
            bullets.append("Jupiter in the 5th house often blesses children, hobbies, or creative ventures with growth.")

        summary = (
            "Whether you have children or not, your 5th house is about what you create and mentor — "
            "make room for play and learning."
        )
        return {"title": "Children & creativity", "summary": summary, "bullets": _bullets(bullets)}

    @classmethod
    def _aspect_plain(cls, asp: dict[str, Any], prefix: str = "") -> str:
        p1, p2, aspect = asp["p1"], asp["p2"], asp["aspect"]
        tone = {
            "Conjunction": "blends closely with",
            "Trine": "flows easily with",
            "Sextile": "cooperates with",
            "Square": "pushes you to grow through tension with",
            "Opposition": "balances and polarizes with",
        }.get(aspect, "connects with")
        lead = f"{prefix}: " if prefix else ""
        return f"{lead}{p1} {tone} your natal {p2} (orb {asp.get('orb', '?')}°)."


