import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { VERDICT } from "../lib/format";
import { checkCard, shareBlob } from "../lib/sharecard";
import { StatusTag } from "./Instruments";

const EXAMPLES = [
  "Sono morte tre persone nel crollo del ponte",
  "La missione navale è stata approvata con 250 voti",
  "Il governo ha abolito l'IMU sulla prima casa",
  "La legge sugli affitti è un esproprio della proprietà privata",
];

/** Il campo "Hai sentito qualcosa?": porta alla pagina di verifica. */
export function CheckPrompt({ dark = false, demo = false, initial = "" }) {
  const nav = useNavigate();
  const [q, setQ] = useState(initial);
  const go = (text) => {
    const t = (text ?? q).trim();
    if (t.length >= 8) nav(`/verifica?q=${encodeURIComponent(t)}${demo ? "&demo=1" : ""}`);
  };
  return (
    <div className={`checkp${dark ? " checkp--dark" : ""}`}>
      <form
        className="checkp-form"
        onSubmit={(e) => {
          e.preventDefault();
          go();
        }}
      >
        <label htmlFor="checkp-in" className="sr-only">
          Incolla una frase da verificare
        </label>
        <textarea
          id="checkp-in"
          rows={2}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              go();
            }
          }}
          placeholder="Incolla qui una frase vista su WhatsApp, sui social o in TV"
          maxLength={500}
        />
        <button type="submit" disabled={q.trim().length < 8}>
          Verifica
        </button>
      </form>
      <div className="checkp-examples">
        <span>Prova con:</span>
        {EXAMPLES.slice(0, 3).map((e) => (
          <button key={e} type="button" onClick={() => go(e)}>
            {e}
          </button>
        ))}
      </div>
    </div>
  );
}

const KIND = { fatto: "Fatto", interpretazione: "Opinione", versione: "Versione", titolo: "Titolo" };

export function CheckResultView({ r }) {
  const [shared, setShared] = useState(null);
  const tone = VERDICT[r.verdict]?.tone || "neutro";
  const share = async () => {
    const blob = await checkCard(r);
    setShared(await shareBlob(blob, "pulsar-verifica.png", `Ho verificato su Pulsar: «${r.claim}»`));
  };

  return (
    <article className={`verdict verdict--${tone}`} aria-live="polite">
      <p className="verdict-claim">
        <q>{r.claim}</q>
      </p>
      <div className="verdict-head">
        <span className={`verdict-mark st-${tone}`} aria-hidden />
        <div>
          <p className="verdict-kind">{VERDICT[r.verdict]?.short}</p>
          <h2 className="verdict-title">{r.headline}</h2>
        </div>
      </div>
      <p className="verdict-expl">{r.explanation}</p>

      {r.numbers_mismatch && (
        <p className="verdict-numbers">
          Numeri nella tua frase: <strong>{r.claim_numbers.join(", ")}</strong>. Nelle testate: <strong>{r.source_numbers.join(", ")}</strong>.
        </p>
      )}

      {r.story_id && (
        <div className="verdict-story">
          <p>La storia di riferimento</p>
          <Link to={`/storia/${r.story_id}`}>{r.story_title}</Link>
        </div>
      )}

      {r.matches?.length > 0 && (
        <details className="verdict-matches">
          <summary>Su cosa si basa il verdetto</summary>
          <ul>
            {r.matches.map((m, i) => (
              <li key={i}>
                <span className="vm-kind">{KIND[m.kind] || m.kind}</span>
                {m.status && m.kind === "fatto" && <StatusTag status={m.status} />}
                <span className="vm-text">{m.text}</span>
                {m.source_names.length > 0 && <span className="vm-src">{m.source_names.join(", ")}</span>}
              </li>
            ))}
          </ul>
        </details>
      )}

      <div className="verdict-actions">
        <button className="btn-line" onClick={share}>
          {shared === "downloaded" ? "Immagine scaricata" : shared === "shared" ? "Condivisa" : "Condividi il verdetto"}
        </button>
        <p className="verdict-method">
          Cercato tra {r.stories_searched} storie di oggi. Metodo: {r.method}.
        </p>
      </div>
    </article>
  );
}
