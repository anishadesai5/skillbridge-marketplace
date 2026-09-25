import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Package = { id: number; category: string; title: string; description: string; price: string; duration_days: number };
type Provider = { id: number; first_name: string; last_name: string; bio?: string; rating: string; packages: Package[] };

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [message, setMessage] = useState("Loading verified providers…");

  useEffect(() => {
    fetch(`${apiBase}/providers`)
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        return response.json();
      })
      .then((data) => { setProviders(data); setMessage(data.length ? "" : "No published providers found."); })
      .catch(() => setMessage("Start the API and seed the database to view providers."));
  }, []);

  return (
    <main>
      <header><span className="eyebrow">SKILLBRIDGE</span><h1>Find trusted independent expertise.</h1><p>Explore verified providers, compare fixed-price packages, and manage milestone-based work in one place.</p></header>
      <section aria-label="Provider marketplace">
        <div className="section-title"><h2>Featured providers</h2><span>Payments are simulated for this academic prototype.</span></div>
        {message && <p className="notice">{message}</p>}
        <div className="grid">
          {providers.map((provider) => provider.packages.map((pkg) => (
            <article key={pkg.id}>
              <div className="avatar">{provider.first_name[0]}{provider.last_name[0]}</div>
              <div><span className="tag">{pkg.category}</span><h3>{pkg.title}</h3><p>{pkg.description}</p><p className="provider">{provider.first_name} {provider.last_name} · ★ {provider.rating}</p></div>
              <footer><strong>${Number(pkg.price).toFixed(2)}</strong><span>{pkg.duration_days} days</span><button type="button">View package</button></footer>
            </article>
          )))}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
