import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Fingerprint, IndependenceLine, SourceChips, Spectrum, StatusTag } from "../components/Instruments";
import { api } from "../lib/api";
import { INTERP_KIND, STATUS_ORDER, clock, pct, plural, sourceNames } from "../lib/format";

function Section({ id, title, intro, children }) {
  return (
    <section id={id} className="dsec" aria-labelledby={`${id}-h`}>
      <h2 id={`${id}-h`}>{title}</h2>
      {intro && <p className="dsec-intro">{intro}</p>}
      {children}
    </section>
  );
}

function FactRow({ f, names, articlesById }) {
  return (
    <li className={`fact st-row-${f.status}`}>
      <details>
        <summary>
          <StatusTag status={f.status} from={f.downgraded_from} />
          <span className="fact-text">{f.text}</span>
        </summary>
        <div className="fact-body">
          {f.note && <p className="fact-note">{f.note}</p>}
          {f.verification && (
            <p className="fact-check">
              {f.downgraded_from ? "Declassato da Pulsar: " : ""}
              {f.verification}
            </p>
          )}
          <ul className="fact-cites">
            {f.article_ids.map((id) => {
              const a = articlesById[id];
              if (!a) return null;
              return (
                <li key={id}>
                  <span className="fact-cite-src">{a.source_name}</span>
                  {a.url ? (
                    <a href={a.url} target="_blank" rel="noreferrer">
                      {a.title}
                    </a>
                  ) : (
                    <span>{a.title}</span>
                  )}
                  {a.echo_of && <span className="echo">ripresa</span>}
                </li>
              );
            })}
          </ul>
        </div>
      </details>
      <div className="fact-foot">
        <SourceChips ids={f.source_ids} names={names} />
        <span className="fact-voices">{plural(f.independent_voices, "voce", "voci")}</span>
      </div>
    </li>
  );
}

function Position({ ids, orientation }) {
  const vals = ids.map((id) => orientation[id]).filter((v) => v != null);
  if (!vals.length) return null;
  const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
  return (
    <span className="pos" aria-label="Posizione media delle testate sull'asse sinistra-destra">
      <span className="pos-dot" style={{ left: `${((mean + 1) / 2) * 100}%` }} />
    </span>
  );
}

