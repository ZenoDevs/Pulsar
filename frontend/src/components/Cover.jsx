import { STATUS_ORDER, toneOf } from "../lib/format";

/** Copertina viva di una storia.
 *  Con una foto dal feed: foto con velatura nella tinta della sezione.
 *  Senza: una "pulsar" disegnata dai dati. Le onde partono dalla posizione
 *  media delle testate sull'asse; ce n'è una per ogni voce indipendente;
 *  i punti sull'orizzonte sono le testate. Più voci, più onde. */
export default function Cover({ story, variant = "card", animate = true, showFacts = true }) {
  const m = story.metrics || {};
  const [hi, lo] = toneOf(story.section);
  const cx = (((m.mean_orientation ?? 0) + 1) / 2) * 100;
  const voices = Math.max(1, Math.min(7, m.independence?.independent_voices ?? 1));
  const counts = m.status_counts || {};
  const cells = [...STATUS_ORDER.flatMap((s) => Array(counts[s] || 0).fill(s)), ...Array(counts.interpretazione || 0).fill("interpretazione")];

  return (
    <div
      className={`cover2 cover2--${variant}${animate ? " is-live" : ""}`}
      style={{ "--hi": hi, "--lo": lo, "--cx": `${cx}%` }}
      aria-hidden
    >
      {story.image_url ? (
        <img className="cover2-photo" src={story.image_url} alt="" loading="lazy" />
      ) : (
        <>
          <div className="cover2-glow" />
          <div className="cover2-waves">
            {Array.from({ length: voices + 1 }, (_, i) => (
              <span key={i} style={{ animationDelay: `${(i * 4.2) / (voices + 1)}s` }} />
            ))}
          </div>
          <div className="cover2-horizon">
            {(m.spectrum || []).map((p) => (
              <i key={p.source_id} style={{ left: `${((p.orientation + 1) / 2) * 100}%`, "--s": `${6 + Math.min(6, p.articles * 2)}px` }} />
            ))}
          </div>
        </>
      )}
      {showFacts && cells.length > 0 && (
        <div className="cover2-facts">
          {cells.map((s, i) => (
            <b key={i} className={`st-${s}`} />
          ))}
        </div>
      )}
    </div>
  );
}
