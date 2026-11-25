import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

export default function Masthead() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  const submit = (e) => {
    e.preventDefault();
    if (q.trim()) {
      nav(`/cerca?q=${encodeURIComponent(q.trim())}`);
      setOpen(false);
    }
  };

  return (
    <header className="mast2">
      <Link to="/" className="mast2-brand" aria-label="Pulsar, la tua edizione">
        <svg className="mast2-mark" viewBox="0 0 32 32" aria-hidden>
          <circle cx="16" cy="19" r="3.6" />
          <path d="M8 19a8 8 0 0 1 16 0M3 19a13 13 0 0 1 26 0" />
        </svg>
        Pulsar
      </Link>
      <nav className="mast2-nav">
        <NavLink to="/" end>
          Edizione
        </NavLink>
        <NavLink to="/briefing">Briefing</NavLink>
        <NavLink to="/argomenti">Argomenti</NavLink>
        <NavLink to="/fonti">Metodo</NavLink>
      </nav>
      <button className="mast2-search-btn" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-controls="mast2-search">
        Cerca
      </button>
      {open && (
        <form id="mast2-search" className="mast2-search" onSubmit={submit} role="search">
          <label htmlFor="q" className="sr-only">
            Cerca un argomento
          </label>
          <input id="q" autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca un argomento nelle testate" />
          <button type="submit">Cerca</button>
        </form>
      )}
    </header>
  );
}
