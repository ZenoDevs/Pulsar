import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Briefing, GuessGame, WordOfDay } from "../components/Engage";
import { BlindspotItem, Hero, StoryRow } from "../components/StoryItems";
import { api, poll } from "../lib/api";
import { ago, plural, today } from "../lib/format";

export default function EditionPage() {
  const [params] = useSearchParams();
  const demo = params.get("demo") === "1";
  const [edition, setEdition] = useState(null);
  const [error, setError] = useState(null);
  const [job, setJob] = useState(null);
  const [section, setSection] = useState("Tutte");

  const load = () =>
    api
      .edition(demo)
      .then((e) => {
        setEdition(e);
        setError(null);
      })
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, [demo]); // eslint-disable-line react-hooks/exhaustive-deps

  const refresh = async () => {
    const { job_id } = await api.refresh();
    setJob({ status: "pending", message: "In coda" });
    poll(
      () => api.job(job_id),
      (s) => {
        setJob(s);
        if (s.status === "completed") {
          setJob(null);
          load();
        }
      }
    );
  };

  if (error)
    return (
      <div className="state">
        <h1>La prima pagina non si è caricata</h1>
        <p>{error}. Controlla che il backend sia attivo su porta 8000, poi ricarica.</p>
      </div>
    );
  if (!edition) return <div className="state state--loading">Carico la prima pagina…</div>;

  const [lead, ...rest] = edition.stories;
  const sections = ["Tutte", ...new Set(rest.map((s) => s.section).filter(Boolean))];
  const visible = section === "Tutte" ? rest : rest.filter((s) => s.section === section);

  return (
    <main className="edition">
      <div className="edition-bar">
        <p className="edition-date">{today()}</p>
        <p className="edition-stats">
          {plural(edition.stories.length, "storia", "storie")} da {plural(edition.sources_ok, "testata", "testate")},{" "}
          {edition.articles_analyzed} articoli confrontati. Aggiornata {ago(edition.generated_at)}.
        </p>
        {!demo && !edition.demo && (
          <button className="btn-quiet" onClick={refresh} disabled={!!job}>
            {job ? job.message || "Aggiorno…" : "Aggiorna"}
          </button>
        )}
      </div>

      {edition.demo && (
        <p className="demo-note">
          Edizione dimostrativa: testate, luoghi e fatti sono inventati per mostrare come funziona Pulsar.
          {!demo && (
            <>
              {" "}
              <button className="demo-btn" onClick={refresh} disabled={!!job}>
                {job ? job.message || "Genero l'edizione…" : "Genera l'edizione di oggi"}
              </button>
            </>
          )}
        </p>
      )}

      {lead && <Hero s={lead} />}

      <div className="wrap">
        {rest.length > 0 && <Briefing stories={rest.slice(0, 5)} />}

        <div className="edition-body">
          <section className="edition-list" aria-labelledby="list-h">
            <div className="list-head">
              <h2 id="list-h">Le altre storie</h2>
              {sections.length > 2 && (
                <div className="chips-filter" role="group" aria-label="Filtra per sezione">
                  {sections.map((s) => (
                    <button key={s} type="button" aria-pressed={section === s} onClick={() => setSection(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {visible.map((s) => (
              <StoryRow key={s.id} s={s} />
            ))}
          </section>

          <aside className="edition-aside">
            <GuessGame stories={edition.stories} />

            <section className="aside-block">
              <h2>Punti ciechi</h2>
              <p className="aside-intro">Storie raccontate da una parte sola. Se leggi solo l'altra, non le hai viste.</p>
              {edition.blindspots.length ? (
                <ul className="blind-list">
                  {edition.blindspots.map((s) => (
                    <BlindspotItem key={s.id} s={s} />
                  ))}
                </ul>
              ) : (
                <p className="aside-intro">Oggi nessuna storia rilevante è coperta da una parte sola.</p>
              )}
            </section>

            <WordOfDay stories={edition.stories} />

            <section className="aside-block aside-key">
              <h2>Come leggere Pulsar</h2>
              <p>
                Ogni tassello colorato è un fatto: il colore dice quanto è solido, mai da che parte sta. Le posizioni sull'asse sono
                testate, non opinioni nostre.
              </p>
              <Link to="/fonti">Fonti, proprietà e metodo</Link>
            </section>
          </aside>
        </div>
      </div>
    </main>
  );
}
