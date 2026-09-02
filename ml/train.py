"""Train a 4-class landslide risk model on corridor-style synthetic labels."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "risk_zones.geojson"
OUT = Path(__file__).resolve().parent
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
LABELS = ["low", "moderate", "high", "severe"]


def latent_score(row: dict, rain24: float, rain72: float, rainf: float, reports: float) -> float:
    s = (
        0.22 * min(rain24 / 120.0, 1.5)
        + 0.18 * min(rain72 / 250.0, 1.5)
        + 0.12 * min(rainf / 80.0, 1.4)
        + 0.16 * (row["slope_class"] / 5.0)
        + 0.10 * row["soil_moisture"]
        + 0.08 * row["lithology_proxy"]
        + 0.08 * min(row["prior_landslide_density"] / 2.0, 1.2)
        + 0.04 * min(reports / 5.0, 1.0)
        + 0.03 * (1.0 - min(row["ndvi_proxy"], 1.0))
        + 0.04 * (1.0 / (1.0 + row["dist_drainage_km"]))
    )
    if row["elevation_m"] > 1200:
        s += 0.04
    return s


def label_from_score(score: float) -> str:
    if score >= 0.72:
        return "severe"
    if score >= 0.55:
        return "high"
    if score >= 0.38:
        return "moderate"
    return "low"


def build_matrix() -> tuple[np.ndarray, np.ndarray]:
    zones = json.loads(DATA.read_text(encoding="utf-8"))["features"]
    rng = np.random.default_rng(7)
    X, y = [], []
    for feat in zones:
        p = feat["properties"]
        for _ in range(8):
            rain24 = float(max(0.0, rng.gamma(2.2, 18.0)))
            rain72 = rain24 + float(max(0.0, rng.gamma(2.4, 28.0)))
            rainf = float(max(0.0, rng.gamma(1.8, 12.0)))
            reports = float(rng.poisson(0.4 + p["prior_landslide_density"]))
            soil = float(np.clip(p["soil_moisture"] + rain72 / 800.0 + rng.normal(0, 0.04), 0.05, 0.95))
            score = latent_score(p, rain24, rain72, rainf, reports) + float(rng.normal(0, 0.05))
            row = [
                rain24,
                rain72,
                rainf,
                float(p["slope_class"]),
                float(p["elevation_m"]),
                soil,
                float(p["dist_drainage_km"]),
                float(p["lithology_proxy"]),
                float(p["prior_landslide_density"]),
                reports,
                float(p["ndvi_proxy"]),
            ]
            X.append(row)
            y.append(label_from_score(score))
    return np.array(X, dtype=float), np.array(y)


def main() -> None:
    if not DATA.exists():
        raise SystemExit("Run python ml/generate_gis.py first")
    X, y = build_matrix()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf = GradientBoostingClassifier(random_state=42, n_estimators=160, max_depth=3, learning_rate=0.08)
    clf.fit(Xtr, ytr)
    print(classification_report(yte, clf.predict(Xte), labels=LABELS))
    bundle = {
        "model": clf,
        "features": FEATURES,
        "labels": list(clf.classes_),
        "importances": dict(zip(FEATURES, [float(x) for x in clf.feature_importances_])),
    }
    joblib.dump(bundle, OUT / "model.joblib")
    (OUT / "features.json").write_text(json.dumps({"features": FEATURES, "labels": LABELS, "importances": bundle["importances"]}, indent=2), encoding="utf-8")
    print(f"saved {OUT / 'model.joblib'}")


if __name__ == "__main__":
    main()
