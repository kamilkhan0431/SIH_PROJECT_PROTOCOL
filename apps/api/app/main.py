from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

from fastapi import Body, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .auth import DEMO_USERS, get_current_user, make_token, optional_user, require_roles
from .config import settings
from .database import Base, engine, get_db
from .models import Alert, FieldReport, HistoricalEvent, Infra, RiskPrediction, Road, User, Village, Zone
from .seed import seed_if_empty
from .services import alerts as alert_service
from .services import risk_engine
from .services import weather as weather_service

app = FastAPI(title="SlopeSense NER API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_if_empty(db)
        weather_service.ingest_weather(db)
        risk_engine.score_all(db)
        alert_service.evaluate_alerts(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"ok": True, "product": "SlopeSense NER"}


@app.post("/auth/login")
def login(body: dict = Body(...), db: Session = Depends(get_db)):
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unknown demo user")
    return {
        "token": make_token(user),
        "user": {"username": user.username, "role": user.role, "display_name": user.display_name, "district": user.district},
    }


@app.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"username": user.username, "role": user.role, "display_name": user.display_name, "district": user.district}


@app.get("/auth/demo-users")
def demo_users():
    return [{"username": u["username"], "role": u["role"], "display_name": u["display_name"]} for u in DEMO_USERS]


def _fc(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


@app.get("/gis/states")
def gis_states():
    path = Path(settings.data_dir) / "ner_states.geojson"
    if not path.exists():
        return _fc([])
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/gis/risk")
def gis_risk(db: Session = Depends(get_db)):
    preds = {p.zone_id: p for p in db.query(RiskPrediction).all()}
    features = []
    for z in db.query(Zone).all():
        p = preds.get(z.id)
        geom = json.loads(z.geom_json)
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "id": z.id,
                    "name": z.name,
                    "state": z.state,
                    "district": z.district,
                    "severity": p.severity if p else "low",
                    "score": p.score if p else 0,
                    "slope_class": z.slope_class,
                    "rain_24h": z.rain_24h,
                    "rain_72h": z.rain_72h,
                    "rain_forecast_48h": z.rain_forecast_48h,
                    "soil_moisture": z.soil_moisture,
                    "inhabited": z.inhabited,
                    "highway": z.highway,
                },
            }
        )
    return _fc(features)


@app.get("/gis/villages")
def gis_villages(db: Session = Depends(get_db)):
    feats = []
    for v in db.query(Village).all():
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]},
                "properties": {"name": v.name, "state": v.state, "district": v.district, "population": v.population},
            }
        )
    return _fc(feats)


@app.get("/gis/roads")
def gis_roads(db: Session = Depends(get_db)):
    preds = {p.zone_id: p for p in db.query(RiskPrediction).all()}
    zones = db.query(Zone).all()
    feats = []
    for r in db.query(Road).all():
        geom = json.loads(r.geom_json)
        coords = geom.get("coordinates") or []
        derived = r.status
        if coords:
            mid = coords[len(coords) // 2]
            for z in zones:
                pr = preds.get(z.id)
                if pr and z.highway and abs(z.lon - mid[0]) < 0.1 and abs(z.lat - mid[1]) < 0.1:
                    if pr.severity == "severe":
                        derived = "blocked" if r.status == "blocked" else "at_risk"
                    elif pr.severity == "high" and derived == "open":
                        derived = "at_risk"
        feats.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {"id": r.id, "name": r.name, "status": r.status, "derived_status": derived},
            }
        )
    return _fc(feats)


@app.get("/gis/infrastructure")
def gis_infra(db: Session = Depends(get_db)):
    feats = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [i.lon, i.lat]},
            "properties": {"name": i.name, "kind": i.kind, "state": i.state},
        }
        for i in db.query(Infra).all()
    ]
    return _fc(feats)


@app.get("/gis/history")
def gis_history(db: Session = Depends(get_db)):
    feats = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [h.lon, h.lat]},
            "properties": {"name": h.name, "date": h.date, "state": h.state},
        }
        for h in db.query(HistoricalEvent).all()
    ]
    return _fc(feats)


@app.get("/gis/reports")
def gis_reports(status: str = "approved", db: Session = Depends(get_db)):
    q = db.query(FieldReport)
    if status != "all":
        q = q.filter(FieldReport.status == status)
    feats = []
    for r in q.all():
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r.lon, r.lat]},
                "properties": {
                    "id": r.id,
                    "type": r.type,
                    "status": r.status,
                    "description": r.description,
                    "media_path": r.media_path,
                    "created_at": r.created_at.isoformat(),
                },
            }
        )
    return _fc(feats)


