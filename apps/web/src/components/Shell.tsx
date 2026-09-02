"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearSession, readSession, SessionUser } from "@/lib/api";
import { Lang, readLang, STRINGS, writeLang } from "@/lib/i18n";
import { flushQueue } from "@/lib/offline";

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [lang, setLang] = useState<Lang>("en");
  const [offline, setOffline] = useState(false);
  const t = STRINGS[lang];

  useEffect(() => {
    setUser(readSession()?.user ?? null);
    setLang(readLang());
    const on = () => {
      setOffline(!navigator.onLine);
      if (navigator.onLine) flushQueue().catch(() => undefined);
    };
    on();
    window.addEventListener("online", on);
    window.addEventListener("offline", on);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", on);
    };
  }, [pathname]);

  function changeLang(next: Lang) {
    writeLang(next);
    setLang(next);
  }

  const links = [
    { href: "/map", label: t.map },
    { href: "/report", label: t.report },
    { href: "/alerts", label: t.alerts },
    { href: "/dashboard", label: t.dash },
  ];

  return (
    <div className="shell">
      <header className="topbar">
        <Link href="/" className="brand">
          <span className="mark" aria-hidden />
          <span>
            <strong>{t.product}</strong>
            <em>Northeast India</em>
          </span>
        </Link>
        <nav>
          {links.map((l) => (
            <Link key={l.href} href={l.href} className={pathname.startsWith(l.href) ? "active" : ""}>
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="tools">
          <label>
            {t.language}
            <select value={lang} onChange={(e) => changeLang(e.target.value as Lang)}>
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
              <option value="as">অসমীয়া</option>
              <option value="bn">বাংলা</option>
            </select>
          </label>
          {user ? (
            <>
              <span className="who">
                {user.display_name} · {user.role}
              </span>
              <button
                className="ghost"
                onClick={() => {
                  clearSession();
                  setUser(null);
                  router.push("/login");
                }}
              >
                {t.logout}
              </button>
            </>
          ) : (
            <Link href="/login" className="btn">
              {t.login}
            </Link>
          )}
        </div>
      </header>
      {offline ? <div className="banner">{t.offline}</div> : null}
      <main>{children}</main>
    </div>
  );
}
