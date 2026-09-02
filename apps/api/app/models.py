from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(32))
    display_name: Mapped[str] = mapped_column(String(128))
    district: Mapped[str] = mapped_column(String(128), default="East Khasi Hills")
    lang: Mapped[str] = mapped_column(String(8), default="en")


class Zone(Base):
    __tablename__ = "zones"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    corridor_id: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(64))
    district: Mapped[str] = mapped_column(String(128))
    lon: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    geom_json: Mapped[str] = mapped_column(Text)
    slope_class: Mapped[int] = mapped_column(Integer)
    elevation_m: Mapped[float] = mapped_column(Float)
    soil_moisture: Mapped[float] = mapped_column(Float)
    dist_drainage_km: Mapped[float] = mapped_column(Float)
    lithology_proxy: Mapped[float] = mapped_column(Float)
    prior_landslide_density: Mapped[float] = mapped_column(Float)
    ndvi_proxy: Mapped[float] = mapped_column(Float)
    inhabited: Mapped[bool] = mapped_column(Boolean, default=True)
    highway: Mapped[bool] = mapped_column(Boolean, default=False)
    rain_24h: Mapped[float] = mapped_column(Float, default=0)
    rain_72h: Mapped[float] = mapped_column(Float, default=0)
    rain_forecast_48h: Mapped[float] = mapped_column(Float, default=0)
    weather_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    satellite_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"))
    severity: Mapped[str] = mapped_column(String(16))
    score: Mapped[float] = mapped_column(Float)
    explanation_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    zone: Mapped[Zone] = relationship()


class Village(Base):
    __tablename__ = "villages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(String(64))
    district: Mapped[str] = mapped_column(String(128))
    lon: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    population: Mapped[int] = mapped_column(Integer)


class Road(Base):
    __tablename__ = "roads"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    geom_json: Mapped[str] = mapped_column(Text)


class Infra(Base):
    __tablename__ = "infrastructure"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(64))
    lon: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)


class HistoricalEvent(Base):
    __tablename__ = "historical_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    date: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(64))
    lon: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)


class FieldReport(Base):
    __tablename__ = "field_reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reporter_role: Mapped[str] = mapped_column(String(32))
    type: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text, default="")
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    media_path: Mapped[str] = mapped_column(String(512), default="")
    media_type: Mapped[str] = mapped_column(String(32), default="")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    client_id: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16))
    zone_id: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(256))
    body_en: Mapped[str] = mapped_column(Text)
    body_hi: Mapped[str] = mapped_column(Text)
    body_as: Mapped[str] = mapped_column(Text)
    body_bn: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(String(64), default="all")
    sms_status: Mapped[str] = mapped_column(String(32), default="logged")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
