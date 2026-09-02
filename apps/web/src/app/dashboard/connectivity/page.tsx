"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { DashNav, Guard } from "@/components/DashNav";

type Row = { road: string; status: string; villages: { name: string; population: number; district: string }[] };

export default function ConnectivityPage() {
  const [data, setData] = useState<{ blocked: Row[]; at_risk: Row[]; open_count: number } | null>(null);
  useEffect(() => {
    apiGet("/dashboard/connectivity").then(setData).catch(() => setData(null));
  }, []);
  return (
    <Guard>
      <div className="page">
        <h1>Road connectivity</h1>
        <DashNav />
        <p className="note">Derived from reported blockages plus predicted highway-cell risk.</p>
        {data ? (
          <>
            <p>{data.open_count} corridors currently treated as open.</p>
            <h2>Blocked</h2>
            {data.blocked.map((r) => (
              <article key={r.road} className="card sev-severe">
                <h3>{r.road}</h3>
                <p>Villages: {r.villages.map((v) => `${v.name} (${v.population})`).join(", ") || "—"}</p>
              </article>
            ))}
            <h2>At risk</h2>
            {data.at_risk.map((r) => (
              <article key={r.road} className="card sev-high">
                <h3>{r.road}</h3>
                <p>Villages: {r.villages.map((v) => v.name).join(", ") || "—"}</p>
              </article>
            ))}
          </>
        ) : (
          <p>Loading…</p>
        )}
      </div>
    </Guard>
  );
}
