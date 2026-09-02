"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { Map, Popup } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { API, apiGet } from "@/lib/api";
import { cacheJson, readCache } from "@/lib/offline";

type ZoneInfo = {
  id: string;
  name: string;
  state: string;
  district: string;
  slope_class: number;
  rain_24h: number;
  rain_72h: number;
  rain_forecast_48h: number;
  soil_moisture: number;
  weather_updated_at: string | null;
  satellite_updated_at: string | null;
  severity: string;
  score: number;
  explanation: { why: string[]; drivers: { feature: string; value: number; importance: number }[] };
  nearby_reports: { id: number; type: string; description: string }[];
};

type FC = { type: "FeatureCollection"; features: unknown[] };

const COLORS: Record<string, string> = {
  low: "#c5d4a8",
  moderate: "#e0b45a",
  high: "#d46a3a",
  severe: "#8b1e1e",
};

export function MapView() {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const detailRef = useRef<(z: ZoneInfo) => void>(() => undefined);
  const [detail, setDetail] = useState<ZoneInfo | null>(null);
  const [layers, setLayers] = useState({ villages: true, roads: true, infra: true, reports: true, history: false, weather: true });
  const [err, setErr] = useState("");
  detailRef.current = setDetail;

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center: [93.2, 25.6],
      zoom: 5.4,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", async () => {
      try {
        const [risk, villages, roads, infra, history, reports] = await Promise.all([
          apiGet<FC>("/gis/risk"),
          apiGet<FC>("/gis/villages"),
          apiGet<FC>("/gis/roads"),
          apiGet<FC>("/gis/infrastructure"),
          apiGet<FC>("/gis/history"),
          apiGet<FC>("/gis/reports"),
        ]);
        await cacheJson("risk", risk);
        addLayers(map, { risk, villages, roads, infra, history, reports }, (z) => detailRef.current(z));
      } catch {
        const risk = await readCache<FC>("risk");
        if (risk) addLayers(map, { risk, villages: empty(), roads: empty(), infra: empty(), history: empty(), reports: empty() }, (z) => detailRef.current(z));
        else setErr("Could not reach the API. Start FastAPI on port 8000.");
      }
    });
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getLayer("villages")) return;
    const vis = (on: boolean) => (on ? "visible" : "none");
    map.setLayoutProperty("villages", "visibility", vis(layers.villages));
    map.setLayoutProperty("roads", "visibility", vis(layers.roads));
    map.setLayoutProperty("infra", "visibility", vis(layers.infra));
    map.setLayoutProperty("reports", "visibility", vis(layers.reports));
    map.setLayoutProperty("history", "visibility", vis(layers.history));
    if (map.getLayer("weather-rain")) map.setLayoutProperty("weather-rain", "visibility", vis(layers.weather));
  }, [layers]);

  return (
    <div className="map-wrap">
      <div ref={ref} className="map-canvas" />
      <aside className="map-legend">
        <h2>Risk heatmap</h2>
        {Object.entries(COLORS).map(([k, c]) => (
          <div key={k} className="leg">
            <i style={{ background: c }} /> {k}
          </div>
        ))}
        <h3>Layers</h3>
        {(
          [
            ["villages", "Villages"],
            ["roads", "Roads"],
            ["infra", "Critical infra"],
            ["reports", "Field pins"],
            ["history", "Past slides"],
            ["weather", "Rain overlay"],
          ] as const
        ).map(([k, label]) => (
          <label key={k} className="chk">
            <input type="checkbox" checked={layers[k]} onChange={() => setLayers({ ...layers, [k]: !layers[k] })} />
            {label}
          </label>
        ))}
        {err ? <p className="warn">{err}</p> : null}
        {detail ? (
          <div className="why">
            <h3>{detail.name}</h3>
            <p>
              {detail.district}, {detail.state}
            </p>
            <p>
              <b>{detail.severity}</b> · score {detail.score}
            </p>
            <ul>
              <li>24h rain {detail.rain_24h} mm</li>
              <li>72h rain {detail.rain_72h} mm</li>
              <li>48h forecast {detail.rain_forecast_48h} mm</li>
              <li>Soil moisture {detail.soil_moisture}</li>
              <li>Slope class {detail.slope_class}</li>
              <li>Weather {detail.weather_updated_at || "—"}</li>
              <li>Satellite (mock IMD) {detail.satellite_updated_at || "—"}</li>
            </ul>
            <h4>Why this zone</h4>
            <ul>
              {(detail.explanation?.why || []).map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="hint">Click a risk cell for rainfall, soil, model score, and nearby reports.</p>
        )}
      </aside>
    </div>
  );
}

function empty(): FC {
  return { type: "FeatureCollection", features: [] };
}

function addLayers(map: Map, data: Record<string, FC>, onZone: (z: ZoneInfo) => void) {
  const add = (id: string, fc: FC) => {
    if (map.getSource(id)) (map.getSource(id) as maplibregl.GeoJSONSource).setData(fc as never);
    else map.addSource(id, { type: "geojson", data: fc as never });
  };
  add("risk", data.risk);
  add("villages", data.villages);
  add("roads", data.roads);
  add("infra", data.infra);
  add("history", data.history);
  add("reports", data.reports);
  if (map.getLayer("risk-fill")) return;
  map.addLayer({
    id: "risk-fill",
    type: "fill",
    source: "risk",
    paint: {
      "fill-color": ["match", ["get", "severity"], "low", COLORS.low, "moderate", COLORS.moderate, "high", COLORS.high, "severe", COLORS.severe, COLORS.low],
      "fill-opacity": 0.55,
    },
  });
  map.addLayer({
    id: "weather-rain",
    type: "circle",
    source: "risk",
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["get", "rain_72h"], 0, 0, 40, 6, 200, 18],
      "circle-color": "#4a7c9b",
      "circle-opacity": 0.25,
    },
  });
  map.addLayer({
    id: "roads",
    type: "line",
    source: "roads",
    paint: {
      "line-width": 3.2,
      "line-color": ["match", ["get", "derived_status"], "open", "#2f6b4f", "at_risk", "#c47b16", "blocked", "#8b1e1e", "#2f6b4f"],
    },
  });
  map.addLayer({
    id: "villages",
    type: "circle",
    source: "villages",
    paint: { "circle-radius": 5, "circle-color": "#1c2a22", "circle-stroke-width": 1.5, "circle-stroke-color": "#f4efe4" },
  });
  map.addLayer({
    id: "infra",
    type: "circle",
    source: "infra",
    paint: { "circle-radius": 6, "circle-color": "#3d5a80", "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
  });
  map.addLayer({
    id: "history",
    type: "circle",
    source: "history",
    paint: { "circle-radius": 4, "circle-color": "#6b3fa0" },
    layout: { visibility: "none" },
  });
  map.addLayer({
    id: "reports",
    type: "circle",
    source: "reports",
    paint: { "circle-radius": 7, "circle-color": "#0e7490", "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
  });
  map.on("click", "risk-fill", async (e) => {
    const f = e.features?.[0];
    const id = f?.properties?.id as string | undefined;
    if (!id) return;
    const info: ZoneInfo = await fetch(`${API}/zones/${id}`).then((r) => r.json());
    onZone(info);
    new Popup({ maxWidth: "280px" }).setLngLat(e.lngLat).setHTML(`<strong>${info.name}</strong><br/>${info.severity} · ${info.score}`).addTo(map);
  });
}
