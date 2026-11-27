import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CheckPrompt, CheckResultView } from "../components/Verify";
import { api } from "../lib/api";

export default function VerifyPage() {
  const [params] = useSearchParams();
  const q = params.get("q") || "";
  const demo = params.get("demo") === "1";
  const [state, setState] = useState({ q: null });

  useEffect(() => {
    if (!q) return;
    let alive = true;
    api
      .check(q, demo)
      .then((r) => alive && setState({ q, result: r }))
      .catch((e) => alive && setState({ q, error: e.message }));
    return () => {
      alive = false;
    };
  }, [q, demo]);

  const current = state.q === q ? state : { loading: !!q };

  return (
    <main className="verify">
      <header className="verify-head">
        <h1>Hai sentito qualcosa?</h1>
        <p>
          Incolla una frase, un titolo, un messaggio inoltrato. Pulsar la confronta con quello che riportano davvero le testate,
          da sinistra a destra, e ti dice quanto regge.
        </p>
      </header>
      <CheckPrompt key={q} demo={demo} initial={q} />
      {current.loading && <p className="state state--loading">Confronto con le testate…</p>}
      {current.error && <p className="state">La verifica non è riuscita: {current.error}</p>}
      {current.result && <CheckResultView r={current.result} />}
      <aside className="verify-note">
        <h2>Come funziona</h2>
        <p>
          La frase viene confrontata con i fatti, le opinioni e le versioni di tutte le storie del giorno. Il verdetto usa le stesse
          regole del dossier: "confermato" vuol dire almeno due voci indipendenti. "Non trovata" non vuol dire falsa: vuol dire che
          nessuna testata la riporta. Non salviamo quello che scrivi.
        </p>
      </aside>
    </main>
  );
}
