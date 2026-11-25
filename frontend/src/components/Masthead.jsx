import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

export default function Masthead() {
  const [q, setQ] = useState("");
  const nav = useNavigate();
  const submit = (e) => {
    e.preventDefault();
    if (q.trim()) nav(`/cerca?q=${encodeURIComponent(q.trim())}`);
  };

  return (
    <header className="mast">
      <Link to="/" className="mast-brand" aria-label="Pulsar, prima pagina">
        <svg className="mast-mark" viewBox="0 0 32 32" aria-hidden>
          <circle cx="16" cy="16" r="4" />
          <path d="M6 16a10 10 0 0 1 20 0M2 16a14 14 0 0 1 28 0" />
        </svg>
        Pulsar
      </Link>
      <nav className="mast-nav">
        <NavLink to="/" end>
          Prima pagina
        </NavLink>
        <NavLink to="/fonti">Fonti e metodo</NavLink>
      </nav>
      <form className="mast-search" onSubmit={submit} role="search">
        <label htmlFor="q" className="sr-only">
          Cerca un argomento
        </label>
        <input id="q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca un argomento" />
        <button type="submit">Cerca</button>
      </form>
    </header>
  );
}