export default function StoryPage() {
  const { id } = useParams();
  const [loaded, setLoaded] = useState({ id: null, story: null, error: null });

  useEffect(() => {
    api
      .story(id)
      .then((story) => setLoaded({ id, story, error: null }))
      .catch((e) => setLoaded({ id, story: null, error: e.message }));
    window.scrollTo(0, 0);
  }, [id]);

  const current = loaded.id === id;
  const story = current ? loaded.story : null;
  const error = current ? loaded.error : null;

  const derived = useMemo(() => {
    if (!story) return null;
    const names = sourceNames(story);
    const orientation = {};
    story.metrics?.spectrum.forEach((p) => (orientation[p.source_id] = p.orientation));
    const articlesById = Object.fromEntries(story.articles.map((a) => [a.id, a]));
    const bySource = {};
    story.articles.forEach((a) => (bySource[a.source_id] = [...(bySource[a.source_id] || []), a]));
    const outlets = Object.keys(bySource).sort((a, b) => (orientation[a] ?? 0) - (orientation[b] ?? 0));
    return { names, orientation, articlesById, bySource, outlets };
  }, [story]);

  if (error)
    return (
      <div className="state">
        <h1>Storia non trovata</h1>
        <p>
          {error}. Le storie delle ricerche restano disponibili finché il backend conserva il database. <Link to="/">Torna alla prima pagina</Link>
        </p>
      </div>
    );
  if (!story) return <div className="state state--loading">Apro il dossier…</div>;

  const d = story.dossier;
  const m = story.metrics;
  const { names, orientation, articlesById, bySource, outlets } = derived;
  const facts = d ? [...d.facts].sort((a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)) : [];
  const toc = [
    ["sappiamo", "Cosa sappiamo", facts.length],
    ["divergenze", "Dove non concordano", d?.divergences.length],
    ["racconto", "Come la raccontano", d?.framings.length],
    ["interpretazioni", "Opinioni e interpretazioni", d?.interpretations.length],
    ["omissioni", "Cosa manca, e a chi", d?.omissions.length],
    ["parole", "Parole cariche", d?.loaded_language.length],
    ["domande", "Cosa non sappiamo ancora", d?.open_questions.length],
    ["cronologia", "Chi l'ha detto e quando", m?.timeline.length],
    ["articoli", "Tutti gli articoli", story.articles.length],
  ].filter(([, , n]) => n);

  return (
    <main className="story">
      <Link to="/" className="back">
        Prima pagina
      </Link>

      <header className="story-head">
        <p className="meta">
          {story.section && <span className="meta-section">{story.section}</span>}
          <span>
            {plural(story.stats.total_articles, "articolo", "articoli")} da {plural(outlets.length, "testata", "testate")}
          </span>
          {m?.first_reported_by && <span>prima notizia: {m.first_reported_by}</span>}
        </p>
        <h1 className="story-title">{story.title}</h1>
        {d?.summary && <p className="story-summary">{d.summary}</p>}
        {m?.blindspot && <p className="story-blind">{m.blindspot.message}</p>}
      </header>

      <div className="story-grid">
        <div className="story-main">
          {!d && (
            <p className="nodossier">
              Per questa storia non c'è ancora un dossier: serve un modello linguistico configurato nel backend e almeno due testate
              che ne parlino. Sotto trovi comunque spettro, cronologia e articoli.
            </p>
          )}

          {facts.length > 0 && (
            <Section
              id="sappiamo"
              title="Cosa sappiamo"
              intro="Ogni affermazione verificabile, con lo stato e chi la riporta. Apri una riga per vedere gli articoli citati."
            >
              <ul className="facts">
                {facts.map((f) => (
                  <FactRow key={f.id} f={f} names={names} articlesById={articlesById} />
                ))}
              </ul>
            </Section>
          )}

          {d?.divergences.length > 0 && (
            <Section id="divergenze" title="Dove non concordano">
              {d.divergences.map((dv, i) => (
                <div key={i} className="div">
                  <h3>{dv.topic}</h3>
                  <div className="div-versions">
                    {dv.versions.map((v, j) => (
                      <div key={j} className="div-v">
                        <p>{v.account}</p>
                        <SourceChips ids={v.source_ids} names={names} />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </Section>
          )}

          {d?.framings.length > 0 && (
            <Section
              id="racconto"
              title="Come la raccontano"
              intro="Gli stessi fatti dentro cornici diverse. Le cornici sono ordinate dalla testata più a sinistra a quella più a destra."
            >
              <div className="frames">
                {d.framings.map((fr, i) => (
                  <div key={i} className="frame">
                    <Position ids={fr.source_ids} orientation={orientation} />
                    <h3>{fr.label}</h3>
                    <p>{fr.frame}</p>
                    {fr.keywords.length > 0 && (
                      <p className="frame-kw">
                        {fr.keywords.map((k) => (
                          <q key={k}>{k}</q>
                        ))}
                      </p>
                    )}
                    <SourceChips ids={fr.source_ids} names={names} muted />
                  </div>
                ))}
              </div>
            </Section>
          )}

          {d?.interpretations.length > 0 && (
            <Section id="interpretazioni" title="Opinioni e interpretazioni" intro="Non sono fatti. Sono qui perché sapere chi le sostiene aiuta a pesarle.">
              <ul className="interps">
                {d.interpretations.map((it, i) => (
                  <li key={i}>
                    <span className="interp-kind">{INTERP_KIND[it.kind] || "Opinione"}</span>
                    <p>{it.text}</p>
                    <SourceChips ids={it.source_ids} names={names} muted />
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {d?.omissions.length > 0 && (
            <Section id="omissioni" title="Cosa manca, e a chi">
              <ul className="omits">
                {d.omissions.map((o, i) => (
                  <li key={i}>
                    <p>{o.element}</p>
                    <dl>
                      <dt>Lo riportano</dt>
                      <dd>
                        <SourceChips ids={o.present_in} names={names} />
                      </dd>
                      <dt>Non ne parlano</dt>
                      <dd>
                        <SourceChips ids={o.absent_in} names={names} muted />
                      </dd>
                    </dl>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {d?.loaded_language.length > 0 && (
            <Section id="parole" title="Parole cariche" intro="Termini che portano un giudizio dentro la notizia, con un'alternativa neutra.">
              <table className="words">
                <thead>
                  <tr>
                    <th scope="col">Scritto</th>
                    <th scope="col">Detto in modo neutro</th>
                    <th scope="col">Perché</th>
                  </tr>
                </thead>
                <tbody>
                  {d.loaded_language.map((t, i) => (
                    <tr key={i}>
                      <td>
                        <q className="word-loaded">{t.term}</q>
                        {t.source_id && <span className="word-src">{names[t.source_id]}</span>}
                      </td>
                      <td>{t.neutral}</td>
                      <td className="word-why">{t.why}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {d?.open_questions.length > 0 && (
            <Section id="domande" title="Cosa non sappiamo ancora">
              <ul className="questions">
                {d.open_questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </Section>
          )}

          {m?.timeline.length > 0 && (
            <Section id="cronologia" title="Chi l'ha detto e quando" intro="Le riprese sono testi quasi identici a uno uscito prima: non contano come conferme.">
              <ol className="tl">
                {m.timeline.map((t) => (
                  <li key={t.article_id} className={t.is_echo ? "tl-echo" : ""}>
                    <time>{clock(t.published_at)}</time>
                    <span className="tl-src">{t.source_name}</span>
                    <span className="tl-title">
                      {t.title}
                      {t.is_echo && <span className="echo">ripresa</span>}
                    </span>
                  </li>
                ))}
              </ol>
            </Section>
          )}

          <Section id="articoli" title="Tutti gli articoli">
            <div className="arts">
              {outlets.map((sid) => (
                <div key={sid} className="arts-src">
                  <h3>{names[sid]}</h3>
                  <ul>
                    {bySource[sid].map((a) => (
                      <li key={a.id}>
                        {a.url ? (
                          <a href={a.url} target="_blank" rel="noreferrer">
                            {a.title}
                          </a>
                        ) : (
                          <span className="art-title">{a.title}</span>
                        )}
                        <p className="art-snip">{a.snippet}</p>
                        {a.bias_explanation && (
                          <p className="art-bias">
                            Lettura del testo: {a.bias_explanation} ({pct(a.bias_confidence)} di affidabilità)
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Section>
        </div>

        <aside className="story-rail">
          <div className="rail-block">
            <h2 className="side-h">Quanto è solida</h2>
            <Fingerprint facts={facts} counts={m?.status_counts} size="lg" showLegend animate />
            {m?.solidity != null && (
              <p className="rail-note">
                {pct(m.solidity)} dei fatti è confermato da almeno due voci indipendenti.
              </p>
            )}
          </div>
          <div className="rail-block">
            <h2 className="side-h">Chi la racconta</h2>
            <Spectrum points={m?.spectrum} mean={m?.mean_orientation} size="lg" />
            <IndependenceLine ind={m?.independence} />
          </div>
          {toc.length > 2 && (
            <nav className="rail-block rail-toc" aria-label="In questa pagina">
              <h2 className="side-h">In questa pagina</h2>
              <ul>
                {toc.map(([id, label, n]) => (
                  <li key={id}>
                    <a href={`#${id}`}>{label}</a>
                    <span>{n}</span>
                  </li>
                ))}
              </ul>
            </nav>
          )}
          {d && (
            <p className="rail-gen">
              Dossier generato {d.generated_by === "demo" ? "a mano per la demo" : `da un modello (${d.generated_by})`} a partire dai soli
              articoli elencati. Gli stati sono poi controllati da regole fisse: possono essere abbassati, mai alzati.{" "}
              <Link to="/fonti#metodo">Come funziona</Link>
            </p>
          )}
        </aside>
      </div>
    </main>
  );
}

