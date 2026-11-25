import { useState } from "react";
import { Link } from "react-router-dom";
import TopicPicker from "../components/TopicPicker";
import { loadProfile, saveProfile } from "../lib/profile";

export default function TopicsPage() {
  const [profile, setProfile] = useState(loadProfile);
  const [saved, setSaved] = useState(false);
  const learned = Object.entries(profile.sections)
    .filter(([, v]) => v > 0.05)
    .sort((a, b) => b[1] - a[1]);

  const save = () => {
    saveProfile({ ...profile, onboarded: true });
    setSaved(true);
  };
  const forget = () => {
    const p = { ...profile, sections: {}, more: [], less: [] };
    setProfile(p);
    saveProfile(p);
  };

  return (
    <main className="topics-page">
      <header className="tp-head">
        <h1>I tuoi argomenti</h1>
        <p>Il briefing e l'ordine delle storie partono da qui. Restano solo su questo dispositivo.</p>
      </header>
      <TopicPicker
        value={profile.topics}
        onChange={(topics) => {
          setProfile({ ...profile, topics });
          setSaved(false);
        }}
      />
      <div className="tp-actions">
        <button className="onb-cta onb-cta--dark" onClick={save}>
          {saved ? "Argomenti salvati" : "Salva gli argomenti"}
        </button>
        {saved && <Link to="/">Torna alla tua edizione</Link>}
      </div>

      <section className="tp-learned">
        <h2>Cosa ha imparato Pulsar leggendo con te</h2>
        {learned.length ? (
          <>
            <ul>
              {learned.map(([sec, v]) => (
                <li key={sec}>
                  <span>{sec}</span>
                  <span className="tp-bar">
                    <span style={{ width: `${Math.round(v * 100)}%` }} />
                  </span>
                </li>
              ))}
            </ul>
            <button className="btn-line" onClick={forget}>
              Dimentica quello che ha imparato
            </button>
          </>
        ) : (
          <p>Ancora niente: apri qualche storia e qui vedrai le sezioni che leggi di più.</p>
        )}
      </section>
    </main>
  );
}
