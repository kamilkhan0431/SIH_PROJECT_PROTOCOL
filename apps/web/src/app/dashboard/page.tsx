"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { DashNav, Guard, RefreshButton } from "@/components/DashNav";

type Summary = {
  risk_counts: Record<string, number>;
  by_state: Record<string, Record<string, number>>;
  roads: Record<string, number>;
  active_alerts: number;
  pending_reports: number;
  approved_reports: number;
  updated_at: string;
};

export default function RiskDash() {
  const [data, setData] = useState<Summary | null>(null);
  useEffect(() => {
    apiGet<Summary>("/dashboard/summary").then(setData).catch(() => setData(null));
  }, []);
  return (
    <Guard>
      <div className="page">
        <h1>Risk severity</h1>
        <DashNav />
        <RefreshButton />
        {data ? (
          <>
            <section className="grid4">
              {Object.entries(data.risk_counts).map(([k, v]) => (
                <div key={k} className={`stat sev-${k}`}>
                  <b>{v}</b>
                  {k} cells
                </div>
              ))}
            </section>
            <p className="note">
              Alerts {data.active_alerts} · pending reports {data.pending_reports} · approved {data.approved_reports} · {data.updated_at}
            </p>
            <table className="table">
              <thead>
                <tr>
                  <th>State</th>
                  <th>Low</th>
                  <th>Mod</th>
                  <th>High</th>
                  <th>Severe</th>
                  <th>Max score</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.by_state).map(([st, b]) => (
                  <tr key={st}>
                    <td>{st}</td>
                    <td>{b.low}</td>
                    <td>{b.moderate}</td>
                    <td>{b.high}</td>
                    <td>{b.severe}</td>
                    <td>{b.max_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <p>Loading…</p>
        )}
      </div>
    </Guard>
  );
}
