import { openDB } from "idb";
import { API, authHeader } from "./api";

export type QueuedReport = {
  client_id: string;
  type: string;
  description: string;
  lat: number;
  lon: number;
  media?: { name: string; type: string; blob: Blob };
  created_at: string;
};

function db() {
  return openDB("slopesense", 1, {
    upgrade(d) {
      if (!d.objectStoreNames.contains("queue")) d.createObjectStore("queue", { keyPath: "client_id" });
      if (!d.objectStoreNames.contains("mapcache")) d.createObjectStore("mapcache");
    },
  });
}

export async function enqueueReport(item: QueuedReport) {
  const d = await db();
  await d.put("queue", item);
}

export async function listQueue(): Promise<QueuedReport[]> {
  const d = await db();
  return d.getAll("queue");
}

export async function cacheJson(key: string, value: unknown) {
  const d = await db();
  await d.put("mapcache", value, key);
}

export async function readCache<T>(key: string): Promise<T | undefined> {
  const d = await db();
  return d.get("mapcache", key);
}

export async function flushQueue(): Promise<number> {
  if (typeof navigator !== "undefined" && !navigator.onLine) return 0;
  const d = await db();
  const items: QueuedReport[] = await d.getAll("queue");
  let n = 0;
  for (const item of items) {
    const fd = new FormData();
    fd.append("type", item.type);
    fd.append("description", item.description);
    fd.append("lat", String(item.lat));
    fd.append("lon", String(item.lon));
    fd.append("client_id", item.client_id);
    if (item.media) {
      fd.append("media", item.media.blob, item.media.name);
    }
    const res = await fetch(`${API}/reports`, { method: "POST", headers: { ...authHeader() }, body: fd });
    if (res.ok) {
      await d.delete("queue", item.client_id);
      n += 1;
    }
  }
  return n;
}
