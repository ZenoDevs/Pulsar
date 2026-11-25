import { useEffect, useRef, useState } from "react";
import { STATUS, STATUS_ORDER, plural } from "../lib/format";

/** La storia raccontata dallo scroll: a sinistra il testo, a destra (fisso)
 *  un'unica scena che si trasforma: le testate sull'asse, poi i fatti
 *  accertati, poi lo spacco sulle versioni, poi le cornici narrative. */
export default function Scrolly({ story, names, orientation }) {
  const d = story.dossier;
  const m = story.metrics;
  const outlets = (m?.spectrum || []).map((p) => p.source_id);
  const echoOutlets = new Set(story.articles.filter((a) => a.echo_of).map((a) => a.source_id));
  const div = d?.divergences?.[0];
  const frames = d?.framings || [];

  const steps = [
    {
      key: "chi",
      title: "Chi ne parla",
      text: `${plural(outlets.length, "testata", "testate")}, ma ${plural(m?.independence?.independent_voices ?? 0, "voce indipendente", "voci indipendenti")}. ${
        echoOutlets.size ? `${plural(echoOutlets.size, "testata ricopia", "testate ricopiano")} un testo uscito prima: i cerchi vuoti.` : "Ognuna ha scritto un testo suo."
      }`,
    },
    d?.facts?.length && {
      key: "fatti",
      title: "Cosa è accertato",
      text: `Su ${plural(d.facts.length, "fatto", "fatti")}, ${m?.status_counts?.confermato || 0} ${
        (m?.status_counts?.confermato || 0) === 1 ? "è confermato" : "sono confermati"
      } da almeno due voci indipendenti. Il resto è detto da una sola fonte, contestato o non verificabile.`,
    },
    div && {
      key: "spacco",
      title: "Dove si dividono",
      text: `${div.topic}. ${div.versions.map((v) => `Per ${v.source_ids.map((s) => names[s]).join(" e ")}: ${v.account.toLowerCase()}`).join(" ")}`,
    },
    frames.length > 1 && {
      key: "cornici",
      title: "Come la raccontano",
      text: `Stessi fatti, ${frames.length} cornici: ${frames.map((f) => f.label.toLowerCase()).join(", ")}.`,
    },
  ].filter(Boolean);

  const [active, setActive] = useState(0);
  const refs = useRef([]);
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(Number(e.target.dataset.step))),
      { rootMargin: window.matchMedia("(max-width: 1020px)").matches ? "-72% 0px -18% 0px" : "-45% 0px -45% 0px" }
    );
    refs.current.forEach((el) => el && io.observe(el));
    return () => io.disconnect();
  }, [steps.length]);

  const stepKey = steps[active]?.key;
  const pctX = (o) => ((o + 1) / 2) * 100;
  const versionOf = (sid) => (div ? div.versions.findIndex((v) => v.source_ids.includes(sid)) : -1);

  const dotPos = (sid, i) => {
    const o = orientation[sid] ?? 0;
    if (stepKey === "fatti") return { left: 8 + (i / Math.max(1, outlets.length - 1)) * 84, top: 88, opacity: 0, faded: true };
    if (stepKey === "spacco") {
      const v = versionOf(sid);
      if (v < 0) return { left: pctX(o), top: 90, opacity: 0.18, faded: true };
      const n = div.versions.length;
      const members = div.versions[v].source_ids;
      const k = members.indexOf(sid);
      return { left: ((v + 0.5) / n) * 100 + (k - (members.length - 1) / 2) * 13, top: 40 + (k % 2) * 7, opacity: 1 };
    }
    return { left: pctX(o), top: 58, opacity: 1 };
  };

  const cells = d ? [...d.facts].sort((a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)) : [];

  return (
    <section className="scrolly" aria-label="La storia in quattro passaggi">
      <div className="scrolly-steps">
        {steps.map((s, i) => (
          <div key={s.key} className={`scrolly-step${i === active ? " is-on" : ""}`} data-step={i} ref={(el) => (refs.current[i] = el)}>
            <p className="scrolly-n">{s.title}</p>
            <p className="scrolly-text">{s.text}</p>
          </div>
        ))}
      </div>

      <div className="scrolly-stage" data-state={stepKey} aria-hidden>
        <div className="sc-axis">
          <span>sinistra</span>
          <span>centro</span>
          <span>destra</span>
        </div>

        {outlets.map((sid, i) => {
          const p = dotPos(sid, i);
          return (
            <div
              key={sid}
              className={`sc-dot${echoOutlets.has(sid) ? " is-echo" : ""}${p.faded ? " is-faded" : ""}`}
              style={{ left: `${p.left}%`, top: `${p.top}%`, opacity: p.opacity }}
            >
              <span>{names[sid]}</span>
            </div>
          );
        })}

        <div className="sc-facts">
          <div className="sc-tiles">
            {cells.map((f, i) => (
              <b key={f.id} className={`sc-fact st-${f.status}`} style={{ transitionDelay: `${i * 70}ms` }} title={f.text} />
            ))}
          </div>
          <ul className="sc-legend">
            {STATUS_ORDER.filter((st) => cells.some((f) => f.status === st)).map((st) => (
              <li key={st} className={`st-${st}`}>
                <b />
                {cells.filter((f) => f.status === st).length} {STATUS[st].label.toLowerCase()}
              </li>
            ))}
          </ul>
        </div>

        {div && (
          <div className="sc-versions">
            {div.versions.map((v, i) => (
              <p key={i} style={{ left: `${((i + 0.5) / div.versions.length) * 100}%` }}>
                {v.account}
              </p>
            ))}
          </div>
        )}

        <div className="sc-frames">
          {frames.map((f, i) => {
            const vals = f.source_ids.map((s) => orientation[s]).filter((v) => v != null);
            const mean = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
            return (
              <p key={i} style={{ left: `${Math.min(84, Math.max(16, pctX(mean)))}%`, top: `${18 + (i % 2) * 14}%` }}>
                {f.label}
              </p>
            );
          })}
        </div>
      </div>
    </section>
  );
}
