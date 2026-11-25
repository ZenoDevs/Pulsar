import { Link } from "react-router-dom";
import { Fingerprint, IndependenceLine, Spectrum, StatusTag } from "./Instruments";
import { ago, plural, sourceNames } from "../lib/format";

function Meta({ s }) {
  return (
    <p className="meta">
      {s.section && <span className="meta-section">{s.section}</span>}
      <span>{plural(s.stats.total_articles, "articolo", "articoli")}</span>
      <span>{plural(Object.keys(s.stats.by_source).length, "testata", "testate")}</span>
      {s.stats.last_published_at && <span>{ago(s.stats.last_published_at)}</span>}
    </p>
  );
}

export function StoryLead({ s }) {
  const names = sourceNames(s);
  const m = s.metrics;
  return (
    <article className="lead">
      <div className="lead-main">
        <Meta s={s} />
        <h2 className="lead-title">
          <Link to={`/storia/${s.id}`}>{s.title}</Link>
        </h2>
        {s.summary && <p className="lead-summary">{s.summary}</p>}
        {s.key_facts.length > 0 && (
          <ul className="lead-facts">
            {s.key_facts.map((f) => (
              <li key={f.id}>
                <StatusTag status={f.status} />
                <span>{f.text}</span>
              </li>
            ))}
          </ul>
        )}
        {s.top_divergence && (
          <div className="lead-div">
            <h3>Dove non concordano: {s.top_divergence.topic.toLowerCase()}</h3>
            <div className="lead-div-cols">
              {s.top_divergence.versions.slice(0, 2).map((v, i) => (
                <p key={i}>
                  <span className="lead-div-who">{v.source_ids.map((id) => names[id] || id).join(", ")}</span>
                  {v.account}
                </p>
              ))}
            </div>
          </div>
        )}
        <Link className="more" to={`/storia/${s.id}`}>
          Apri il dossier
        </Link>
      </div>
      <aside className="lead-side">
        <h3 className="side-h">Quanto è solida</h3>
        <Fingerprint counts={m?.status_counts} size="lg" showLegend animate />
        <h3 className="side-h">Chi la racconta</h3>
        <Spectrum points={m?.spectrum} mean={m?.mean_orientation} />
        <IndependenceLine ind={m?.independence} />
      </aside>
    </article>
  );
}

export function StoryRow({ s }) {
  const m = s.metrics;
  return (
    <article className="row">
      <div>
        <Meta s={s} />
        <h3 className="row-title">
          <Link to={`/storia/${s.id}`}>{s.title}</Link>
        </h3>
        {s.summary && <p className="row-summary">{s.summary}</p>}
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
