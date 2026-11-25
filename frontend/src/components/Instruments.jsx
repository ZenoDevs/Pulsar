import { STATUS, STATUS_ORDER, plural } from "../lib/format";

/** Un tassello per ogni fatto, colorato per stato, poi le interpretazioni. */
export function Fingerprint({ counts = {}, facts, size = "sm", animate = false, showLegend = false }) {
  const cells = facts
    ? facts.map((f) => f.status)
    : STATUS_ORDER.flatMap((s) => Array(counts[s] || 0).fill(s));
  const interp = counts.interpretazione || 0;
  const all = [...cells, ...Array(interp).fill("interpretazione")];

  if (!all.length) {
    return <p className="fp-empty">Nessun dossier: servono almeno due testate per confrontare i fatti.</p>;
  }

  const summary = [...STATUS_ORDER, "interpretazione"]
    .map((s) => [s, all.filter((c) => c === s).length])
    .filter(([, n]) => n);

  return (
    <div className={`fp fp--${size}`}>
      <div
        className={`fp-cells${animate ? " fp-cells--animate" : ""}`}
        role="img"
        aria-label={summary.map(([s, n]) => `${n} ${n === 1 ? STATUS[s].label.toLowerCase() : STATUS[s].many}`).join(", ")}
      >
        {all.map((s, i) => (
          <span
            key={i}
            className={`fp-cell st-${s}${s === "interpretazione" && i === cells.length ? " fp-cell--gap" : ""}`}
            style={animate ? { animationDelay: `${i * 45}ms` } : undefined}
            title={STATUS[s].label}
          />
        ))}
      </div>
      {showLegend && (
        <ul className="fp-legend">
          {summary.map(([s, n]) => (
            <li key={s}>
              <span className={`fp-cell st-${s}`} aria-hidden /> {n} {n === 1 ? STATUS[s].label.toLowerCase() : STATUS[s].many}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function StatusTag({ status, from }) {
  const meta = STATUS[status] || STATUS.non_verificato;
  return (
    <span className={`tag st-${status}`} title={meta.hint}>
      <span className="tag-dot" aria-hidden />
      {meta.label}
      {from && <s className="tag-from">{STATUS[from]?.label}</s>}
    </span>
  );
}

/** Lo spettro: dove stanno, su un asse, le testate che hanno coperto la storia.
 *  In piccolo è un asse con i punti; in grande diventa un grafico a punti,
 *  una riga per testata, così i nomi non si sovrappongono. */
export function Spectrum({ points = [], mean, size = "sm" }) {
  if (!points.length) return null;
  const x = (o) => `${((o + 1) / 2) * 100}%`;
  const label = "Posizione delle testate che hanno coperto la storia, da sinistra a destra";

  if (size === "lg") {
    return (
      <figure className="spec spec--lg" aria-label={label}>
        <ul className="spec-rows">
          {points.map((p) => (
            <li key={p.source_id}>
              <span className="spec-row-name">
                {p.source_name}
                {p.articles > 1 && <span className="spec-row-n"> {p.articles}</span>}
              </span>
              <span className="spec-row-track">
                <span className="spec-dot" style={{ left: x(p.orientation) }} />
              </span>
            </li>
          ))}
        </ul>
        <figcaption className="spec-scale spec-scale--lg">
          <span>sinistra</span>
          <span>centro</span>
          <span>destra</span>
        </figcaption>
      </figure>
    );
  }

  const rows = [];
  const placed = points.map((p) => {
    let row = 0;
    while ((rows[row] || []).some((o) => Math.abs(o - p.orientation) < 0.09)) row++;
    (rows[row] = rows[row] || []).push(p.orientation);
    return { ...p, row };
  });

  return (
    <figure className="spec spec--sm" aria-label={label}>
      <div className="spec-track" style={{ height: 12 + rows.length * 9 }}>
        <span className="spec-axis" />
        <span className="spec-mid" />
        {placed.map((p) => (
          <span
            key={p.source_id}
            className="spec-pt"
            style={{ left: x(p.orientation), bottom: 5 + p.row * 9, "--r": `${Math.min(14, 6 + p.articles * 2)}px` }}
            title={`${p.source_name}: ${plural(p.articles, "articolo", "articoli")}`}
          />
        ))}
      </div>
      {mean != null && (
        <div className="spec-meanrow">
          <span className="spec-mean" style={{ left: x(mean) }} title="Posizione media delle testate" />
        </div>
      )}
      <figcaption className="spec-scale">
        <span>sinistra</span>
        <span>centro</span>
        <span>destra</span>
      </figcaption>
    </figure>
  );
}

export function IndependenceLine({ ind }) {
  if (!ind) return null;
  return (
    <p className="indep">
      <strong>{plural(ind.independent_voices, "voce indipendente", "voci indipendenti")}</strong> su{" "}
      {plural(ind.articles, "articolo", "articoli")}
      {ind.echoes > 0 && <>, {plural(ind.echoes, "ripresa", "riprese")} quasi letterali</>}
    </p>
  );
}

export function SourceChips({ ids = [], names = {}, muted = false }) {
  return (
    <span className={`chips${muted ? " chips--muted" : ""}`}>
      {ids.map((id) => (
        <span key={id} className="chip">
          {names[id] || id}
        </span>
      ))}
    </span>
  );
}
