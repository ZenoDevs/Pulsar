import { useState } from "react";
import { api } from "../lib/api";
import { STATUS_ORDER } from "../lib/format";
import { isFollowing, loadProfile, toggleFollow } from "../lib/profile";
import { shareBlob, storyCard } from "../lib/sharecard";
import { Fingerprint, SourceChips, StatusTag } from "./Instruments";

const DEPTHS = [
  ["10s", "10 secondi"],
  ["1min", "1 minuto"],
  ["tutto", "Tutto il dossier"],
];

export function DepthSwitch({ value, onChange }) {
  return (
    <div className="depth" role="tablist" aria-label="Quanto vuoi approfondire">
      {DEPTHS.map(([k, label]) => (
        <button key={k} role="tab" aria-selected={value === k} onClick={() => onChange(k)}>
          {label}
        </button>
      ))}
    </div>
  );
}

/** 10 secondi: una frase certa, quanto è solida, dove si litiga. */
export function TenSeconds({ story }) {
  const d = story.dossier;
  const fact = d?.facts.find((f) => f.status === "confermato") || d?.facts[0];
  return (
    <section className="quick quick--10">
      {fact ? (
        <p className="quick-fact">
          <StatusTag status={fact.status} />
          <span>{fact.text}</span>
        </p>
      ) : (
        <p className="quick-fact">{story.articles[0]?.snippet}</p>
      )}
      {d?.divergences[0] && (
        <p className="quick-div">
          <StatusTag status="contestato" /> <span>Non concordano su: {d.divergences[0].topic.toLowerCase()}.</span>
        </p>
      )}
      <Fingerprint counts={story.metrics?.status_counts} size="lg" showLegend />
    </section>
  );
}

/** 1 minuto: il sommario, i fatti che contano, lo spacco principale, le cornici. */
export function OneMinute({ story, names }) {
  const d = story.dossier;
  if (!d) return <TenSeconds story={story} />;
  const facts = [...d.facts].sort((a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)).slice(0, 5);
  const div = d.divergences[0];
  return (
    <section className="quick quick--1">
      <ul className="quick-facts">
        {facts.map((f) => (
          <li key={f.id}>
            <StatusTag status={f.status} />
            <span>{f.text}</span>
          </li>
        ))}
      </ul>
      {div && (
        <div className="quick-block">
          <h3>Dove non concordano: {div.topic.toLowerCase()}</h3>
          <div className="div-versions">
            {div.versions.map((v, i) => (
              <div key={i} className="div-v">
                <p>{v.account}</p>
                <SourceChips ids={v.source_ids} names={names} />
              </div>
            ))}
          </div>
        </div>
      )}
      {d.framings.length > 1 && (
        <div className="quick-block">
          <h3>Come la raccontano</h3>
          <ul className="quick-frames">
            {d.framings.map((f, i) => (
              <li key={i}>
                <strong>{f.label}</strong> {f.frame} <SourceChips ids={f.source_ids} names={names} muted />
              </li>
            ))}
          </ul>
        </div>
      )}
      {d.open_questions[0] && (
        <p className="quick-open">
          <strong>Non si sa ancora:</strong> {d.open_questions[0]}
        </p>
      )}
    </section>
  );
}

export function FollowButton({ storyId }) {
  const [on, setOn] = useState(() => isFollowing(loadProfile(), storyId));
  return (
    <button
      className={`btn-follow${on ? " is-on" : ""}`}
      aria-pressed={on}
      onClick={() => setOn(isFollowing(toggleFollow(storyId), storyId))}
    >
      {on ? "La segui" : "Segui questa storia"}
    </button>
  );
}

export function ShareButton({ summary, light = false }) {
  const [state, setState] = useState(null);
  const share = async () => {
    setState("busy");
    const blob = await storyCard(summary);
    setState(await shareBlob(blob, "pulsar-storia.png", summary.title));
  };
  return (
    <button className={`btn-line${light ? " btn-line--light" : ""}`} onClick={share} disabled={state === "busy"}>
      {state === "downloaded" ? "Immagine scaricata" : state === "shared" ? "Condivisa" : state === "busy" ? "Preparo l'immagine…" : "Condividi"}
    </button>
  );
}

function suggestions(story) {
  const d = story.dossier;
  const out = [];
  if (d?.divergences[0]) {
    const t = d.divergences[0].topic.trim();
    out.push(/\?$/.test(t) ? t : `${t}?`);
  }
  out.push("Cosa è confermato?", "Chi ha detto cosa?");
  return out.slice(0, 3);
}

/** Domande alla storia: risposte solo dagli articoli, con le frasi originali. */
export function AskBox({ story }) {
  const [q, setQ] = useState("");
  const [state, setState] = useState({});
  const ask = async (question) => {
    const text = (question ?? q).trim();
    if (text.length < 4) return;
    setQ(text);
    setState({ loading: true });
    try {
      setState({ result: await api.ask(story.id, text) });
    } catch (e) {
      setState({ error: e.message });
    }
  };
  const r = state.result;

  return (
    <section className="ask" aria-labelledby="ask-h">
      <h2 id="ask-h">Chiedi a questa storia</h2>
      <p className="ask-lede">Le risposte arrivano solo dagli articoli, con le frasi originali. Se la risposta non c'è, te lo diciamo.</p>
      <form
        className="ask-form"
        onSubmit={(e) => {
          e.preventDefault();
          ask();
        }}
      >
        <label htmlFor="ask-in" className="sr-only">
          La tua domanda
        </label>
        <input id="ask-in" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Es. quante persone sono rimaste ferite?" maxLength={300} />
        <button type="submit" disabled={q.trim().length < 4 || state.loading}>
          {state.loading ? "Cerco…" : "Chiedi"}
        </button>
      </form>
      <div className="ask-sugg">
        {suggestions(story).map((s) => (
          <button key={s} type="button" onClick={() => ask(s)}>
            {s}
          </button>
        ))}
      </div>

      {state.error && <p className="ask-note">{state.error}</p>}
      {r && (
        <div className="ask-answer" aria-live="polite">
          {r.certainty && r.certainty !== "non_si_sa" && (
            <p className="ask-cert">
              <StatusTag status={r.certainty} />
              {r.certainty === "contestato" && <span> Le testate danno risposte diverse.</span>}
            </p>
          )}
          {r.answer && <p className="ask-text">{r.answer}</p>}
          {r.citations.length > 0 && (
            <ul className="ask-cites">
              {r.citations.map((c, i) => (
                <li key={i}>
                  <q>{c.text}</q>
                  <span>
                    {c.source_name}
                    {c.also_in.length > 0 && <> (anche in {c.also_in.join(", ")})</>}
                    {c.fact_status && <StatusTag status={c.fact_status} />}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {r.note && <p className="ask-note">{r.note}</p>}
          <p className="ask-method">Metodo: {r.method}.</p>
        </div>
      )}
    </section>
  );
}
