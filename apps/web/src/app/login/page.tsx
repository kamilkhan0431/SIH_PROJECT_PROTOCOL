"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { API, writeSession } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("district");
  const [password, setPassword] = useState("demo123");
  const [err, setErr] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      setErr("Login failed. Use a demo user.");
      return;
    }
    const data = await res.json();
    writeSession(data.token, data.user);
    router.push(data.user.role === "citizen" ? "/report" : "/dashboard");
  }

  return (
    <div className="page">
      <h1>Sign in</h1>
      <p className="note">Demo accounts share the password demo123.</p>
      <form className="form" onSubmit={onSubmit}>
        <label>
          Username
          <select value={username} onChange={(e) => setUsername(e.target.value)}>
            <option value="citizen">citizen</option>
            <option value="field">field</option>
            <option value="district">district</option>
            <option value="sdma">sdma</option>
          </select>
        </label>
        <label>
          Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
        </label>
        {err ? <p className="warn">{err}</p> : null}
        <button className="btn" type="submit">
          Enter desk
        </button>
      </form>
    </div>
  );
}
