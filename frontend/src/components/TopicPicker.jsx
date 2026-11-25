import { useEffect, useState } from "react";
import { api } from "../lib/api";

const FALLBACK = [
  { id: "esteri-italia", label: "Politica estera dell'Italia", blurb: "Diplomazia, missioni, alleanze" },
  { id: "politica", label: "Politica italiana", blurb: "Governo, Parlamento, leggi" },
  { id: "economia", label: "Economia e conti", blurb: "Conti pubblici, imprese, mercati" },
  { id: "lavoro", label: "Lavoro e diritti", blurb: "Contratti, salari, scioperi" },
];

/** Scelta degli argomenti: catalogo + argomenti scritti dal lettore. */
export default function TopicPicker({ value, onChange }) {
  const [catalog, setCatalog] = useState(FALLBACK);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    api.topics().then((r) => setCatalog(r.topics)).catch(() => {});
  }, []);

  const has = (t) => value.some((v) => (t.id ? v.id === t.id : v.label?.toLowerCase() === t.label.toLowerCase()));
  const toggle = (t) => onChange(has(t) ? value.filter((v) => v.id !== t.id) : [...value, { id: t.id, weight: 1 }]);
  const addCustom = (e) => {
    e.preventDefault();
    const label = draft.trim();
    if (!label || value.some((v) => v.label?.toLowerCase() === label.toLowerCase())) return;
    onChange([...value, { label, weight: 1 }]);
    setDraft("");
  };
  const custom = value.filter((v) => v.label);

  return (
    <div className="picker">
      <ul className="picker-grid">
        {catalog.map((t) => {
          const on = has(t);
          return (
            <li key={t.id}>
              <button type="button" className={`picker-tile${on ? " is-on" : ""}`} aria-pressed={on} onClick={() => toggle(t)}>
                <span className="picker-label">{t.label}</span>
                <span className="picker-blurb">{t.blurb}</span>
                <span className="picker-check" aria-hidden />
              </button>
            </li>
          );
        })}
      </ul>

      <form className="picker-custom" onSubmit={addCustom}>
        <label htmlFor="custom-topic">Qualcos'altro? Scrivilo con parole tue.</label>
        <div className="picker-custom-row">
          <input
            id="custom-topic"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Es. Formula 1, intelligenza artificiale, Medio Oriente"
            maxLength={60}
          />
          <button type="submit" disabled={!draft.trim()}>
            Aggiungi
          </button>
        </div>
        {custom.length > 0 && (
          <ul className="picker-chips">
            {custom.map((c) => (
              <li key={c.label}>
                {c.label}
                <button type="button" aria-label={`Togli ${c.label}`} onClick={() => onChange(value.filter((v) => v !== c))}>
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </form>
    </div>
  );
}
