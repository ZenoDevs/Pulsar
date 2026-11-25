import { Link } from "react-router-dom";
import Cover from "./Cover";
import { Fingerprint, Spectrum } from "./Instruments";
import { ago, plural } from "../lib/format";

export function Card({ s, size = "md", showReason = false }) {
  const ind = s.metrics?.independence;
  return (
    <article className={`card card--${size}`}>
      <Link to={`/storia/${s.id}`} className="card-link">
        <Cover story={s} variant="card" animate={size === "lg"} showFacts={false} />
        <div className="card-body">
          <p className="card-meta">
            {showReason && s.reason ? <span className="card-reason">{s.reason}</span> : s.section && <span className="card-sec">{s.section}</span>}
            {s.stats?.last_published_at && <span>{ago(s.stats.last_published_at)}</span>}
          </p>
          <h3 className="card-title">{s.title}</h3>
          {size !== "sm" && s.summary && <p className="card-summary">{s.summary}</p>}
          <div className="card-foot">
            <Fingerprint counts={s.metrics?.status_counts} />
            {ind && <span>{plural(ind.independent_voices, "voce", "voci")}</span>}
          </div>
        </div>
      </Link>
    </article>
  );
}

export function Rail({ title, kicker, stories }) {
  if (!stories.length) return null;
  return (
    <section className="rail" aria-label={title}>
      <header className="rail-head">
        <p className="rail-kicker">{kicker}</p>
        <h2 className="rail-title">{title}</h2>
      </header>
      <ul className="rail-track">
        {stories.map((s) => (
          <li key={s.id}>
            <Card s={s} size="sm" />
          </li>
        ))}
      </ul>
    </section>
  );
}

function BlindCol({ items, title, text }) {
  if (!items.length) return null;
  return (
    <div className="blind2-col">
      <h3>{title}</h3>
      <p>{text}</p>
      <ul>
        {items.map((s) => (
          <li key={s.id}>
            <Link to={`/storia/${s.id}`}>{s.title}</Link>
            <Spectrum points={s.metrics?.spectrum} />
          </li>
        ))}
      </ul>
    </div>
  );
}

export function BlindspotBand({ stories }) {
  if (!stories.length) return null;
  const right = stories.filter((s) => s.metrics?.blindspot?.side === "right");
  const left = stories.filter((s) => s.metrics?.blindspot?.side === "left");
  return (
    <section className="blind2" aria-labelledby="blind2-h">
      <div className="blind2-inner">
        <h2 id="blind2-h">Punti ciechi</h2>
        <p className="blind2-lede">Storie che metà dello spettro non ha raccontato. Se leggi solo l'altra metà, non le hai viste.</p>
        <div className="blind2-cols">
          <BlindCol items={right} title="Ignorate dalle testate di destra" text="Le trovi quasi solo a sinistra e al centro." />
          <BlindCol items={left} title="Ignorate dalle testate di sinistra" text="Le trovi quasi solo a destra e al centro." />
        </div>
      </div>
    </section>
  );
}
