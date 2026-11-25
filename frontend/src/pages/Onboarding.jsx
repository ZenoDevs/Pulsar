import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TopicPicker from "../components/TopicPicker";
import { loadProfile, saveProfile } from "../lib/profile";
import { STATUS } from "../lib/format";

export default function Onboarding() {
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [topics, setTopics] = useState(() => loadProfile().topics);

  const finish = (goBriefing) => {
    saveProfile({ ...loadProfile(), topics, onboarded: true });
    nav(goBriefing ? "/briefing" : "/");
  };

  return (
    <main className="onb" data-step={step}>
      <div className="onb-pulse" aria-hidden>
        <span />
        <span />
        <span />
      </div>

      {step === 0 && (
        <section className="onb-step onb-intro">
          <p className="onb-brand">Pulsar</p>
          <h1>
            Le notizie,
            <br />
            senza il rumore.
          </h1>
          <p className="onb-lede">
            Leggiamo tutte le testate, da sinistra a destra, e ti mostriamo cosa è confermato, cosa è solo detto e chi lo racconta come.
            Il resto lo decidi tu.
          </p>
          <button className="onb-cta" onClick={() => setStep(1)}>
            Scegli cosa seguire
          </button>
        </section>
      )}

      {step === 1 && (
        <section className="onb-step onb-topics">
          <h1>Cosa ti interessa davvero?</h1>
          <p className="onb-lede">Il tuo briefing partirà da qui. Pulsar impara mentre leggi: puoi cambiare idea quando vuoi.</p>
          <TopicPicker value={topics} onChange={setTopics} />
          <div className="onb-actions">
            <button className="onb-cta" onClick={() => setStep(2)} disabled={!topics.length}>
              {topics.length ? `Continua con ${topics.length} ${topics.length === 1 ? "argomento" : "argomenti"}` : "Scegli almeno un argomento"}
            </button>
            <button className="onb-skip" onClick={() => finish(false)}>
              Salta, mostrami tutto
            </button>
          </div>
        </section>
      )}

      {step === 2 && (
        <section className="onb-step onb-key">
          <h1>Ogni fatto ha un colore. Nessun colore ha un partito.</h1>
          <ul className="onb-legend">
            {["confermato", "riportato", "contestato", "non_verificato", "interpretazione"].map((s) => (
              <li key={s}>
                <b className={`st-${s}`} aria-hidden />
                <span>
                  <strong>{STATUS[s].label}</strong> {STATUS[s].hint}
                </span>
              </li>
            ))}
          </ul>
          <p className="onb-lede">Ogni mattina, la prima volta che apri Pulsar, trovi il briefing: poche storie, una per schermata, solo su quello che segui.</p>
          <button className="onb-cta" onClick={() => finish(true)}>
            Apri il briefing di oggi
          </button>
        </section>
      )}

      <ol className="onb-dots" aria-label="Avanzamento">
        {[0, 1, 2].map((i) => (
          <li key={i} className={i === step ? "is-on" : ""} aria-current={i === step ? "step" : undefined} />
        ))}
      </ol>
    </main>
  );
}