@app.get("/zones/{zone_id}")
def zone_detail(zone_id: str, db: Session = Depends(get_db)):
    z = db.query(Zone).filter(Zone.id == zone_id).first()
    if not z:
        raise HTTPException(404, "Zone not found")
    pred = db.query(RiskPrediction).filter(RiskPrediction.zone_id == zone_id).first()
    nearby = (
        db.query(FieldReport)
        .filter(FieldReport.status == "approved")
        .all()
    )
    near = [r for r in nearby if abs(r.lat - z.lat) < 0.1 and abs(r.lon - z.lon) < 0.1]
    return {
        "id": z.id,
        "name": z.name,
        "state": z.state,
        "district": z.district,
        "lon": z.lon,
        "lat": z.lat,
        "slope_class": z.slope_class,
        "elevation_m": z.elevation_m,
        "soil_moisture": z.soil_moisture,
        "rain_24h": z.rain_24h,
        "rain_72h": z.rain_72h,
        "rain_forecast_48h": z.rain_forecast_48h,
        "lithology_proxy": z.lithology_proxy,
        "prior_landslide_density": z.prior_landslide_density,
        "ndvi_proxy": z.ndvi_proxy,
        "weather_updated_at": z.weather_updated_at.isoformat() if z.weather_updated_at else None,
        "satellite_updated_at": z.satellite_updated_at.isoformat() if z.satellite_updated_at else None,
        "severity": pred.severity if pred else None,
        "score": pred.score if pred else None,
        "explanation": json.loads(pred.explanation_json) if pred else None,
        "nearby_reports": [
            {"id": r.id, "type": r.type, "description": r.description, "lat": r.lat, "lon": r.lon} for r in near
        ],
    }


@app.post("/ingest/refresh")
def ingest_refresh(user: User = Depends(require_roles("district", "sdma", "field")), db: Session = Depends(get_db)):
    weather = weather_service.ingest_weather(db)
    risk = risk_engine.score_all(db)
    n_alerts = alert_service.evaluate_alerts(db)
    return {"weather": weather, "risk": risk, "alerts": n_alerts}


@app.get("/model/info")
def model_info():
    path = Path(settings.model_path)
    return {"loaded": path.exists(), "path": str(path), "classes": ["low", "moderate", "high", "severe"]}


@app.get("/reports")
def list_reports(
    status: str | None = None,
    user: User = Depends(optional_user),
    db: Session = Depends(get_db),
):
    q = db.query(FieldReport).order_by(FieldReport.created_at.desc())
    if status:
        q = q.filter(FieldReport.status == status)
    elif not user or user.role == "citizen":
        q = q.filter(FieldReport.status == "approved")
    rows = q.all()
    return [_report_out(r) for r in rows]


