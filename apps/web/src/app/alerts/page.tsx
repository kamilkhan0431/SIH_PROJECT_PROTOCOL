"use client";

import { useEffect, useState } from "react";
import { API, apiGet } from "@/lib/api";
import { readLang } from "@/lib/i18n";

type Alert = {
  id: number;
  rule: string;
  severity: string;
  title: string;
  body: string;
  sms_status: string;
  created_at: string;
};

export default function AlertsPage() {
  const [rows, setRows] = useState<Alert[]>([]);
  const lang = readLang();

  useEffect(() => {
    apiGet<Alert[]>(`/alerts?lang=${lang}`).then(setRows).catch(() => setRows([]));
    if (typeof Notification !== "undefined" && Notification.permission === "default") {
      Notification.requestPermission().catch(() => undefined);
    }
  }, [lang]);

  useEffect(() => {
    if (!rows.length || typeof Notification === "undefined" || Notification.permission !== "granted") return;
    const first = rows[0];
    if (sessionStorage.getItem("ss_last_alert") === String(first.id)) return;
    sessionStorage.setItem("ss_last_alert", String(first.id));
    new Notification(first.title, { body: first.body });
  }, [rows]);

  return (
    <div className="page">
      <h1>Alerts</h1>
      <p className="note">
        Rules: severe inhabited cells, high-risk highways, clusters of approved field reports. SMS uses a MSG91/Twilio-shaped stub (
        logged unless a key is set). Copy is English, Hindi, Assamese, and Bengali.
      </p>
      <div className="cards">
        {rows.map((a) => (
          <article key={a.id} className={`card sev-${a.severity}`}>
            <h3>{a.title}</h3>
            <p>{a.body}</p>
            <p className="note">
              {a.rule} · SMS {a.sms_status} · {a.created_at}
            </p>
          </article>
        ))}
        {!rows.length ? <p>No active alerts. Refresh ingest from the authority desk after weather updates.</p> : null}
      </div>
      <p className="note">API base {API}</p>
    </div>
  );
}
