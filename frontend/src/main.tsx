import React, { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type User = { id: number; email: string; role: "customer" | "provider" | "administrator" };
type Package = { id: number; provider_id: number; category: string; title: string; description: string; price: string; duration_days: number };
type Provider = { id: number; first_name: string; last_name: string; bio?: string; portfolio_url?: string; rating: string; packages: Package[] };
type Listing = { package_id: number; provider_id: number; provider_name: string; provider_rating: string; category: string; title: string; description: string; price: string; duration_days: number };
type Booking = { id: number; provider_id: number; package_id: number; status: string; booking_date: string; total: string; customer_notes?: string };

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  const [token, setToken] = useState(localStorage.getItem("skillbridge_token") || "");
  const [user, setUser] = useState<User | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [selected, setSelected] = useState<Provider | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [message, setMessage] = useState("Loading available services…");
  const [bookingMessage, setBookingMessage] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authError, setAuthError] = useState("");

  async function loadListings(params = "") {
    setMessage("Searching available services…");
    try {
      const response = await fetch(`${apiBase}/services${params}`);
      if (!response.ok) throw new Error((await response.json()).detail || "Search failed");
      const data = await response.json();
      setListings(data); setMessage(data.length ? "" : "No services match those filters.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Start the API to view services."); }
  }

  async function loadBookings(activeToken = token) {
    if (!activeToken) return;
    const response = await fetch(`${apiBase}/customers/me/bookings`, { headers: { Authorization: `Bearer ${activeToken}` } });
    if (response.ok) setBookings(await response.json());
  }

  useEffect(() => { loadListings(); }, []);
  useEffect(() => {
    if (!token) { setUser(null); setBookings([]); return; }
    fetch(`${apiBase}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then((currentUser) => { setUser(currentUser); if (currentUser.role === "customer") loadBookings(token); })
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

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget); const params = new URLSearchParams();
    for (const key of ["q", "category", "min_price", "max_price", "min_rating"]) { const value = String(data.get(key) || "").trim(); if (value) params.set(key, value); }
    loadListings(params.size ? `?${params}` : "");
  }

  async function viewProvider(providerId: number) {
    const response = await fetch(`${apiBase}/providers/${providerId}`);
    if (response.ok) { setSelected(await response.json()); setBookingMessage(""); document.getElementById("provider-detail")?.scrollIntoView({ behavior: "smooth" }); }
  }

  async function submitBooking(event: FormEvent<HTMLFormElement>, packageId: number) {
    event.preventDefault(); setBookingMessage("");
    const data = new FormData(event.currentTarget);
    const response = await fetch(`${apiBase}/bookings`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ package_id: packageId, booking_date: data.get("booking_date"), customer_notes: data.get("customer_notes") || null }) });
    const body = await response.json();
    if (!response.ok) { setBookingMessage(body.detail || "Booking request failed."); return; }
    setBookingMessage(`Booking request #${body.id} was saved with Pending status.`); await loadBookings();
  }

  function logout() { localStorage.removeItem("skillbridge_token"); setToken(""); setUser(null); setSelected(null); }

  return (
    <main>
      <header><span className="eyebrow">SKILLBRIDGE</span><h1>Find trusted independent expertise.</h1><p>Search approved providers, compare fixed-price services, and submit a booking request in one place.</p>{user && <div className="session"><span>{user.email} · {user.role}</span><button type="button" onClick={logout}>Sign out</button></div>}</header>
      {!user && <section className="auth"><div className="auth-card"><h2>{authMode === "login" ? "Sign in" : "Create account"}</h2><form onSubmit={submitAuth}>{authMode === "register" && <><div className="row"><input name="first_name" placeholder="First name" required/><input name="last_name" placeholder="Last name" required/></div><select name="role" defaultValue="customer"><option value="customer">Customer</option><option value="provider">Provider</option></select></>}<input name="email" type="email" placeholder="Email" required/><input name="password" type="password" placeholder="Password" minLength={8} required/><button type="submit">{authMode === "login" ? "Sign in" : "Register"}</button></form>{authError && <p className="error">{authError}</p>}<button className="link" type="button" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "Create an account" : "Already have an account"}</button></div></section>}
      {user && <section className="role-banner"><strong>{user.role === "customer" ? "Customer marketplace" : user.role === "provider" ? "Provider workspace" : "Administrator workspace"}</strong><span>{user.role === "customer" ? "Search approved services and request a booking below." : "Use the API dashboard for role-specific management functions."}</span></section>}
      <section aria-label="Service marketplace">
        <div className="section-title"><h2>Search services</h2><span>Only approved providers and active packages appear.</span></div>
        <form className="filters" onSubmit={search}><input name="q" placeholder="Keyword or provider"/><select name="category" defaultValue=""><option value="">All categories</option><option>Design</option><option>Career</option></select><input name="min_price" type="number" min="0" step="1" placeholder="Min price"/><input name="max_price" type="number" min="0" step="1" placeholder="Max price"/><select name="min_rating" defaultValue=""><option value="">Any rating</option><option value="4">4+ stars</option><option value="4.5">4.5+ stars</option></select><button type="submit">Search</button></form>
        {message && <p className="notice">{message}</p>}
        <div className="grid">{listings.map((item) => <article key={item.package_id}><div className="avatar">{item.provider_name.split(" ").map((name) => name[0]).join("")}</div><div><span className="tag">{item.category}</span><h3>{item.title}</h3><p>{item.description}</p><p className="provider">{item.provider_name} · ★ {item.provider_rating}</p></div><footer><strong>${Number(item.price).toFixed(2)}</strong><span>{item.duration_days} days</span><button type="button" onClick={() => viewProvider(item.provider_id)}>View provider</button></footer></article>)}</div>
      </section>
      {selected && <section id="provider-detail" className="detail"><div className="section-title"><div><span className="tag">APPROVED PROVIDER</span><h2>{selected.first_name} {selected.last_name}</h2></div><button className="secondary" type="button" onClick={() => setSelected(null)}>Close</button></div><p>{selected.bio}</p><p>★ {selected.rating} rating</p><div className="packages">{selected.packages.map((pkg) => <div className="package" key={pkg.id}><div><h3>{pkg.title}</h3><p>{pkg.description}</p><strong>${Number(pkg.price).toFixed(2)} · {pkg.duration_days} days</strong></div>{user?.role === "customer" ? <form className="booking-form" onSubmit={(event) => submitBooking(event, pkg.id)}><label>Requested date<input name="booking_date" type="date" min={new Date().toISOString().slice(0,10)} required/></label><label>Notes<textarea name="customer_notes" maxLength={2000} placeholder="Describe what you need (optional)"/></label><button type="submit">Request booking</button></form> : <p className="notice">Sign in as a customer to request this service.</p>}</div>)}</div>{bookingMessage && <p className={bookingMessage.includes("saved") ? "success" : "error"}>{bookingMessage}</p>}</section>}
      {user?.role === "customer" && <section><div className="section-title"><h2>My bookings</h2><span>Saved booking requests</span></div>{bookings.length === 0 ? <p className="notice">No booking requests yet.</p> : <div className="booking-list">{bookings.map((booking) => <div className="booking-row" key={booking.id}><strong>Request #{booking.id}</strong><span>{booking.booking_date}</span><span>${Number(booking.total).toFixed(2)}</span><span className="status">{booking.status}</span></div>)}</div>}</section>}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
