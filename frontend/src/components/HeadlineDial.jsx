import { useEffect, useMemo, useRef, useState } from "react";

const nearest = (headlines, v) =>
  headlines.reduce((best, h) => (Math.abs(h.orientation - v) < Math.abs(best.orientation - v) ? h : best), headlines[0]);

/** "Lo stesso fatto, giornali diversi": trascini il cursore sull'asse e il
 *  titolo cambia con quello della testata più vicina. Al primo caricamento
 *  il cursore attraversa l'asse una volta da solo, per far capire il gesto. */
export default function HeadlineDial({ headlines }) {
  const min = headlines[0]?.orientation ?? -1;
  const max = headlines[headlines.length - 1]?.orientation ?? 1;
  const [value, setValue] = useState(min);
  const touched = useRef(false);
  const current = useMemo(() => nearest(headlines, value), [headlines, value]);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || headlines.length < 2) return;
    let frame;
    let start;
    const duration = 900 * headlines.length;
    const tick = (t) => {
      if (touched.current) return;
      start ??= t;
      const k = Math.min(1, (t - start) / duration);
      const eased = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2;
      setValue(min + (max - min) * eased);
      if (k < 1) frame = requestAnimationFrame(tick);
    };
    const delay = setTimeout(() => (frame = requestAnimationFrame(tick)), 700);
    return () => {
      clearTimeout(delay);
      cancelAnimationFrame(frame);
    };
  }, [headlines, min, max]);

  if (headlines.length < 2) return null;
  const pos = (o) => `${((o + 1) / 2) * 100}%`;
  const user = (v) => {
    touched.current = true;
    setValue(v);
  };

  return (
    <div className="dial">
      <p className="dial-lede">Come l'hanno titolato. Trascina sull'asse per cambiare giornale.</p>
      <blockquote className="dial-quote" key={current.source_id} aria-live="polite">
        <p>{current.title}</p>
        <footer>
          {current.url ? (
            <a href={current.url} target="_blank" rel="noreferrer">
              {current.source_name}
            </a>
          ) : (
            current.source_name
          )}
        </footer>
      </blockquote>

      <div className="dial-axis">
        <div className="dial-track">
          {headlines.map((h) => (
            <button
              key={h.source_id}
              type="button"
              className={`dial-stop${h.source_id === current.source_id ? " is-on" : ""}`}
              style={{ left: pos(h.orientation) }}
              onClick={() => user(h.orientation)}
              aria-label={`Titolo di ${h.source_name}`}
            />
          ))}
          <span className="dial-thumb" style={{ left: pos(value) }} aria-hidden />
          <input
            type="range"
            min={-1}
            max={1}
            step={0.01}
            value={value}
            onChange={(e) => user(Number(e.target.value))}
            aria-label="Posizione sull'asse sinistra-destra"
            aria-valuetext={current.source_name}
          />
        </div>
        <div className="dial-scale">
          <span>sinistra</span>
          <span>centro</span>
          <span>destra</span>
        </div>
      </div>
    </div>
  );
}
