import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../components/Cards";
import { api } from "../lib/api";
import { feedPayload, loadProfile } from "../lib/profile";

const SIDE = (m) => (m == null ? null : m <= -0.15 ? "left" : m >= 0.15 ? "right" : "center");

/** Lo specchio: da che parte dello spettro arrivano le storie che leggi.
 *  Tutto calcolato nel browser con le tue letture: niente esce dal dispositivo. */
export default function MirrorPage() {
  const [profile] = useState(loadProfile);
  const reads = useMemo(() => (profile.reads || []).filter((r) => r.mean != null), [profile]);
  const [suggest, setSuggest] = useState([]);

  const avg = reads.length ? reads.reduce((a, r) => a + r.mean, 0) / reads.length : null;
  const share = { left: 0, center: 0, right: 0 };
  reads.forEach((r) => (share[SIDE(r.mean)] += 1));
  const n = reads.length || 1;
  const lean = avg == null ? null : avg <= -0.12 ? "left" : avg >= 0.12 ? "right" : "center";

  const sections = {};
  (profile.reads || []).forEach((r) => r.section && (sections[r.section] = (sections[r.section] || 0) + 1));
  const sectionList = Object.entries(sections).sort((a, b) => b[1] - a[1]);
  const maxSec = sectionList[0]?.[1] || 1;

  useEffect(() => {
    if (lean === null || lean === "center") return;
    api
      .feed(feedPayload(loadProfile(), false))
      .then((r) => {
        const pool = [...r.for_you, ...r.blindspots];
        const seen = new Set((profile.reads || []).map((x) => x.id));
        const opposite = pool.filter((s) => {
          const m = s.metrics?.mean_orientation;
          const blind = s.metrics?.blindspot?.side;
          if (seen.has(s.id)) return false;
          return lean === "left" ? m >= 0.05 || blind === "left" : m <= -0.05 || blind === "right";
        });
        setSuggest([...new Map(opposite.map((s) => [s.id, s])).values()].slice(0, 3));
      })
      .catch(() => {});
  }, [lean, profile]);

  const message =
    lean === null
      ? "Apri qualche storia: lo specchio si riempie mentre leggi."
      : lean === "center"
        ? "Leggi storie raccontate da tutto lo spettro. Continua così."
        : lean === "left"
          ? "Le storie che apri sono raccontate soprattutto da testate di sinistra."
          : "Le storie che apri sono raccontate soprattutto da testate di destra.";

  return (
    <main className="mirror">
      <header className="mirror-head">
        <h1>Il tuo specchio</h1>
        <p>Da che parte arrivano le notizie che leggi davvero. Lo vedi solo tu: è calcolato su questo dispositivo.</p>
      </header>

      <section className="mirror-axis" aria-label="Le tue letture sull'asse sinistra-destra">
        <div className="mirror-track">
          {reads.map((r, i) => (
            <span key={r.id} className="mirror-dot" style={{ left: `${((r.mean + 1) / 2) * 100}%`, bottom: `${8 + (i % 6) * 14}px` }} title={r.title} />
          ))}
          {avg != null && (
            <span className="mirror-avg" style={{ left: `${((avg + 1) / 2) * 100}%` }}>
              <span>tu</span>
            </span>
          )}
        </div>
        <div className="mirror-scale">
          <span>sinistra</span>
          <span>centro</span>
          <span>destra</span>
        </div>
        <p className="mirror-msg">{message}</p>
      </section>

      <div className="mirror-grid">
        <section className="mirror-box">
          <h2>Le tue letture</h2>
          <dl className="mirror-share">
            {[
              ["left", "Coperte soprattutto a sinistra"],
              ["center", "Coperte da tutto lo spettro"],
              ["right", "Coperte soprattutto a destra"],
            ].map(([k, label]) => (
              <div key={k}>
                <dt>{Math.round((share[k] / n) * 100)}%</dt>
                <dd>{label}</dd>
              </div>
            ))}
          </dl>
          <p className="mirror-small">
            {reads.length} storie lette di recente.{" "}
            {profile.streak?.count > 1 && <>Briefing completato {profile.streak.count} giorni di fila.</>}
          </p>
        </section>

        <section className="mirror-box">
          <h2>Le sezioni che leggi</h2>
          {sectionList.length ? (
            <ul className="mirror-sections">
              {sectionList.map(([sec, c]) => (
                <li key={sec}>
                  <span>{sec}</span>
                  <span className="tp-bar">
                    <span style={{ width: `${(c / maxSec) * 100}%` }} />
                  </span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mirror-small">Ancora nessuna lettura.</p>
          )}
        </section>
      </div>

      {suggest.length > 0 && (
        <section className="mirror-suggest">
          <h2>Allarga lo sguardo</h2>
          <p>Tre storie che oggi si leggono soprattutto dall'altra parte. Non per cambiare idea: per sapere cosa vede chi non la pensa come te.</p>
          <div className="day-grid">
            {suggest.map((s) => (
              <Card key={s.id} s={s} />
            ))}
          </div>
        </section>
      )}

      <p className="mirror-foot">
        Lo specchio guarda dove si colloca la copertura delle storie che apri, non le tue opinioni.{" "}
        <Link to="/argomenti">Gestisci argomenti e dati</Link>
      </p>
    </main>
  );
}
