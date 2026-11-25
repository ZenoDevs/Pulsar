import { Link } from "react-router-dom";
import HeadlineDial from "./HeadlineDial";
import { Fingerprint, IndependenceLine, Spectrum } from "./Instruments";
import StoryCover from "./StoryCover";
import { ago, plural } from "../lib/format";

function Meta({ s }) {
  return (
    <p className="meta">
      {s.section && <span className="meta-section">{s.section}</span>}
      <span>{plural(Object.keys(s.stats.by_source).length, "testata", "testate")}</span>
      {s.stats.last_published_at && <span>{ago(s.stats.last_published_at)}</span>}
    </p>
  );
}

/** Il fatto del giorno: fascia scura a tutta larghezza. */
export function Hero({ s }) {
  const m = s.metrics;
  const ind = m?.independence;
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-inner">
        <div className="hero-main">
          <p className="hero-kicker">
            Il fatto del giorno{s.section && <span>{s.section}</span>}
            {s.stats.last_published_at && <span>{ago(s.stats.last_published_at)}</span>}
          </p>
          <h1 id="hero-title" className="hero-title">
            <Link to={`/storia/${s.id}`}>{s.title}</Link>
          </h1>
          {s.summary && <p className="hero-summary">{s.summary}</p>}
          <HeadlineDial headlines={s.headlines || []} />
        </div>

        <aside className="hero-side">
          <div className="hero-stat">
            <span className="hero-num">{ind?.independent_voices ?? "–"}</span>
            <span>
              voci indipendenti
              <br />
              su {plural(ind?.articles ?? 0, "articolo", "articoli")}
            </span>
          </div>
          <div>
            <h2 className="side-h">Quanto è solida</h2>
            <Fingerprint counts={m?.status_counts} size="lg" showLegend animate />
          </div>
          {s.top_divergence && (
            <div className="hero-div">
              <h2 className="side-h">Non concordano su</h2>
              <p>{s.top_divergence.topic}</p>
            </div>
          )}
          <Link className="hero-cta" to={`/storia/${s.id}`}>
            Apri il dossier completo
          </Link>
        </aside>
      </div>
    </section>
  );
}

export function StoryRow({ s }) {
  const m = s.metrics;
  return (
    <article className="row">
      <Link to={`/storia/${s.id}`} className="row-cover" tabIndex={-1} aria-hidden>
        <StoryCover story={s} />
      </Link>
      <div className="row-text">
        <Meta s={s} />
        <h3 className="row-title">
          <Link to={`/storia/${s.id}`}>{s.title}</Link>
        </h3>
        {s.summary && <p className="row-summary">{s.summary}</p>}
        {s.top_divergence && (
          <p className="row-div">
            <span className="tag st-contestato">
              <span className="tag-dot" aria-hidden />
              Non concordano
            </span>{" "}
            {s.top_divergence.topic}
          </p>
        )}
      </div>
      <div className="row-instr">
        <Fingerprint counts={m?.status_counts} />
        <Spectrum points={m?.spectrum} mean={m?.mean_orientation} />
        <IndependenceLine ind={m?.independence} />
      </div>
    </article>
  );
}

export function BlindspotItem({ s }) {
  const side = s.metrics?.blindspot?.side;
  return (
    <li className="blind">
      <p className="blind-who">{side === "right" ? "Ignorata dalle testate di destra" : "Ignorata dalle testate di sinistra"}</p>
      <Link to={`/storia/${s.id}`}>{s.title}</Link>
      <Spectrum points={s.metrics?.spectrum} />
    </li>
  );
}
