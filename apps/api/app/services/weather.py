from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from ..models import Zone

# Adapter contract: live Open-Meteo; IMD/sensor would share this shape.
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def _mock_for_zone(zone: Zone) -> tuple[float, float, float, float]:
    """Deterministic monsoon-ish mock if the network is unavailable."""
    seed = abs(hash(zone.id)) % 1000
    rain24 = 12 + (seed % 90) + zone.slope_class * 8
    rain72 = rain24 * 2.1 + (seed % 40)
    rainf = 8 + (seed % 55) + (10 if zone.slope_class >= 4 else 0)
    soil = min(0.92, zone.soil_moisture + rain72 / 900.0)
    return rain24, rain72, rainf, soil


def fetch_open_meteo(lat: float, lon: float) -> dict | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,soil_moisture_0_to_7cm",
        "forecast_days": 3,
        "past_days": 3,
        "timezone": "Asia/Kolkata",
    }
    try:
        with httpx.Client(timeout=12.0) as client:
            r = client.get(OPEN_METEO, params=params)
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def summarize_hourly(payload: dict) -> tuple[float, float, float, float]:
    hourly = payload.get("hourly") or {}
    precip = hourly.get("precipitation") or []
    soil = hourly.get("soil_moisture_0_to_7cm") or []
    times = hourly.get("time") or []
    now = datetime.now(timezone.utc)
    rain24 = rain72 = rainf = 0.0
    soil_now = 0.28
    for i, t in enumerate(times):
        try:
            ts = datetime.fromisoformat(t.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        val = float(precip[i] or 0) if i < len(precip) else 0.0
        delta = now - ts
        if timedelta(0) <= delta <= timedelta(hours=24):
            rain24 += val
        if timedelta(0) <= delta <= timedelta(hours=72):
            rain72 += val
        if timedelta(hours=-48) <= delta <= timedelta(0):
            rainf += val
        if soil and i < len(soil) and soil[i] is not None and abs(delta) < timedelta(hours=3):
            soil_now = float(soil[i])
    if soil and soil[-1] is not None:
        soil_now = float(soil[-1])
    return rain24, rain72, rainf, soil_now


def ingest_weather(db: Session) -> dict:
    corridors: dict[str, Zone] = {}
    for z in db.query(Zone).all():
        if z.corridor_id not in corridors:
            corridors[z.corridor_id] = z
    weather_by_corridor: dict[str, tuple[float, float, float, float]] = {}
    source = "open-meteo"
    for cid, sample in corridors.items():
        raw = fetch_open_meteo(sample.lat, sample.lon)
        if raw:
            weather_by_corridor[cid] = summarize_hourly(raw)
        else:
            source = "mock-open-meteo-fallback"
            weather_by_corridor[cid] = _mock_for_zone(sample)
    now = datetime.utcnow()
    sat = now - timedelta(hours=6)
    n = 0
    for z in db.query(Zone).all():
        rain24, rain72, rainf, soil = weather_by_corridor.get(z.corridor_id, _mock_for_zone(z))
        jitter = (abs(hash(z.id)) % 13) / 10.0
        z.rain_24h = round(max(0.0, rain24 + jitter - 0.6), 2)
        z.rain_72h = round(max(0.0, rain72 + jitter), 2)
        z.rain_forecast_48h = round(max(0.0, rainf), 2)
        z.soil_moisture = round(min(0.95, max(0.05, soil)), 3)
        z.weather_updated_at = now
        z.satellite_updated_at = sat
        n += 1
    db.commit()
    return {"zones": n, "source": source, "corridors": len(corridors)}
