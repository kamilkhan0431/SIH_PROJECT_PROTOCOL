from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from .auth import DEMO_USERS
from .config import settings
from .models import FieldReport, HistoricalEvent, Infra, Road, User, Village, Zone


def load_fc(name: str) -> dict:
    path = Path(settings.data_dir) / name
    if not path.exists():
        return {"features": []}
    return json.loads(path.read_text(encoding="utf-8"))


def seed_if_empty(db: Session) -> None:
    if db.query(User).count() == 0:
        for u in DEMO_USERS:
            db.add(User(**u, lang="en"))
        db.commit()
    if db.query(Zone).count() > 0:
        return
    for f in load_fc("risk_zones.geojson").get("features", []):
        p = f["properties"]
        db.add(
            Zone(
                id=p["id"],
                name=p["name"],
                corridor_id=p["corridor_id"],
                state=p["state"],
                district=p["district"],
                lon=p["lon"],
                lat=p["lat"],
                geom_json=json.dumps(f["geometry"]),
                slope_class=p["slope_class"],
                elevation_m=p["elevation_m"],
                soil_moisture=p["soil_moisture"],
                dist_drainage_km=p["dist_drainage_km"],
                lithology_proxy=p["lithology_proxy"],
                prior_landslide_density=p["prior_landslide_density"],
                ndvi_proxy=p["ndvi_proxy"],
                inhabited=p["inhabited"],
                highway=p["highway"],
                satellite_updated_at=datetime.utcnow() - timedelta(hours=6),
            )
        )
    for f in load_fc("villages.geojson").get("features", []):
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        db.add(Village(name=p["name"], state=p["state"], district=p["district"], lon=lon, lat=lat, population=p["population"]))
    for f in load_fc("roads.geojson").get("features", []):
        p = f["properties"]
        db.add(Road(id=p["id"], name=p["name"], status=p["status"], geom_json=json.dumps(f["geometry"])))
    for f in load_fc("infrastructure.geojson").get("features", []):
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        db.add(Infra(name=p["name"], kind=p["kind"], state=p["state"], lon=lon, lat=lat))
    for f in load_fc("historical_landslides.geojson").get("features", []):
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        db.add(HistoricalEvent(name=p["name"], date=p["date"], state=p["state"], lon=lon, lat=lat))
    db.commit()
    _seed_demo_reports(db)


def _seed_demo_reports(db: Session) -> None:
    field = db.query(User).filter(User.username == "field").first()
    citizen = db.query(User).filter(User.username == "citizen").first()
    if not field or not citizen:
        return
    samples = [
        (citizen.id, "citizen", "crack", 25.28, 91.74, "Fresh tension crack above Sohra road cut", "approved"),
        (field.id, "field", "blocked_road", 25.70, 94.05, "NH-29 boulder fall, one lane closed", "approved"),
        (citizen.id, "citizen", "slope_movement", 27.19, 88.54, "Downslope movement near Rangpo bazaar wall", "approved"),
        (field.id, "field", "blocked_road", 25.17, 93.02, "Haflong stretch muddy, HMV advised against", "pending"),
        (citizen.id, "citizen", "flash_flood", 24.83, 92.80, "Barak overbank near Silchar approach", "pending"),
    ]
    for uid, role, typ, lat, lon, desc, status in samples:
        db.add(
            FieldReport(
                user_id=uid,
                reporter_role=role,
                type=typ,
                description=desc,
                lat=lat,
                lon=lon,
                status=status,
                created_at=datetime.utcnow() - timedelta(hours=3),
            )
        )
    db.commit()
