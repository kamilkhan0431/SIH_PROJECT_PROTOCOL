"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { apiPost, readSession } from "@/lib/api";
import { readLang, STRINGS } from "@/lib/i18n";

export function DashNav() {
  const pathname = usePathname();
  const t = STRINGS[readLang()];
  const links = [
    { href: "/dashboard", label: t.risk },
    { href: "/dashboard/connectivity", label: t.connectivity },
    { href: "/dashboard/forecast", label: t.forecast },
    { href: "/dashboard/priority", label: t.priority },
    { href: "/dashboard/review", label: t.review },
  ];
  return (
    <div className="dash-nav">
      {links.map((l) => (
        <Link key={l.href} href={l.href} className={pathname === l.href ? "active" : ""}>
          {l.label}
        </Link>
      ))}
    </div>
  );
}

export function Guard({ children }: { children: React.ReactNode }) {
  const [ok, setOk] = useState(false);
  useEffect(() => {
    const s = readSession();
    setOk(Boolean(s && s.user.role !== "citizen"));
  }, []);
  if (!ok) {
    return (
      <div className="page">
        <p>Authority dashboards need a field, district, or SDMA login.</p>
        <Link href="/login">Sign in</Link>
      </div>
    );
  }
  return <>{children}</>;
}

export function RefreshButton() {
  const [msg, setMsg] = useState("");
  return (
    <p>
      <button
        className="btn"
        onClick={async () => {
          try {
            await apiPost("/ingest/refresh", {});
            setMsg("Weather + model + alerts refreshed");
            location.reload();
          } catch {
            setMsg("Refresh failed");
          }
        }}
      >
        Rescore now
      </button>{" "}
      {msg}
    </p>
  );
}
