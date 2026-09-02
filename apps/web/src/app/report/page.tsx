"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API, authHeader, readSession } from "@/lib/api";
import { enqueueReport, flushQueue, listQueue } from "@/lib/offline";
import { readLang, STRINGS } from "@/lib/i18n";

const TYPES = ["crack", "slope_movement", "blocked_road", "flash_flood", "other"];

export default function ReportPage() {
  const router = useRouter();
  const t = STRINGS[readLang()];
  const [type, setType] = useState("crack");
  const [description, setDescription] = useState("");
  const [lat, setLat] = useState(25.47);
  const [lon, setLon] = useState(91.88);
  const [file, setFile] = useState<File | null>(null);
  const [msg, setMsg] = useState("");
  const [queued, setQueued] = useState(0);

  useEffect(() => {
    if (!readSession()) router.push("/login");
    listQueue().then((q) => setQueued(q.length));
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (p) => {
          setLat(Number(p.coords.latitude.toFixed(5)));
          setLon(Number(p.coords.longitude.toFixed(5)));
        },
        () => undefined,
        { timeout: 4000 }
      );
    }
  }, [router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const client_id = crypto.randomUUID();
    const payload = {
      client_id,
      type,
      description,
      lat,
      lon,
      created_at: new Date().toISOString(),
      media: file ? { name: file.name, type: file.type, blob: file } : undefined,
    };
    if (!navigator.onLine) {
      await enqueueReport(payload);
      setQueued((n) => n + 1);
      setMsg(t.queued);
      return;
    }
    const fd = new FormData();
    fd.append("type", type);
    fd.append("description", description);
    fd.append("lat", String(lat));
    fd.append("lon", String(lon));
    fd.append("client_id", client_id);
    if (file) fd.append("media", file);
    const res = await fetch(`${API}/reports`, { method: "POST", headers: { ...authHeader() }, body: fd });
    if (!res.ok) {
      await enqueueReport(payload);
      setMsg("Saved locally after a send error");
      return;
    }
    setMsg("Report received");
    flushQueue().then((n) => setQueued((q) => Math.max(0, q - n)));
  }

  return (
    <div className="page">
      <h1>{t.report}</h1>
      <p className="note">Geo-tagged photo or video. If GPS is denied, drop a pin by editing coordinates. Officials auto-approve; citizens wait for review.</p>
      {queued ? <p className="banner">{queued} {t.queued}</p> : null}
      <form className="form" onSubmit={submit}>
        <label>
          Type
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {TYPES.map((x) => (
              <option key={x} value={x}>
                {x}
              </option>
            ))}
          </select>
        </label>
        <label>
          Latitude
          <input type="number" step="0.00001" value={lat} onChange={(e) => setLat(Number(e.target.value))} />
        </label>
        <label>
          Longitude
          <input type="number" step="0.00001" value={lon} onChange={(e) => setLon(Number(e.target.value))} />
        </label>
        <label>
          Notes
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
        </label>
        <label>
          Photo / video
          <input type="file" accept="image/*,video/*" capture="environment" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </label>
        <button className="btn" type="submit">
          {t.submit}
        </button>
        {msg ? <p>{msg}</p> : null}
      </form>
    </div>
  );
}
