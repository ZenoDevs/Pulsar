import { STATUS_ORDER } from "../lib/format";

/** Copertina della storia. Se il feed porta una foto la usiamo; altrimenti
 *  disegniamo una copertina dai dati: gli anelli partono dalla posizione media
 *  delle testate (uno per voce indipendente), i punti sono le testate,
 *  la fascia in basso è l'impronta dei fatti. Ogni storia ha la sua. */
export default function StoryCover({ story, className = "" }) {
  if (story.image_url) {
    return (
      <div className={`cover cover--photo ${className}`}>
        <img src={story.image_url} alt="" loading="lazy" />
      </div>
    );
  }

  const m = story.metrics || {};
  const W = 320;
  const H = 200;
  const base = 150;
  const x = (o) => 24 + ((o + 1) / 2) * (W - 48);
  const cx = x(m.mean_orientation ?? 0);
  const voices = Math.max(1, m.independence?.independent_voices ?? 1);
  const seed = [...story.id].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
  const step = 15 + (seed % 9);
  const rings = Array.from({ length: voices + 2 }, (_, i) => (i + 1) * step);

  const counts = m.status_counts || {};
  const cells = [...STATUS_ORDER.flatMap((s) => Array(counts[s] || 0).fill(s)), ...Array(counts.interpretazione || 0).fill("interpretazione")];
  const cw = cells.length ? Math.min(28, (W - 48) / cells.length - 3) : 0;

  return (
    <div className={`cover ${className}`} aria-hidden>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid slice">
        <rect width={W} height={H} className="cv-bg" />
        {rings.map((r, i) => (
          <path
            key={r}
            d={`M ${cx - r} ${base} A ${r} ${r} 0 0 1 ${cx + r} ${base}`}
            className="cv-ring"
            style={{ opacity: Math.max(0.12, 0.85 - i * 0.14) }}
          />
        ))}
        <line x1="24" x2={W - 24} y1={base} y2={base} className="cv-axis" />
        <line x1={W / 2} x2={W / 2} y1={base - 6} y2={base + 6} className="cv-axis" />
        {(m.spectrum || []).map((p) => (
          <circle key={p.source_id} cx={x(p.orientation)} cy={base} r={3 + Math.min(4, p.articles)} className="cv-dot" />
        ))}
        {cells.map((s, i) => (
          <rect key={i} x={24 + i * (cw + 3)} y={H - 30} width={cw} height={14} className={`cv-cell cv-${s}`} />
        ))}
      </svg>
    </div>
  );
}
