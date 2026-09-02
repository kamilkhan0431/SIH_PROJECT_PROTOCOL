"""Generate demo GeoJSON for NER landslide corridors, villages, roads, infra, history."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
RNG = random.Random(42)

CORRIDORS = [
    {"id": "sikkim-nh10", "name": "NH-10 Sikkim corridor", "state": "Sikkim", "district": "East Sikkim", "lon": 88.53, "lat": 27.17, "slope": 4, "elev": 1400, "lithology": 0.78, "inhabited": True},
    {"id": "gangtok", "name": "Gangtok hills", "state": "Sikkim", "district": "Gangtok", "lon": 88.61, "lat": 27.33, "slope": 5, "elev": 1650, "lithology": 0.82, "inhabited": True},
    {"id": "barak", "name": "Barak valley / Haflong", "state": "Assam", "district": "Dima Hasao", "lon": 93.02, "lat": 25.17, "slope": 4, "elev": 680, "lithology": 0.71, "inhabited": True},
    {"id": "silchar", "name": "Silchar foothills", "state": "Assam", "district": "Cachar", "lon": 92.80, "lat": 24.83, "slope": 3, "elev": 120, "lithology": 0.45, "inhabited": True},
    {"id": "aizawl", "name": "Aizawl ridge", "state": "Mizoram", "district": "Aizawl", "lon": 92.72, "lat": 23.73, "slope": 5, "elev": 1130, "lithology": 0.80, "inhabited": True},
    {"id": "kohima", "name": "Kohima–Dimapur", "state": "Nagaland", "district": "Kohima", "lon": 94.11, "lat": 25.67, "slope": 4, "elev": 1440, "lithology": 0.74, "inhabited": True},
    {"id": "dimapur", "name": "Dimapur plains edge", "state": "Nagaland", "district": "Dimapur", "lon": 93.73, "lat": 25.91, "slope": 2, "elev": 160, "lithology": 0.32, "inhabited": True},
    {"id": "tawang", "name": "Tawang approach", "state": "Arunachal Pradesh", "district": "Tawang", "lon": 91.87, "lat": 27.59, "slope": 5, "elev": 2800, "lithology": 0.69, "inhabited": True},
    {"id": "itanagar", "name": "Itanagar–Ziro", "state": "Arunachal Pradesh", "district": "Papum Pare", "lon": 93.62, "lat": 27.08, "slope": 4, "elev": 320, "lithology": 0.61, "inhabited": True},
    {"id": "shillong", "name": "Shillong–Cherrapunji", "state": "Meghalaya", "district": "East Khasi Hills", "lon": 91.88, "lat": 25.47, "slope": 4, "elev": 1490, "lithology": 0.66, "inhabited": True},
    {"id": "cherrapunji", "name": "Sohra escarpment", "state": "Meghalaya", "district": "East Khasi Hills", "lon": 91.73, "lat": 25.27, "slope": 5, "elev": 1480, "lithology": 0.70, "inhabited": True},
    {"id": "imphal", "name": "Imphal hills", "state": "Manipur", "district": "Imphal East", "lon": 94.00, "lat": 24.82, "slope": 3, "elev": 790, "lithology": 0.58, "inhabited": True},
    {"id": "ukhrul", "name": "Ukhrul ridge", "state": "Manipur", "district": "Ukhrul", "lon": 94.36, "lat": 25.12, "slope": 4, "elev": 1660, "lithology": 0.72, "inhabited": True},
    {"id": "agartala", "name": "Tripura hills", "state": "Tripura", "district": "West Tripura", "lon": 91.29, "lat": 23.83, "slope": 2, "elev": 45, "lithology": 0.38, "inhabited": True},
    {"id": "dhalai", "name": "Dhalai uplands", "state": "Tripura", "district": "Dhalai", "lon": 91.94, "lat": 23.84, "slope": 3, "elev": 220, "lithology": 0.52, "inhabited": False},
    {"id": "lunglei", "name": "Lunglei hills", "state": "Mizoram", "district": "Lunglei", "lon": 92.73, "lat": 22.88, "slope": 4, "elev": 720, "lithology": 0.67, "inhabited": True},
]

STATE_POLYS = {
    "Arunachal Pradesh": [[91.6, 26.6], [97.4, 26.6], [97.4, 29.4], [91.6, 29.4], [91.6, 26.6]],
    "Assam": [[89.7, 24.1], [96.0, 24.1], [96.0, 27.9], [89.7, 27.9], [89.7, 24.1]],
    "Manipur": [[93.0, 23.8], [94.8, 23.8], [94.8, 25.7], [93.0, 25.7], [93.0, 23.8]],
    "Meghalaya": [[89.8, 25.0], [92.8, 25.0], [92.8, 26.1], [89.8, 26.1], [89.8, 25.0]],
    "Mizoram": [[92.2, 21.9], [93.5, 21.9], [93.5, 24.5], [92.2, 24.5], [92.2, 21.9]],
    "Nagaland": [[93.3, 25.2], [95.3, 25.2], [95.3, 27.0], [93.3, 27.0], [93.3, 25.2]],
    "Sikkim": [[88.0, 27.0], [88.9, 27.0], [88.9, 28.1], [88.0, 28.1], [88.0, 27.0]],
    "Tripura": [[91.1, 22.9], [92.3, 22.9], [92.3, 24.5], [91.1, 24.5], [91.1, 22.9]],
}

VILLAGES = [
    ("Rangpo", "Sikkim", "East Sikkim", 88.53, 27.17, 4200),
    ("Singtam", "Sikkim", "East Sikkim", 88.50, 27.23, 5860),
    ("Gangtok", "Sikkim", "Gangtok", 88.61, 27.33, 100286),
    ("Haflong", "Assam", "Dima Hasao", 93.02, 25.17, 43600),
    ("Silchar", "Assam", "Cachar", 92.80, 24.83, 228985),
    ("Aizawl", "Mizoram", "Aizawl", 92.72, 23.73, 293416),
    ("Kohima", "Nagaland", "Kohima", 94.11, 25.67, 99039),
    ("Dimapur", "Nagaland", "Dimapur", 93.73, 25.91, 122834),
    ("Tawang", "Arunachal Pradesh", "Tawang", 91.87, 27.59, 11202),
    ("Itanagar", "Arunachal Pradesh", "Papum Pare", 93.62, 27.08, 59490),
    ("Shillong", "Meghalaya", "East Khasi Hills", 91.88, 25.57, 143229),
    ("Sohra", "Meghalaya", "East Khasi Hills", 91.73, 25.27, 11721),
    ("Imphal", "Manipur", "Imphal West", 93.94, 24.81, 268243),
    ("Ukhrul", "Manipur", "Ukhrul", 94.36, 25.12, 27200),
    ("Agartala", "Tripura", "West Tripura", 91.29, 23.83, 400004),
    ("Lunglei", "Mizoram", "Lunglei", 92.73, 22.88, 57000),
    ("Mawlynnong", "Meghalaya", "East Khasi Hills", 91.92, 25.20, 530),
    ("Ziro", "Arunachal Pradesh", "Lower Subansiri", 93.83, 27.63, 12890),
]

ROADS = [
    {"id": "nh10", "name": "NH-10", "status": "open", "coords": [[88.43, 26.89], [88.50, 27.05], [88.53, 27.17], [88.57, 27.25], [88.61, 27.33]]},
    {"id": "nh6-barak", "name": "NH-6 Barak", "status": "at_risk", "coords": [[92.80, 24.83], [92.90, 25.00], [93.02, 25.17], [93.20, 25.40]]},
    {"id": "nh2-mizoram", "name": "NH-2 Mizoram", "status": "open", "coords": [[92.72, 23.73], [92.73, 23.30], [92.73, 22.88]]},
    {"id": "nh29", "name": "NH-29 Kohima–Dimapur", "status": "blocked", "coords": [[93.73, 25.91], [93.90, 25.80], [94.11, 25.67]]},
    {"id": "nh13-tawang", "name": "Tawang highway", "status": "at_risk", "coords": [[92.40, 27.20], [92.10, 27.40], [91.87, 27.59]]},
    {"id": "nh6-khasi", "name": "Shillong–Sohra", "status": "open", "coords": [[91.88, 25.57], [91.82, 25.42], [91.73, 25.27]]},
    {"id": "nh2-manipur", "name": "NH-2 Imphal–Kohima", "status": "open", "coords": [[93.94, 24.81], [94.05, 25.20], [94.11, 25.67]]},
    {"id": "nh8-tripura", "name": "NH-8 Tripura", "status": "open", "coords": [[91.29, 23.83], [91.50, 23.84], [91.94, 23.84]]},
    {"id": "nh15-itanagar", "name": "Itanagar–Ziro", "status": "at_risk", "coords": [[93.62, 27.08], [93.72, 27.35], [93.83, 27.63]]},
]

INFRA = [
    ("STNM Hospital", "hospital", 88.61, 27.33, "Sikkim"),
    ("NEIGRIHMS", "hospital", 91.89, 25.58, "Meghalaya"),
    ("RIMS Imphal", "hospital", 93.93, 24.81, "Manipur"),
    ("Civil Hospital Aizawl", "hospital", 92.72, 23.73, "Mizoram"),
    ("Teesta bridge Rangpo", "bridge", 88.53, 27.17, "Sikkim"),
    ("Barak bridge Silchar", "bridge", 92.80, 24.83, "Assam"),
    ("Dzukou approach bridge", "bridge", 94.08, 25.60, "Nagaland"),
    ("Sohra viewpoint roadhead", "bridge", 91.73, 25.27, "Meghalaya"),
    ("SDMA Gangtok", "command", 88.61, 27.32, "Sikkim"),
    ("SEOC Shillong", "command", 91.88, 25.57, "Meghalaya"),
]

HISTORY = [
    ("2019-09-14", "NH-10 debris slide", 88.54, 27.19, "Sikkim"),
    ("2021-10-20", "Chanmari slope failure", 88.61, 27.34, "Sikkim"),
    ("2018-06-11", "Haflong cut-slope", 93.03, 25.18, "Assam"),
    ("2022-07-03", "Aizawl ramhlun crack", 92.73, 23.74, "Mizoram"),
    ("2020-08-19", "Kohima NH-29 blockage", 94.05, 25.70, "Nagaland"),
    ("2017-07-22", "Tawang highway slide", 91.90, 27.56, "Arunachal Pradesh"),
    ("2023-06-16", "Sohra escarpment rockfall", 91.74, 25.28, "Meghalaya"),
    ("2016-08-02", "Ukhrul ridge slide", 94.35, 25.13, "Manipur"),
    ("2024-05-28", "East Khasi Hills monsoon cluster", 91.85, 25.40, "Meghalaya"),
    ("2015-09-09", "South Sikkim village slide", 88.40, 27.16, "Sikkim"),
    ("2021-06-30", "Lunglei hillside", 92.74, 22.89, "Mizoram"),
    ("2019-07-18", "Papum Pare valley wall", 93.63, 27.10, "Arunachal Pradesh"),
]


def square(lon: float, lat: float, half: float = 0.035) -> list[list[float]]:
    return [
        [lon - half, lat - half],
        [lon + half, lat - half],
        [lon + half, lat + half],
        [lon - half, lat + half],
        [lon - half, lat - half],
    ]


def fc(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def feat(geom: dict, props: dict) -> dict:
    return {"type": "Feature", "geometry": geom, "properties": props}


def write(name: str, obj: dict) -> None:
    path = DATA / name
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(f"wrote {path}")


def zone_grid() -> dict:
    features = []
    idx = 0
    for c in CORRIDORS:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                lon = c["lon"] + dx * 0.07
                lat = c["lat"] + dy * 0.06
                slope = max(1, min(5, int(round(c["slope"] + RNG.choice([-1, 0, 0, 1])))))
                elev = max(20, int(c["elev"] + dy * 80 + RNG.randint(-60, 60)))
                drain = abs(dx) * 0.8 + abs(dy) * 0.6 + RNG.random() * 0.4
                prior = 0.0
                for rec in HISTORY:
                    hlon, hlat = rec[2], rec[3]
                    dist = math.hypot(lon - hlon, lat - hlat)
                    if dist < 0.25:
                        prior += max(0.0, 1.0 - dist / 0.25)
                inhabited = c["inhabited"] and abs(dx) + abs(dy) <= 3
                idx += 1
                zid = f"z-{c['id']}-{dx+2}{dy+2}"
                features.append(
                    feat(
                        {"type": "Polygon", "coordinates": [square(lon, lat)]},
                        {
                            "id": zid,
                            "name": f"{c['name']} cell {dx:+d},{dy:+d}",
                            "corridor_id": c["id"],
                            "state": c["state"],
                            "district": c["district"],
                            "lon": round(lon, 5),
                            "lat": round(lat, 5),
                            "slope_class": slope,
                            "elevation_m": elev,
                            "soil_moisture": round(0.25 + slope * 0.06 + RNG.random() * 0.15, 3),
                            "dist_drainage_km": round(drain, 2),
                            "lithology_proxy": round(min(1.0, max(0.1, c["lithology"] + RNG.uniform(-0.1, 0.1))), 3),
                            "prior_landslide_density": round(min(3.0, prior), 3),
                            "ndvi_proxy": round(0.35 + RNG.random() * 0.4, 3),
                            "inhabited": inhabited,
                            "highway": abs(dx) <= 1 and abs(dy) <= 1,
                        },
                    )
                )
    return fc(features)


def main() -> None:
    write(
        "ner_states.geojson",
        fc(
            [
                feat({"type": "Polygon", "coordinates": [coords]}, {"name": name})
                for name, coords in STATE_POLYS.items()
            ]
        ),
    )
    write("risk_zones.geojson", zone_grid())
    write(
        "villages.geojson",
        fc(
            [
                feat(
                    {"type": "Point", "coordinates": [lon, lat]},
                    {"name": n, "state": s, "district": d, "population": p},
                )
                for n, s, d, lon, lat, p in VILLAGES
            ]
        ),
    )
    write(
        "roads.geojson",
        fc(
            [
                feat(
                    {"type": "LineString", "coordinates": r["coords"]},
                    {"id": r["id"], "name": r["name"], "status": r["status"]},
                )
                for r in ROADS
            ]
        ),
    )
    write(
        "infrastructure.geojson",
        fc(
            [
                feat(
                    {"type": "Point", "coordinates": [lon, lat]},
                    {"name": n, "kind": k, "state": st},
                )
                for n, k, lon, lat, st in INFRA
            ]
        ),
    )
    write(
        "historical_landslides.geojson",
        fc(
            [
                feat(
                    {"type": "Point", "coordinates": [lon, lat]},
                    {"date": dt, "name": n, "state": st},
                )
                for dt, n, lon, lat, st in HISTORY
            ]
        ),
    )
    print("GIS seed complete.")


if __name__ == "__main__":
    main()
