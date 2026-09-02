from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session

from ..config import settings
from ..models import FieldReport, RiskPrediction, Zone

FEATURES = [
    "rain_24h",
    "rain_72h",
    "rain_forecast_48h",
    "slope_class",
    "elevation_m",
    "soil_moisture",
    "dist_drainage_km",
    "lithology_proxy",
    "prior_landslide_density",
    "nearby_reports",
    "ndvi_proxy",
]
ORDER = {"low": 0, "moderate": 1, "high": 2, "severe": 3}


def _load_model():
    path = Path(settings.model_path)
    if not path.exists():
        return None
    return joblib.load(path)


def nearby_report_count(db: Session, zone: Zone) -> float:
    reports = db.query(FieldReport).filter(FieldReport.status == "approved").all()
    n = 0
    for r in reports:
        if abs(r.lat - zone.lat) < 0.08 and abs(r.lon - zone.lon) < 0.08:
            n += 1
    return float(n)


def feature_row(zone: Zone, reports: float) -> list[float]:
    return [
        zone.rain_24h,
        zone.rain_72h,
        zone.rain_forecast_48h,
        float(zone.slope_class),
        zone.elevation_m,
        zone.soil_moisture,
        zone.dist_drainage_km,
        zone.lithology_proxy,
        zone.prior_landslide_density,
        reports,
        zone.ndvi_proxy,
    ]


def heuristic_score(row: list[float]) -> tuple[str, float]:
    rain24, rain72, rainf, slope, elev, soil, drain, lith, prior, reports, ndvi = row
    s = (
        0.22 * min(rain24 / 120.0, 1.5)
        + 0.18 * min(rain72 / 250.0, 1.5)
        + 0.12 * min(rainf / 80.0, 1.4)
        + 0.16 * (slope / 5.0)
        + 0.10 * soil
        + 0.08 * lith
        + 0.08 * min(prior / 2.0, 1.2)
        + 0.04 * min(reports / 5.0, 1.0)
        + 0.03 * (1.0 - min(ndvi, 1.0))
        + 0.04 * (1.0 / (1.0 + drain))
    )
    if elev > 1200:
        s += 0.04
    if rainf > 40 and slope >= 4:
        s += 0.08
    score = float(min(1.0, max(0.0, s)))
    if score >= 0.72:
        sev = "severe"
    elif score >= 0.55:
        sev = "high"
    elif score >= 0.38:
        sev = "moderate"
    else:
        sev = "low"
    return sev, round(score * 100, 1)


def explain(row: list[float], importances: dict[str, float] | None, severity: str) -> dict:
    named = dict(zip(FEATURES, row))
    drivers = []
    weights = importances or {
        "rain_72h": 0.2,
        "rain_24h": 0.18,
        "slope_class": 0.16,
        "soil_moisture": 0.12,
        "rain_forecast_48h": 0.1,
        "prior_landslide_density": 0.08,
        "lithology_proxy": 0.07,
        "nearby_reports": 0.05,
        "dist_drainage_km": 0.02,
        "ndvi_proxy": 0.01,
        "elevation_m": 0.01,
    }
    for k, w in sorted(weights.items(), key=lambda kv: -kv[1])[:6]:
        drivers.append({"feature": k, "value": named.get(k), "importance": round(float(w), 4)})
    why = []
    if named["rain_72h"] > 80:
        why.append("72-hour rainfall is elevated on this slope cell")
    if named["slope_class"] >= 4:
        why.append("Steep slope class (4–5) from corridor terrain proxy")
    if named["soil_moisture"] > 0.45:
        why.append("Soil moisture is high (sensor adapter / Open-Meteo soil layer)")
    if named["prior_landslide_density"] > 0.4:
        why.append("Historical landslide density nearby")
    if named["rain_forecast_48h"] > 35 and named["slope_class"] >= 4:
        why.append("Forecast rain on an already steep cell — severity bump rule")
    if named["nearby_reports"] >= 2:
        why.append("Approved field reports clustered in this cell")
    if not why:
        why.append("Composite rainfall, terrain, and history features are within moderate bounds")
    return {"severity": severity, "drivers": drivers, "why": why, "features": named}


def score_all(db: Session) -> dict:
    bundle = _load_model()
    model = bundle["model"] if bundle else None
    labels = list(bundle["labels"]) if bundle else ["high", "low", "moderate", "severe"]
    importances = bundle.get("importances") if bundle else None
    db.query(RiskPrediction).delete()
    counts = {"low": 0, "moderate": 0, "high": 0, "severe": 0}
    for zone in db.query(Zone).all():
        reports = nearby_report_count(db, zone)
        row = feature_row(zone, reports)
        if model is not None:
            X = np.array([row], dtype=float)
            proba = model.predict_proba(X)[0]
            pred = str(model.predict(X)[0])
            idx = labels.index(pred) if pred in labels else int(np.argmax(proba))
            score = float(proba[idx] * 40 + ORDER.get(pred, 0) * 20)
            if zone.rain_forecast_48h > 40 and zone.slope_class >= 4 and ORDER.get(pred, 0) < 3:
                bumped = [k for k, v in ORDER.items() if v == ORDER.get(pred, 0) + 1][0]
                pred = bumped
                score = min(99.0, score + 12)
            severity = pred
        else:
            severity, score = heuristic_score(row)
        if zone.rain_forecast_48h > 50 and zone.slope_class >= 4 and ORDER[severity] < 3:
            severity = [k for k, v in ORDER.items() if v == ORDER[severity] + 1][0]
            score = min(99.0, score + 8)
        explanation = explain(row, importances, severity)
        db.add(
            RiskPrediction(
                zone_id=zone.id,
                severity=severity,
                score=round(float(score), 1),
                explanation_json=json.dumps(explanation),
                created_at=datetime.utcnow(),
            )
        )
        counts[severity] = counts.get(severity, 0) + 1
    db.commit()
    return {"model": bool(model), "counts": counts}
