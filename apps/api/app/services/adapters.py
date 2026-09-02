"""Production-shaped adapters. Live IMD/Sentinel/LoRa sensors plug in here later."""
from __future__ import annotations

from datetime import datetime, timedelta


def mock_imd_satellite_timestamp() -> datetime:
    return datetime.utcnow() - timedelta(hours=6)


def mock_soil_probe(lat: float, lon: float, rainfall_proxy: float) -> dict:
    moisture = min(0.95, 0.2 + rainfall_proxy / 400.0 + (abs(lat) % 1) * 0.05)
    return {
        "source": "mock-lora-probe",
        "lat": lat,
        "lon": lon,
        "soil_moisture": round(moisture, 3),
        "battery": 0.91,
    }
