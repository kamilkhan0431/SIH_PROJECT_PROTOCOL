"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { DashNav, Guard } from "@/components/DashNav";

type Zone = {
  zone_id: string;
  name: string;
  state: string;
  rain_forecast_48h: number;
  rain_72h: number;
  severity: string;
  forecast_bump: boolean;
};

export default function ForecastPage() {
  const [rows, setRows] = useState<Zone[]>([]);
  const [note, setNote] = useState("");
  useEffect(() => {
    apiGet<{ zones: Zone[]; weather_note: string }>("/dashboard/forecast")
      .then((d) => {
        setRows(d.zones);
        setNote(d.weather_note);
      })
      .catch(() => undefined);
  }, []);
  return (
    <Guard>
      <div className="page">
        <h1>Weather-linked forecast</h1>
        <DashNav />
        <p className="note">{note}. Cells with forecast rain on steep slopes are flagged for a severity bump.</p>
        <table className="table">
          <thead>
            <tr>
              <th>Zone</th>
              <th>State</th>
              <th>72h rain</th>
              <th>48h forecast</th>
              <th>Now</th>
              <th>Bump</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((z) => (
              <tr key={z.zone_id}>
                <td>{z.name}</td>
                <td>{z.state}</td>
                <td>{z.rain_72h}</td>
                <td>{z.rain_forecast_48h}</td>
                <td>{z.severity}</td>
                <td>{z.forecast_bump ? "yes" : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Guard>
  );
}
