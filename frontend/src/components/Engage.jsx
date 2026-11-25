import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Fingerprint } from "./Instruments";

const band = (o) => (o <= -0.25 ? "left" : o >= 0.25 ? "right" : "center");
const BAND = { left: "Sinistra", center: "Centro", right: "Destra" };

/** Le storie del giorno in una riga: una frase confermata ciascuna. */
export function Briefing({ stories }) {
  return (
    <section className="brief" aria-labelledby="brief-h">
      <h2 id="brief-h">Oggi in trenta secondi</h2>
      <ol className="brief-list">
        {stories.map((s) => {
          const fact = s.key_facts.find((f) => f.status === "confermato") || s.key_facts[0];
          return (
            <li key={s.id}>
              <Link to={`/storia/${s.id}`}>
                <span className="brief-sec">{s.section || "Notizie"}</span>
                <span className="brief-title">{s.title}</span>
                {fact && <span className="brief-fact">{fact.text}</span>}
                <Fingerprint counts={s.metrics?.status_counts} />
              </Link>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

/** Gioco: indovina da che parte dello spettro viene il titolo. */
export function GuessGame({ stories }) {
  const pool = useMemo(
    () => stories.flatMap((s) => (s.headlines || []).map((h) => ({ ...h, story: s }))).filter((h) => h.title),
    [stories]
  );
  const [i, setI] = useState(() => Math.floor(Math.random() * Math.max(1, pool.length)));
  const [guess, setGuess] = useState(null);
  const [score, setScore] = useState({ ok: 0, tot: 0 });
  if (!pool.length) return null;

  const h = pool[i % pool.length];
  const right = band(h.orientation);
  const answer = (g) => {
    if (guess) return;
    setGuess(g);
    setScore((s) => ({ ok: s.ok + (g === right ? 1 : 0), tot: s.tot + 1 }));
  };
  const next = () => {
    setGuess(null);
    setI((v) => (v + 1 + Math.floor(Math.random() * (pool.length - 1 || 1))) % pool.length);
  };

  return (
    <section className="game" aria-labelledby="game-h">
      <div className="game-top">
        <h2 id="game-h">Di chi è questo titolo?</h2>
        {score.tot > 0 && (
          <span className="game-score">
            {score.ok} su {score.tot}
          </span>
        )}
      </div>
      <p className="game-title">{h.title}</p>
      <div className="game-btns" role="group" aria-label="Da che parte viene?">
        {["left", "center", "right"].map((b) => (
          <button
            key={b}
            type="button"
            onClick={() => answer(b)}
            disabled={!!guess}
            className={guess ? (b === right ? "is-right" : b === guess ? "is-wrong" : "") : ""}
          >
            {BAND[b]}
          </button>
        ))}
      </div>
      {guess && (
        <div className="game-reveal" aria-live="polite">
          <p>
            <strong>{guess === right ? "Esatto." : "No."}</strong> È {h.source_name}.
          </p>
          <span className="pos pos--wide">
            <span className="pos-dot" style={{ left: `${((h.orientation + 1) / 2) * 100}%` }} />
          </span>
          <p className="game-neutral">
            Detto senza inquadramento: <Link to={`/storia/${h.story.id}`}>{h.story.title}</Link>
          </p>
          <button type="button" className="game-next" onClick={next}>
            Un altro titolo
          </button>
        </div>
      )}
    </section>
  );
}

/** La parola carica del giorno, con la sua versione neutra. */
export function WordOfDay({ stories }) {
  const pick = stories.flatMap((s) => (s.loaded_terms || []).map((t) => ({ ...t, story: s })))[0];
  if (!pick) return null;
  const outlet = pick.story.headlines?.find((h) => h.source_id === pick.source_id)?.source_name;
  return (
    <section className="word" aria-labelledby="word-h">
      <h2 id="word-h">La parola del giorno</h2>
      <p className="word-big">
        <del>{pick.term}</del>
      </p>
      <p className="word-neutral">
        Più semplicemente: <strong>{pick.neutral}</strong>
      </p>
      <p className="word-why">
        {pick.why} {outlet && <>Scritto da {outlet}, </>}
        <Link to={`/storia/${pick.story.id}#parole`}>nella storia</Link>.
      </p>
    </section>
  );
}
