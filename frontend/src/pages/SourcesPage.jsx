import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { StatusTag } from "../components/Instruments";
import { api } from "../lib/api";
import { STATUS } from "../lib/format";

const KIND = { agenzia: "Agenzia", quotidiano: "Quotidiano", online: "Online", tv: "TV" };

export default function SourcesPage() {
  const [params] = useSearchParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.sources(params.get("demo") === "1").then(setData).catch((e) => setError(e.message));
  }, [params]);

  return (
    <main className="sources">
      <header className="story-head">
        <h1 className="story-title">Fonti e metodo</h1>
        <p className="story-summary">
          Pulsar non scrive notizie: le confronta. Qui trovi chi leggiamo, chi possiede cosa, e le regole con cui decidiamo che un
          fatto è confermato.
        </p>
      </header>

      <section className="dsec" id="metodo">
        <h2>Come funziona</h2>
        <ol className="method">
          <li>
            <h3>Leggiamo tutte le testate</h3>
            <p>Feed e archivi di agenzie, quotidiani, siti e telegiornali di tutto lo spettro. Gli articoli sullo stesso fatto vengono raggruppati in una storia.</p>
          </li>
          <li>
            <h3>Contiamo le voci, non gli articoli</h3>
            <p>
              Dieci articoli non sono dieci conferme. Le testate dello stesso editore contano come una voce sola, e un testo che riprende
              quasi alla lettera un lancio d'agenzia conta come l'agenzia. Lo misuriamo confrontando le sequenze di parole, senza AI.
            </p>
          </li>
          <li>
            <h3>Separiamo i fatti dalle interpretazioni</h3>
            <p>
              Un modello linguistico legge solo gli articoli della storia e scompone ciò che dicono in affermazioni, ciascuna con le testate
              che la sostengono. Non può aggiungere nulla dalla propria memoria, e le citazioni a articoli inesistenti vengono scartate.
            </p>
          </li>
          <li>
            <h3>Le regole correggono il modello, mai il contrario</h3>
            <p>
              Se il modello dice "confermato" ma le voci indipendenti sono meno di due, lo stato scende a "riportato" e la pagina spiega
              perché. Nessuna regola può alzare uno stato.
            </p>
          </li>
          <li>
            <h3>Mostriamo cosa manca</h3>
            <p>Omissioni, parole cariche, punti ciechi: le storie che una parte dello spettro non racconta affatto.</p>
          </li>
        </ol>
        <dl className="statuses">
          {["confermato", "riportato", "contestato", "non_verificato"].map((s) => (
            <div key={s}>
              <dt>
                <StatusTag status={s} />
              </dt>
              <dd>{STATUS[s].hint}</dd>
            </div>
          ))}
          <div>
            <dt>
              <span className="tag st-interpretazione">
                <span className="tag-dot" aria-hidden />
                Interpretazione
              </span>
            </dt>
            <dd>{STATUS.interpretazione.hint}</dd>
          </div>
        </dl>
      </section>

      <section className="dsec">
        <h2>Le testate</h2>
        {data && <p className="dsec-intro">{data.disclaimer} Assetti proprietari aggiornati a novembre 2026.</p>}
        {error && <p className="state">Elenco non disponibile: {error}.</p>}
        {data && (
          <div className="table-wrap">
            <table className="srcs">
              <thead>
                <tr>
                  <th scope="col">Testata</th>
                  <th scope="col">Posizione di partenza</th>
                  <th scope="col">Editore</th>
                  <th scope="col">Proprietà</th>
                </tr>
              </thead>
              <tbody>
                {data.sources.map((s) => (
                  <tr key={s.id}>
                    <th scope="row">
                      {s.name}
                      <span className="srcs-kind">{KIND[s.kind] || s.kind}</span>
                    </th>
                    <td>
                      <span className="pos pos--wide" title={`${s.orientation > 0 ? "+" : ""}${s.orientation}`}>
                        <span className="pos-dot" style={{ left: `${((s.orientation + 1) / 2) * 100}%` }} />
                      </span>
                    </td>
                    <td>
                      {s.owner}
                      {s.note && <span className="srcs-note">{s.note}</span>}
                    </td>
                    <td>
                      {s.ownership_verified ? (
                        s.ownership_source ? (
                          <a href={s.ownership_source} target="_blank" rel="noreferrer">
                            Verificata
                          </a>
                        ) : (
                          "Verificata"
                        )
                      ) : (
                        <span className="srcs-todo">Da verificare</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