@app.post("/reports")
def create_report(
    type: str = Form(...),
    description: str = Form(""),
    lat: float = Form(...),
    lon: float = Form(...),
    client_id: str = Form(""),
    media: UploadFile | None = File(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if client_id:
        existing = db.query(FieldReport).filter(FieldReport.client_id == client_id).first()
        if existing:
            return _report_out(existing)
    media_path = ""
    media_type = ""
    if media and media.filename:
        ext = Path(media.filename).suffix.lower() or ".bin"
        fname = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{user.id}_{client_id[:8] or 'x'}{ext}"
        dest = Path(settings.upload_dir) / fname
        dest.write_bytes(media.file.read())
        media_path = f"/uploads/{fname}"
        media_type = "video" if ext in {".mp4", ".mov", ".webm"} else "photo"
    status = "approved" if user.role in ("field", "district", "sdma") else "pending"
    row = FieldReport(
        user_id=user.id,
        reporter_role=user.role,
        type=type,
        description=description,
        lat=lat,
        lon=lon,
        media_path=media_path,
        media_type=media_type,
        status=status,
        client_id=client_id,
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    if status == "approved":
        risk_engine.score_all(db)
        alert_service.evaluate_alerts(db)
    return _report_out(row)


@app.post("/reports/{report_id}/review")
def review_report(
    report_id: int,
    body: dict,
    user: User = Depends(require_roles("field", "district", "sdma")),
    db: Session = Depends(get_db),
):
    row = db.query(FieldReport).filter(FieldReport.id == report_id).first()
    if not row:
        raise HTTPException(404, "Report not found")
    decision = body.get("status")
    if decision not in ("approved", "rejected"):
        raise HTTPException(400, "status must be approved or rejected")
    row.status = decision
    db.commit()
    risk_engine.score_all(db)
    alert_service.evaluate_alerts(db)
    return _report_out(row)


def _report_out(r: FieldReport) -> dict:
    return {
        "id": r.id,
        "type": r.type,
        "description": r.description,
        "lat": r.lat,
        "lon": r.lon,
        "media_path": r.media_path,
        "media_type": r.media_type,
        "status": r.status,
        "reporter_role": r.reporter_role,
        "client_id": r.client_id,
        "created_at": r.created_at.isoformat(),
    }


@app.get("/alerts")
def list_alerts(lang: str = "en", db: Session = Depends(get_db)):
    rows = db.query(Alert).filter(Alert.active.is_(True)).order_by(Alert.created_at.desc()).all()
    key = {"en": "body_en", "hi": "body_hi", "as": "body_as", "bn": "body_bn"}.get(lang, "body_en")
    return [
        {
            "id": a.id,
            "rule": a.rule,
            "severity": a.severity,
            "title": a.title,
            "body": getattr(a, key),
            "body_en": a.body_en,
            "body_hi": a.body_hi,
            "body_as": a.body_as,
            "body_bn": a.body_bn,
            "audience": a.audience,
            "sms_status": a.sms_status,
            "created_at": a.created_at.isoformat(),
        }
        for a in rows
    ]


@app.get("/i18n/copy")
def i18n_copy():
    return alert_service.COPY


@app.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    preds = db.query(RiskPrediction).all()
    counts = {"low": 0, "moderate": 0, "high": 0, "severe": 0}
    by_state: dict[str, dict] = {}
    zones = {z.id: z for z in db.query(Zone).all()}
    for p in preds:
        counts[p.severity] = counts.get(p.severity, 0) + 1
        z = zones.get(p.zone_id)
        if not z:
            continue
        bucket = by_state.setdefault(z.state, {"low": 0, "moderate": 0, "high": 0, "severe": 0, "max_score": 0})
        bucket[p.severity] += 1
        bucket["max_score"] = max(bucket["max_score"], p.score)
    roads = db.query(Road).all()
    road_status = {"open": 0, "at_risk": 0, "blocked": 0}
    for r in roads:
        road_status[r.status] = road_status.get(r.status, 0) + 1
    alerts = db.query(Alert).filter(Alert.active.is_(True)).count()
    pending = db.query(FieldReport).filter(FieldReport.status == "pending").count()
    approved = db.query(FieldReport).filter(FieldReport.status == "approved").count()
    return {
        "risk_counts": counts,
        "by_state": by_state,
        "roads": road_status,
        "active_alerts": alerts,
        "pending_reports": pending,
        "approved_reports": approved,
        "updated_at": datetime.utcnow().isoformat(),
    }


@app.get("/dashboard/connectivity")
def dashboard_connectivity(db: Session = Depends(get_db)):
    roads_fc = gis_roads(db)
    villages = db.query(Village).all()
    blocked_near = []
    at_risk_near = []
    for feat in roads_fc["features"]:
        status = feat["properties"]["derived_status"]
        coords = feat["geometry"]["coordinates"]
        mid = coords[len(coords) // 2]
        touched = []
        for v in villages:
            if math.hypot(v.lon - mid[0], v.lat - mid[1]) < 0.35:
                touched.append({"name": v.name, "population": v.population, "district": v.district})
        item = {"road": feat["properties"]["name"], "status": status, "villages": touched}
        if status == "blocked":
            blocked_near.append(item)
        elif status == "at_risk":
            at_risk_near.append(item)
    return {"blocked": blocked_near, "at_risk": at_risk_near, "open_count": sum(1 for f in roads_fc["features"] if f["properties"]["derived_status"] == "open")}


@app.get("/dashboard/forecast")
def dashboard_forecast(db: Session = Depends(get_db)):
    rows = []
    preds = {p.zone_id: p for p in db.query(RiskPrediction).all()}
    for z in db.query(Zone).all():
        p = preds.get(z.id)
        bump = z.rain_forecast_48h > 40 and z.slope_class >= 4
        rows.append(
            {
                "zone_id": z.id,
                "name": z.name,
                "state": z.state,
                "district": z.district,
                "rain_24h": z.rain_24h,
                "rain_72h": z.rain_72h,
                "rain_forecast_48h": z.rain_forecast_48h,
                "severity": p.severity if p else "low",
                "score": p.score if p else 0,
                "forecast_bump": bump,
            }
        )
    rows.sort(key=lambda x: -x["rain_forecast_48h"])
    return {"zones": rows[:40], "weather_note": "Open-Meteo live rainfall with mock IMD/sensor adapters"}


@app.get("/dashboard/priority")
def dashboard_priority(db: Session = Depends(get_db)):
    preds = {p.zone_id: p for p in db.query(RiskPrediction).all()}
    items = []
    for z in db.query(Zone).all():
        p = preds.get(z.id)
        if not p or p.severity not in ("high", "severe"):
            continue
        pop = 0
        for v in db.query(Village).filter(Village.district == z.district).all():
            if abs(v.lat - z.lat) < 0.2 and abs(v.lon - z.lon) < 0.2:
                pop += v.population
        priority = p.score + (25 if z.inhabited else 0) + (15 if z.highway else 0) + min(pop / 8000.0, 20)
        items.append(
            {
                "zone_id": z.id,
                "name": z.name,
                "state": z.state,
                "district": z.district,
                "severity": p.severity,
                "score": p.score,
                "inhabited": z.inhabited,
                "highway": z.highway,
                "population_nearby": pop,
                "priority": round(priority, 1),
                "action": "Evacuate / restrict corridor" if p.severity == "severe" and z.inhabited else "Pre-position machinery and warn traffic",
            }
        )
    items.sort(key=lambda x: -x["priority"])
    return {"items": items[:30]}
