import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Cover from "../components/Cover";
import { Fingerprint } from "../components/Instruments";
import { api } from "../lib/api";
import { plural, today } from "../lib/format";
import { feedPayload, loadProfile, markBriefingDone, markSeen, recordFeedback } from "../lib/profile";

const MAX = 6;

function Versions({ headlines }) {
  if (!headlines?.length) return null;
  return (
    <div className="bv" aria-label="Come l'hanno titolata le testate, da sinistra a destra">
      <p className="bv-hint">Scorri di lato: da sinistra a destra, come l'hanno titolata</p>
      <ul className="bv-track">
        {headlines.map((h) => (
          <li key={h.source_id} className="bv-card">
            <span className="pos pos--light" aria-hidden>
              <span className="pos-dot" style={{ left: `${((h.orientation + 1) / 2) * 100}%` }} />
            </span>
            <q>{h.title}</q>
            <span className="bv-src">{h.source_name}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Slide({ s, index, total, onFeedback, feedback }) {
  const fact = s.key_facts.find((f) => f.status === "confermato");
  const ind = s.metrics?.independence;
  return (
    <section className="bs" data-index={index} aria-label={`Storia ${index + 1} di ${total}`}>
      <Cover story={s} variant="full" showFacts={false} />
      <div className="bs-shade" aria-hidden />
      <div className="bs-body">
        <p className="bs-reason">
          {s.reason || s.section || "Oggi"}
          <span>
            {index + 1} / {total}
          </span>
        </p>
        <h2 className="bs-title">{s.title}</h2>
        {fact && (
          <p className="bs-fact">
            <b className="st-confermato" aria-hidden />
            {fact.text}
          </p>
        )}
        {s.top_divergence && (
          <p className="bs-fact bs-fact--div">
            <b className="st-contestato" aria-hidden />
            Non concordano su: {s.top_divergence.topic.toLowerCase()}
          </p>
        )}
        <Versions headlines={s.headlines} />
        <div className="bs-foot">
          <div className="bs-meter">
            <Fingerprint counts={s.metrics?.status_counts} />
            {ind && <span>{plural(ind.independent_voices, "voce indipendente", "voci indipendenti")}</span>}
          </div>
          <div className="bs-actions">
            <Link to={`/storia/${s.id}`} className="bs-open">
              Apri il dossier
            </Link>
            <button type="button" aria-pressed={feedback === "more"} onClick={() => onFeedback(s.id, "more")}>
              Di più così
            </button>
            <button type="button" aria-pressed={feedback === "less"} onClick={() => onFeedback(s.id, "less")}>
              Meno
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Briefing() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const demo = params.get("demo") === "1";
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [active, setActive] = useState(0);
  const [feedback, setFeedback] = useState({});
  const scroller = useRef(null);

  useEffect(() => {
    api
      .feed(feedPayload(loadProfile(), demo))
      .then(setData)
      .catch((e) => setError(e.message));
  }, [demo]);

  const stories = useMemo(() => (data ? data.for_you.slice(0, MAX) : []), [data]);

  useEffect(() => {
    const root = scroller.current;
    if (!root || !stories.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const i = Number(e.target.dataset.index);
            setActive(i);
            if (stories[i]) markSeen(stories[i].id);
            if (i >= stories.length) markBriefingDone();
          }
        });
      },
      { root, threshold: 0.6 }
    );
    root.querySelectorAll("[data-index]").forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [stories]);

  useEffect(() => {
    const onKey = (e) => {
      const root = scroller.current;
      if (!root) return;
      if (e.key === "ArrowDown" || e.key === "PageDown") {
        e.preventDefault();
        root.scrollBy({ top: root.clientHeight, behavior: "smooth" });
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        root.scrollBy({ top: -root.clientHeight, behavior: "smooth" });
      } else if (e.key === "Escape") {
        nav("/");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [nav]);

  const onFeedback = (id, kind) => {
    recordFeedback(id, kind);
    setFeedback((f) => ({ ...f, [id]: kind }));
  };

  if (error)
    return (
      <div className="state">
        <h1>Il briefing non si è caricato</h1>
        <p>
          {error}. Controlla che il backend sia attivo, poi ricarica. <Link to="/">Vai alla rivista</Link>
        </p>
      </div>
    );
  if (!data) return <div className="brief2-loading">Preparo il tuo briefing…</div>;

  const totals = stories.reduce(
    (acc, s) => {
      const c = s.metrics?.status_counts || {};
      acc.confermato += c.confermato || 0;
      acc.contestato += c.contestato || 0;
      acc.non_verificato += c.non_verificato || 0;
      return acc;
    },
    { confermato: 0, contestato: 0, non_verificato: 0 }
  );

  return (
    <main className="brief2">
      <header className="brief2-top">
        <ol className="brief2-progress" aria-hidden>
          {[...stories, null].map((_, i) => (
            <li key={i} className={i < active ? "is-done" : i === active ? "is-on" : ""} />
          ))}
        </ol>
        <div className="brief2-bar">
          <span>Il tuo briefing, {today()}</span>
          <Link to="/" onClick={markBriefingDone} aria-label="Chiudi il briefing">
            Chiudi
          </Link>
        </div>
      </header>

      <div className="brief2-scroll" ref={scroller}>
        {stories.map((s, i) => (
          <Slide key={s.id} s={s} index={i} total={stories.length} onFeedback={onFeedback} feedback={feedback[s.id]} />
        ))}
        <section className="bs bs--end" data-index={stories.length} aria-label="Fine del briefing">
          <div className="bs-end">
            <p className="bs-reason">Fine del briefing</p>
            <h2 className="bs-title">Sei aggiornato.</h2>
            <dl className="bs-tally">
              <div>
                <dt>{totals.confermato}</dt>
                <dd>fatti confermati</dd>
              </div>
              <div>
                <dt>{totals.contestato}</dt>
                <dd>punti contestati</dd>
              </div>
              <div>
                <dt>{totals.non_verificato}</dt>
                <dd>voci da prendere con le pinze</dd>
              </div>
            </dl>
            <Link to="/" className="onb-cta" onClick={markBriefingDone}>
              Vai alla tua edizione
            </Link>
            <Link to="/argomenti" className="onb-skip">
              Cambia i tuoi argomenti
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
