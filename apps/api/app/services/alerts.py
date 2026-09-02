from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Alert, FieldReport, RiskPrediction, Road, Village, Zone

COPY = {
    "severe_inhabited": {
        "title": "Severe landslide risk — inhabited cell",
        "en": "Severe landslide likelihood in {place}. Move away from cut slopes. District control room is notified.",
        "hi": "{place} में गंभीर भूस्खलन जोखिम। ढलानों से दूर रहें। जिला नियंत्रण कक्ष को सूचना दे दी गई है।",
        "as": "{place}ত গুৰুতৰ ভূমিস্খলনৰ আশংকা। ঢালৰ পৰা আতৰি থাকক।",
        "bn": "{place}-এ গুরুতর ভূমিধসের ঝুঁকি। ঢাল থেকে দূরে থাকুন।",
    },
    "high_highway": {
        "title": "Highway at high landslide risk",
        "en": "{road} may close. High risk on adjoining slopes after recent / forecast rain.",
        "hi": "{road} बंद हो सकता है। वर्षा के बाद ढलानों पर उच्च जोखिम।",
        "as": "{road} বন্ধ হ’ব পাৰে। শেহতীয়া বৰষুণৰ পিছত ঢালত উচ্চ বিপদ।",
        "bn": "{road} বন্ধ হতে পারে। বৃষ্টির পর ঢালে উচ্চ ঝুঁকি।",
    },
    "report_cluster": {
        "title": "Field reports clustered",
        "en": "Multiple approved ground reports near {place}. Treat as a developing incident.",
        "hi": "{place} के पास कई स्वीकृत मैदानी रिपोर्ट। घटना विकसित हो सकती है।",
        "as": "{place}ৰ ওচৰত একাধিক অনুমোদিত স্থানীয় প্ৰতিবেদন।",
        "bn": "{place}-এর কাছে একাধিক অনুমোদিত মাঠ প্রতিবেদন।",
    },
}


def _sms(alert: Alert) -> str:
    if settings.sms_provider == "msg91" and settings.msg91_key:
        return "queued-msg91"
    return "logged-stub"


def evaluate_alerts(db: Session) -> int:
    db.query(Alert).filter(Alert.active.is_(True)).update({"active": False})
    created = 0
    preds = db.query(RiskPrediction).all()
    pred_by_zone = {p.zone_id: p for p in preds}
    zones = {z.id: z for z in db.query(Zone).all()}
    roads = db.query(Road).all()
    reports = db.query(FieldReport).filter(FieldReport.status == "approved").all()

    for z in zones.values():
        p = pred_by_zone.get(z.id)
        if not p:
            continue
        if p.severity == "severe" and z.inhabited:
            village = (
                db.query(Village)
                .filter(Village.district == z.district)
                .first()
            )
            place = village.name if village else z.name
            spec = COPY["severe_inhabited"]
            alert = Alert(
                rule="severe_inhabited",
                severity="severe",
                zone_id=z.id,
                title=spec["title"],
                body_en=spec["en"].format(place=place),
                body_hi=spec["hi"].format(place=place),
                body_as=spec["as"].format(place=place),
                body_bn=spec["bn"].format(place=place),
                audience="district,sdma,field",
                created_at=datetime.utcnow(),
                active=True,
            )
            alert.sms_status = _sms(alert)
            db.add(alert)
            created += 1

    for road in roads:
        geom = json.loads(road.geom_json)
        coords = geom.get("coordinates") or []
        if not coords:
            continue
        mid = coords[len(coords) // 2]
        nearby_high = False
        for z in zones.values():
            if abs(z.lon - mid[0]) < 0.12 and abs(z.lat - mid[1]) < 0.12:
                p = pred_by_zone.get(z.id)
                if p and p.severity in ("high", "severe") and z.highway:
                    nearby_high = True
                    break
        if nearby_high or road.status == "blocked":
            spec = COPY["high_highway"]
            alert = Alert(
                rule="high_highway",
                severity="high" if road.status != "blocked" else "severe",
                zone_id="",
                title=spec["title"],
                body_en=spec["en"].format(road=road.name),
                body_hi=spec["hi"].format(road=road.name),
                body_as=spec["as"].format(road=road.name),
                body_bn=spec["bn"].format(road=road.name),
                audience="all",
                created_at=datetime.utcnow(),
                active=True,
            )
            alert.sms_status = _sms(alert)
            db.add(alert)
            created += 1

    clusters: dict[str, list[FieldReport]] = {}
    for r in reports:
        key = f"{round(r.lat, 1)}:{round(r.lon, 1)}"
        clusters.setdefault(key, []).append(r)
    for items in clusters.values():
        if len(items) >= 3:
            spec = COPY["report_cluster"]
            place = f"{items[0].lat:.2f}N {items[0].lon:.2f}E"
            alert = Alert(
                rule="report_cluster",
                severity="high",
                zone_id="",
                title=spec["title"],
                body_en=spec["en"].format(place=place),
                body_hi=spec["hi"].format(place=place),
                body_as=spec["as"].format(place=place),
                body_bn=spec["bn"].format(place=place),
                audience="field,district,sdma",
                created_at=datetime.utcnow(),
                active=True,
            )
            alert.sms_status = _sms(alert)
            db.add(alert)
            created += 1

    db.commit()
    return created
