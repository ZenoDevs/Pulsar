import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { StoryRow } from "../components/StoryItems";
import { api, poll } from "../lib/api";

export default function SearchPage() {
  const [params] = useSearchParams();
  const q = params.get("q") || "";
  const [result, setResult] = useState({ q: null });

  useEffect(() => {
    if (!q) return;
    let stop = () => {};
    api
      .search(q)
      .then(({ job_id }) => {
        stop = poll(() => api.searchStatus(job_id), (s) => setResult({ ...s, q }));
      })
      .catch((e) => setResult({ q, status: "failed", message: e.message }));
    return () => stop();
  }, [q]);

  const state = !q ? { status: "idle" } : result.q === q ? result : { status: "pending", message: "Avvio la ricerca…" };

  return (
    <main className="search">
      <h1 className="search-title">{q ? <>Ricerca: {q}</> : "Cerca un argomento"}</h1>
      {!q && <p className="search-hint">Scrivi un tema nella barra in alto: Pulsar cerca negli archivi delle testate e raggruppa gli articoli per fatto.</p>}
      {(state.status === "pending" || state.status === "processing") && (
        <p className="state state--loading" aria-live="polite">
          {state.message}
        </p>
      )}
      {state.status === "failed" && (
        <p className="state">
          La ricerca non è riuscita: {state.message}. Controlla che il backend sia attivo e riprova.
        </p>
      )}
      {state.status === "completed" &&
        (state.stories?.length ? (
          <section className="edition-list">
            {state.stories.map((s) => (
              <StoryRow key={s.id} s={s} />
            ))}
          </section>
        ) : (
          <p className="state">Nessun articolo trovato per “{q}”. Prova con un termine più generale.</p>
        ))}
    </main>
  );
}
