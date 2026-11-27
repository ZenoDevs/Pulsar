import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { BlindspotBand, Card, Rail } from "../components/Cards";
import Cover from "../components/Cover";
import { GuessGame, WordOfDay } from "../components/Engage";
import Followed from "../components/Followed";
import { CheckPrompt } from "../components/Verify";
import HeadlineDial from "../components/HeadlineDial";
import { Fingerprint } from "../components/Instruments";
import { api, poll } from "../lib/api";
import { ago, plural, today } from "../lib/format";
import { feedPayload, isBriefingDue, loadProfile } from "../lib/profile";

function greeting() {
  const h = new Date().getHours();
  if (h < 13) return "Buongiorno.";
  if (h < 18) return "Buon pomeriggio.";
  return "Buonasera.";
}

function CoverStory({ s }) {
  const ind = s.metrics?.independence;
  return (
    <section className="cs" aria-labelledby="cs-title">
      <div className="cs-visual">
        <Cover story={s} variant="hero" showFacts={false} />
        <div className="cs-shade" aria-hidden />
        <div className="cs-copy">
          <p className="cs-kicker">{s.reason || "Il fatto del giorno"}</p>
          <h1 id="cs-title" className="cs-title">
            <Link to={`/storia/${s.id}`}>{s.title}</Link>
          </h1>
          {s.summary && <p className="cs-summary">{s.summary}</p>}
          <div className="cs-row">
            <Link to={`/storia/${s.id}`} className="cs-cta">
              Apri il dossier
            </Link>
            <div className="cs-meter">
              <Fingerprint counts={s.metrics?.status_counts} size="lg" />
              {ind && (
                <span>
                  {plural(ind.independent_voices, "voce indipendente", "voci indipendenti")} su {plural(ind.articles, "articolo", "articoli")}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
      {s.headlines?.length > 1 && (
        <div className="cs-dial">
          <HeadlineDial headlines={s.headlines} />
        </div>
      )}
    </section>
  );
}

export default function Home() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const demo = params.get("demo") === "1";
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [job, setJob] = useState(null);
  const profile = loadProfile();

  useEffect(() => {
    const p = loadProfile();
    const q = demo ? "?demo=1" : "";
    if (!p.onboarded) nav(`/benvenuto${q}`, { replace: true });
    else if (isBriefingDue(p)) nav(`/briefing${q}`, { replace: true });
  }, [nav, demo]);

  const load = () =>
    api
      .feed(feedPayload(loadProfile(), demo))
      .then(setData)
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, [demo]); // eslint-disable-line react-hooks/exhaustive-deps

  const refresh = async () => {
    const { job_id } = await api.refresh();
    setJob({ message: "In coda" });
    poll(
      () => api.job(job_id),
      (s) => {
        setJob(s);
        if (s.status === "completed" || s.status === "failed") {
          setJob(null);
          load();
        }
      }
    );
  };

  if (error)
    return (
      <div className="state">
        <h1>L'edizione non si è caricata</h1>
        <p>{error}. Controlla che il backend sia attivo su porta 8000, poi ricarica.</p>
      </div>
    );
  if (!data) return <div className="state state--loading">Preparo la tua edizione…</div>;

  const { edition, for_you, rails, blindspots } = data;
  const [lead, ...rest] = for_you;
  const forYouCount = for_you.filter((s) => s.reason?.startsWith("Perché segui")).length;
  const inRails = new Set(rails.flatMap((r) => r.stories.map((s) => s.id)));
  const notInRails = rest.filter((s) => !inRails.has(s.id));
  const shown = new Set([lead?.id, ...(notInRails.length >= 3 ? inRails : [])]);
  const railsShown = rails
    .map((r) => ({ ...r, stories: r.stories.filter((s) => s.id !== lead?.id) }))
    .filter((r) => r.stories.length);

  return (
    <main className="home">
      <div className="home-hello">
        <div>
          <p className="home-greet">{greeting()}</p>
          <p className="home-sub">
            {today()}. {plural(for_you.length, "storia", "storie")} da {plural(edition.sources_ok, "testata", "testate")}
            {forYouCount > 0 && <>, {forYouCount} sui tuoi argomenti</>}. Aggiornata {ago(edition.generated_at)}.
            {profile.streak?.count > 1 && profile.streak.last === new Date().toLocaleDateString("sv-SE") && (
              <span className="home-streak"> Briefing letto {profile.streak.count} giorni di fila.</span>
            )}
          </p>
        </div>
        <div className="home-actions">
          <Link to={`/briefing${demo ? "?demo=1" : ""}`} className="btn-line">
            Rivedi il briefing
          </Link>
          <Link to="/argomenti" className="btn-line">
            I tuoi argomenti{profile.topics.length ? ` (${profile.topics.length})` : ""}
          </Link>
        </div>
      </div>

      {edition.demo && (
        <p className="demo-note">
          Edizione dimostrativa: testate, luoghi e fatti sono inventati per mostrare come funziona Pulsar.
          {!demo && (
            <button className="demo-btn" onClick={refresh} disabled={!!job}>
              {job ? job.message || "Genero l'edizione…" : "Genera l'edizione di oggi"}
            </button>
          )}
        </p>
      )}

      {lead && <CoverStory s={lead} />}

      <section className="checkband" aria-labelledby="checkband-h">
        <div className="checkband-inner">
          <div>
            <h2 id="checkband-h">Hai sentito qualcosa?</h2>
            <p>Incolla una frase vista sui social o in una chat. Ti diciamo se le testate la confermano, la smentiscono o non ne parlano.</p>
          </div>
          <CheckPrompt demo={demo} />
        </div>
      </section>

      <div className="home-wrap">
        <Followed demo={demo} />
        {railsShown.map((r) => (
          <Rail key={r.id} kicker="Perché lo segui" title={r.label} stories={r.stories} />
        ))}

        <section className="day" aria-labelledby="day-h">
          <header className="rail-head">
            <p className="rail-kicker">Tutto il resto, in ordine di importanza</p>
            <h2 id="day-h" className="rail-title">La giornata</h2>
          </header>
          <div className="day-grid">
            {rest
              .filter((s) => !shown.has(s.id))
              .map((s, i) => (
                <Card key={s.id} s={s} size={i === 0 ? "lg" : "md"} showReason />
              ))}
          </div>
        </section>
      </div>

      <section className="play">
        <div className="play-inner">
          <GuessGame stories={for_you} />
          <WordOfDay stories={for_you} />
        </div>
      </section>

      <BlindspotBand stories={blindspots} />
    </main>
  );
}
