"use client";

import { useEffect, useState } from "react";
import { API, apiGet, apiPost, authHeader } from "@/lib/api";
import { DashNav, Guard } from "@/components/DashNav";

type Report = {
  id: number;
  type: string;
  description: string;
  lat: number;
  lon: number;
  status: string;
  media_path: string;
  reporter_role: string;
  created_at: string;
};

export default function ReviewPage() {
  const [rows, setRows] = useState<Report[]>([]);
  useEffect(() => {
    apiGet<Report[]>("/reports").then(setRows).catch(() => setRows([]));
  }, []);

  async function decide(id: number, status: "approved" | "rejected") {
    await apiPost(`/reports/${id}/review`, { status });
    const data = await fetch(`${API}/reports`, { headers: { ...authHeader() } }).then((r) => r.json());
    setRows(data);
  }

  return (
    <Guard>
      <div className="page">
        <h1>Field report review</h1>
        <DashNav />
        <div className="cards">
          {rows.map((r) => (
            <article key={r.id} className="card">
              <h3>
                {r.type} · {r.status}
              </h3>
              <p>{r.description}</p>
              <p className="note">
                {r.lat}, {r.lon} · {r.reporter_role} · {r.created_at}
              </p>
              {r.media_path ? (
                r.media_path.match(/mp4|webm|mov/i) ? (
                  <video src={`${API}${r.media_path}`} controls width={280} />
                ) : (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={`${API}${r.media_path}`} alt="" width={280} />
                )
              ) : null}
              {r.status === "pending" ? (
                <p>
                  <button className="btn" onClick={() => decide(r.id, "approved")}>
                    Approve
                  </button>{" "}
                  <button className="ghost" onClick={() => decide(r.id, "rejected")}>
                    Reject
                  </button>
                </p>
              ) : null}
            </article>
          ))}
        </div>
      </div>
    </Guard>
  );
}
