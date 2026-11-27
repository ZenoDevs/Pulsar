import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { clock, plural } from "../lib/format";
import { loadProfile } from "../lib/profile";
import { Fingerprint, StatusTag } from "./Instruments";

/** Le storie che segui, con quello che è cambiato dall'ultima volta. */
export default function Followed({ demo }) {
  const [items, setItems] = useState(null);

  useEffect(() => {
    const follow = loadProfile().follow || {};
    if (!Object.keys(follow).length) return;
    api
      .updates(follow, demo)
      .then((r) => setItems(r.stories.filter((s) => !s.gone)))
      .catch(() => setItems([]));
  }, [demo]);

  if (!items?.length) return null;
  const withNews = items.filter((s) => s.new_updates.length);

  return (
    <section className="followed" aria-labelledby="followed-h">
      <header className="rail-head">
        <p className="rail-kicker">{withNews.length ? `${plural(withNews.length, "storia è cambiata", "storie sono cambiate")} da quando le hai lette` : "Nessuna novità da quando le hai lette"}</p>
        <h2 id="followed-h" className="rail-title">
          Le storie che segui
        </h2>
      </header>
      <ul className="followed-list">
        {items.map((s) => (
          <li key={s.id} className={s.new_updates.length ? "has-news" : ""}>
            <Link to={`/storia/${s.id}`}>
              <div className="followed-top">
                {s.new_updates.length > 0 && <span className="followed-badge">{plural(s.new_updates.length, "novità", "novità")}</span>}
                <span className="followed-sec">{s.section}</span>
              </div>
              <h3>{s.title}</h3>
              {s.new_updates.length > 0 ? (
                <ul className="followed-news">
                  {s.new_updates
                    .slice(-3)
                    .reverse()
                    .map((u, i) => (
                      <li key={i}>
                        {u.kind === "cambio_stato" && u.to_status ? (
                          <span className="followed-change">
                            <StatusTag status={u.from_status} /> <span aria-hidden>›</span> <StatusTag status={u.to_status} />
                          </span>
                        ) : null}
                        <span>{u.kind === "cambio_stato" && u.fact_text ? `«${u.fact_text}»` : u.text}</span>
                        <time>{clock(u.at)}</time>
                      </li>
                    ))}
                </ul>
              ) : (
                <p className="followed-quiet">Niente di nuovo.</p>
              )}
              <Fingerprint counts={s.status_counts} />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
