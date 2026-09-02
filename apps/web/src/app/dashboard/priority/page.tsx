"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { DashNav, Guard } from "@/components/DashNav";

type Item = {
  zone_id: string;
  name: string;
  state: string;
  district: string;
  severity: string;
  score: number;
  inhabited: boolean;
  highway: boolean;
  population_nearby: number;
  priority: number;
  action: string;
};

export default function PriorityPage() {
  const [items, setItems] = useState<Item[]>([]);
  useEffect(() => {
    apiGet<{ items: Item[] }>("/dashboard/priority")
      .then((d) => setItems(d.items))
      .catch(() => undefined);
  }, []);
  return (
    <Guard>
      <div className="page">
        <h1>Emergency response priority</h1>
        <DashNav />
        <p className="note">Ranks high/severe cells by score, habitation, highway exposure, and nearby population (East Khasi Hills is the sample district story).</p>
        <table className="table">
          <thead>
            <tr>
              <th>Priority</th>
              <th>Place</th>
              <th>Severity</th>
              <th>People nearby</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.zone_id}>
                <td>{it.priority}</td>
                <td>
                  {it.district}, {it.state}
                  <div className="note">{it.name}</div>
                </td>
                <td>{it.severity}</td>
                <td>{it.population_nearby}</td>
                <td>{it.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Guard>
  );
}
