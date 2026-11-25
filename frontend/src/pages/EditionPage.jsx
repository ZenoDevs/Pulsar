import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { BlindspotItem, StoryLead, StoryRow } from "../components/StoryItems";
import { api, poll } from "../lib/api";
import { ago, plural, today } from "../lib/format";

export default function EditionPage() {
  const [params] = useSearchParams();
  const demo = params.get("demo") === "1";
  const [edition, setEdition] = useState(null);
  const [error, setError] = useState(null);
  const [job, setJob] = useState(null);

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

  return (
    <main className="edition">
      {edition.demo && (
        <p className="demo-note">
          Edizione dimostrativa: testate, luoghi e fatti sono inventati per mostrare come funziona Pulsar.{" "}
          {!demo && "Genera un'edizione reale per sostituirla."}
        </p>
      )}

      <div className="edition-head">
        <h1 className="edition-date">{today()}</h1>
        <p className="edition-stats">
          {plural(edition.stories.length, "storia", "storie")} da {plural(edition.sources_ok, "testata", "testate")},{" "}
          {edition.articles_analyzed} articoli letti e confrontati. Aggiornata {ago(edition.generated_at)}.
        </p>
        {!demo && (
          <button className="btn-quiet" onClick={refresh} disabled={!!job}>
            {job ? job.message || "Aggiorno…" : "Aggiorna l'edizione"}
          </button>
        )}
      </div>

      {lead && <StoryLead s={lead} />}

      <div className="edition-body">
        <section className="edition-list" aria-label="Altre storie">
          {rest.map((s) => (
            <StoryRow key={s.id} s={s} />
          ))}
        </section>

        <aside className="edition-aside">
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
    </main>
  );
}
