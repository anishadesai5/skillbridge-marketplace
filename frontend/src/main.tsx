import React, { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Package = { id: number; category: string; title: string; description: string; price: string; duration_days: number };
type Provider = { id: number; first_name: string; last_name: string; bio?: string; rating: string; packages: Package[] };
type User = { id: number; email: string; role: "customer" | "provider" | "administrator" };

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  const [token, setToken] = useState(localStorage.getItem("skillbridge_token") || "");
  const [user, setUser] = useState<User | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [message, setMessage] = useState("Loading verified providers…");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    fetch(`${apiBase}/providers`)
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        return response.json();
      })
      .then((data) => { setProviders(data); setMessage(data.length ? "" : "No published providers found."); })
      .catch(() => setMessage("Start the API and seed the database to view providers."));
  }, []);

  useEffect(() => {
    if (!token) { setUser(null); return; }
    fetch(`${apiBase}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then(setUser)
      .catch(() => { localStorage.removeItem("skillbridge_token"); setToken(""); });
  }, [token]);

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setAuthError("");
    const data = new FormData(event.currentTarget);
    const payload: Record<string, string> = { email: String(data.get("email")), password: String(data.get("password")) };
    if (authMode === "register") Object.assign(payload, { role: String(data.get("role")), first_name: String(data.get("first_name")), last_name: String(data.get("last_name")) });
    const response = await fetch(`${apiBase}/auth/${authMode}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (!response.ok) { const body = await response.json(); setAuthError(body.detail || "Request failed"); return; }
    const body = await response.json(); localStorage.setItem("skillbridge_token", body.access_token); setToken(body.access_token); setUser(body.user);
  }

  function logout() { localStorage.removeItem("skillbridge_token"); setToken(""); setUser(null); }

  return (
    <main>
      <header><span className="eyebrow">SKILLBRIDGE</span><h1>Find trusted independent expertise.</h1><p>Explore verified providers, compare fixed-price packages, and manage milestone-based work in one place.</p>{user && <div className="session"><span>{user.email} · {user.role}</span><button type="button" onClick={logout}>Sign out</button></div>}</header>
      {!user && <section className="auth"><div className="auth-card"><h2>{authMode === "login" ? "Sign in" : "Create account"}</h2><form onSubmit={submitAuth}>{authMode === "register" && <><div className="row"><input name="first_name" placeholder="First name" required/><input name="last_name" placeholder="Last name" required/></div><select name="role" defaultValue="customer"><option value="customer">Customer</option><option value="provider">Provider</option></select></>}<input name="email" type="email" placeholder="Email" required/><input name="password" type="password" placeholder="Password" minLength={8} required/><button type="submit">{authMode === "login" ? "Sign in" : "Register"}</button></form>{authError && <p className="error">{authError}</p>}<button className="link" type="button" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "Create an account" : "Already have an account"}</button></div></section>}
      {user && <section className="role-banner"><strong>{user.role === "administrator" ? "Administrator workspace" : user.role === "provider" ? "Provider workspace" : "Customer marketplace"}</strong><span>{user.role === "administrator" ? "Review pending provider profiles through the API dashboard." : user.role === "provider" ? "Update your profile and submit credentials through the API dashboard." : "Browse approved service packages below."}</span></section>}
      <section aria-label="Provider marketplace">
        <div className="section-title"><h2>Featured providers</h2><span>Payments are simulated for this academic prototype.</span></div>
        {message && <p className="notice">{message}</p>}
        <div className="grid">
          {providers.map((provider) => provider.packages.map((pkg) => (
            <article key={pkg.id}>
              <div className="avatar">{provider.first_name[0]}{provider.last_name[0]}</div>
              <div><span className="tag">{pkg.category}</span><h3>{pkg.title}</h3><p>{pkg.description}</p><p className="provider">{provider.first_name} {provider.last_name} · ★ {provider.rating}</p></div>
              <footer><strong>${Number(pkg.price).toFixed(2)}</strong><span>{pkg.duration_days} days</span><button type="button" disabled={user?.role !== "customer"}>View package</button></footer>
            </article>
          )))}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
