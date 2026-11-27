/* Versione statica di Pulsar: stessa interfaccia di api.js, nessun server.
   Usa l'edizione demo esportata dal backend (src/static/demo.json).
   Per le frasi libere, verifica e domande usano la stessa logica del backend
   (app/analysis/qa.py) riscritta qui: TF-IDF su n-grammi di caratteri. */

import data from "../static/demo.json";

const STATUSES = ["confermato", "riportato", "contestato", "non_verificato"];
const delay = (v, ms = 250) => new Promise((r) => setTimeout(() => r(structuredClone(v)), ms));

// ------------------------------------------------------------------ testo
const fold = (t) => (t || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();

function ngrams(text) {
  const out = new Map();
  const words = fold(text).replace(/[’'`]/g, " ").replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter(Boolean);
  for (const w of words) {
    const p = ` ${w} `;
    for (let n = 3; n <= 5; n++) {
      if (p.length < n) continue;
      for (let i = 0; i + n <= p.length; i++) {
        const g = p.slice(i, i + n);
        out.set(g, (out.get(g) || 0) + 1);
      }
    }
  }
  return out;
}

/** Similarità coseno TF-IDF (tf sublineare, idf smussato), come scikit-learn. */
function similarities(query, texts) {
  const docs = [...texts, query].map(ngrams);
  const df = new Map();
  docs.forEach((d) => d.forEach((_, g) => df.set(g, (df.get(g) || 0) + 1)));
  const N = docs.length;
  const vec = (d) => {
    const v = new Map();
    let norm = 0;
    d.forEach((tf, g) => {
      const w = (1 + Math.log(tf)) * (Math.log((1 + N) / (1 + df.get(g))) + 1);
      v.set(g, w);
      norm += w * w;
    });
    norm = Math.sqrt(norm) || 1;
    v.forEach((w, g) => v.set(g, w / norm));
    return v;
  };
  const vs = docs.map(vec);
  const q = vs[vs.length - 1];
  return vs.slice(0, -1).map((v) => {
    let s = 0;
    q.forEach((w, g) => {
      const o = v.get(g);
      if (o) s += w * o;
    });
    return s;
  });
}

const NUM_WORDS = { due: 2, tre: 3, quattro: 4, cinque: 5, sei: 6, sette: 7, otto: 8, nove: 9, dieci: 10, venti: 20, trenta: 30, cento: 100, mille: 1000 };

function numbersIn(text) {
  const t = fold(text);
  const out = new Set();
  for (const m of t.matchAll(/\d+(?:[.,]\d+)?/g)) {
    const v = parseFloat(m[0].replace(/\./g, "").replace(",", "."));
    if (!Number.isNaN(v)) out.add(v);
  }
  for (const [w, v] of Object.entries(NUM_WORDS)) if (new RegExp(`\\b${w}\\b`).test(t)) out.add(v);
  if (/\b(un|uno|una)\s+(persona|ferit|mort|vittim|arrest)/.test(t)) out.add(1);
  return out;
}

const sourceName = (id) => data.sources.sources.find((s) => s.id === id)?.name || id;
const allStories = () => Object.values(data.stories);

// ------------------------------------------------------------------ verifica
const HEADLINES = {
  confermato: "Confermato da più voci indipendenti",
  riportato: "Riportato, ma da una sola fonte",
  contestato: "Le testate non concordano",
  non_verificato: "Circola, ma nessuno lo ha verificato",
  opinione: "È un'opinione, non un fatto",
  contraddetto: "Le testate dicono un'altra cosa",
  se_ne_parla: "Se ne parla, ma non in questi termini",
  non_trovata: "Nessuna testata lo riporta",
};
const lc = (t) => (t ? t[0].toLowerCase() + t.slice(1) : t);

function units(stories) {
  const u = [];
  for (const s of stories) {
    const d = s.dossier;
    if (d) {
      d.facts.forEach((f) =>
        u.push({ kind: "fatto", text: f.text, match: [f.text, f.note || "", ...f.evidence.filter((e) => e.verified).map((e) => e.quote)].join(" "), status: f.status, ids: f.source_ids, s })
      );
      d.interpretations.forEach((i) => u.push({ kind: "interpretazione", text: i.text, match: i.text, status: null, ids: i.source_ids, s }));
      d.divergences.forEach((dv) => dv.versions.forEach((v) => u.push({ kind: "versione", text: `${dv.topic}: ${v.account}`, match: `${dv.topic}: ${v.account}`, status: "contestato", ids: v.source_ids, s })));
    }
    s.articles.forEach((a) => u.push({ kind: "titolo", text: a.title, match: a.title, status: null, ids: [a.source_id], s }));
  }
  return u;
}

function checkClaim(claim) {
  const stories = allStories();
  claim = claim.replace(/\s+/g, " ").trim().slice(0, 500);
  const base = { claim, verdict: "non_trovata", headline: HEADLINES.non_trovata, explanation: "", matches: [], claim_numbers: [], source_numbers: [], numbers_mismatch: false, method: "confronto testuale", stories_searched: stories.length };
  const us = units(stories);
  const sims = similarities(claim, us.map((u) => u.match));
  const order = sims.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]).map((x) => x[1]);
  const byStory = {};
  order.slice(0, 60).forEach((i) => (byStory[us[i].s.id] = [...(byStory[us[i].s.id] || []), sims[i]]));
  const sid = Object.keys(byStory).sort((a, b) => sum3(byStory[b]) - sum3(byStory[a]))[0];
  const story = data.stories[sid];
  const matches = order
    .filter((i) => us[i].s.id === sid)
    .slice(0, 6)
    .filter((i) => sims[i] >= 0.24 * 0.8)
    .map((i) => ({ kind: us[i].kind, text: us[i].text, status: us[i].status, source_ids: us[i].ids, source_names: us[i].ids.map(sourceName), similarity: +sims[i].toFixed(3), story_id: sid, story_title: story.title }));
  const bestFact = matches.find((m) => m.kind === "fatto");
  const bestInterp = matches.find((m) => m.kind === "interpretazione");
  const best = matches[0];
  const r = { ...base, cn: numbersIn(claim) };

  if (!best || best.similarity < 0.24) {
    r.explanation = `Abbiamo cercato tra ${stories.length} storie di oggi e nessuna testata riporta questa notizia. Non significa che sia falsa: può essere troppo recente, locale, o non vera. Diffida di chi non cita una fonte.`;
    return finish(r, null);
  }
  Object.assign(r, { story_id: sid, story_title: story.title, matches });
  if (bestInterp && bestInterp.similarity >= 0.42 && (!bestFact || bestInterp.similarity > bestFact.similarity + 0.05)) {
    r.verdict = "opinione";
    r.explanation = `Corrisponde a una lettura dei fatti sostenuta da ${bestInterp.source_names.join(", ") || "alcune testate"}, non a un fatto accertato. Altre testate la raccontano diversamente.`;
  } else if (bestFact && (bestFact.similarity >= 0.42 || (bestFact.similarity >= 0.33 && bestFact.similarity >= best.similarity - 0.06))) {
    r.verdict = bestFact.status || "non_verificato";
    const who = bestFact.source_names.join(", ");
    r.explanation = {
      confermato: `Lo riportano in modo concorde voci indipendenti: ${who}.`,
      riportato: `Lo riporta ${who}, ma non ci sono conferme indipendenti. Potrebbe cambiare.`,
      contestato: "Le testate danno versioni incompatibili su questo punto.",
      non_verificato: `Lo scrive ${who} citando fonti anonime o indiscrezioni. Nessuno lo ha verificato.`,
    }[r.verdict];
  } else {
    r.verdict = "se_ne_parla";
    r.explanation = `La storia è questa: «${story.title}». Ma nessun fatto accertato corrisponde esattamente a quello che hai scritto.`;
  }

  const div = touchedDivergence(claim, story, r.cn);
  if (div && r.verdict === "non_verificato") {
    r.explanation += ` E su questo punto le testate si dividono: ${div.versions.slice(0, 2).map((v) => `per ${v.source_ids.map(sourceName).join(", ")}, ${lc(v.account)}`).join(" ")}`;
  } else if (div && (r.verdict === "se_ne_parla" || r.verdict === "riportato")) {
    r.verdict = "contestato";
    r.explanation = `Su questo punto (${div.topic.toLowerCase()}) le testate non concordano. ${div.versions.slice(0, 3).map((v) => `Per ${v.source_ids.map(sourceName).join(", ")}: ${lc(v.account)}`).join(" ")}`;
    return finish(r, story, true);
  }
  return finish(r, story);
}

const sum3 = (a) => [...a].sort((x, y) => y - x).slice(0, 3).reduce((s, v) => s + v, 0);

function touchedDivergence(claim, story, cn) {
  let best = null;
  let bestSim = 0;
  for (const dv of story.dossier?.divergences || []) {
    const texts = [dv.topic, ...dv.versions.map((v) => v.account)];
    let sim = similarities(claim, [texts.join(" ")])[0];
    const nums = new Set(texts.flatMap((t) => [...numbersIn(t)]));
    if ([...cn].some((n) => nums.has(n))) sim += 0.15;
    if (sim > bestSim) [best, bestSim] = [dv, sim];
  }
  return bestSim >= 0.22 ? best : null;
}

function finish(r, story, skipNumbers = false) {
  const cn = r.cn;
  delete r.cn;
  r.claim_numbers = [...cn].sort((a, b) => a - b);
  if (!skipNumbers && cn.size && r.story_id) {
    const texts = r.matches.filter((m) => m.kind !== "interpretazione").map((m) => m.text);
    const facts = story?.dossier?.facts || [];
    if (facts.length) {
      const fs = similarities(r.claim, facts.map((f) => f.text));
      facts.forEach((f, i) => fs[i] >= 0.15 && texts.push(f.text));
    }
    const sn = new Set(texts.flatMap((t) => [...numbersIn(t)]));
    r.source_numbers = [...sn].sort((a, b) => a - b);
    r.numbers_mismatch = sn.size > 0 && ![...cn].some((n) => sn.has(n));
    if (r.numbers_mismatch && ["confermato", "riportato", "se_ne_parla"].includes(r.verdict)) {
      const vague = r.verdict === "se_ne_parla";
      r.verdict = "contraddetto";
      const nums = `I numeri non tornano: tu scrivi ${r.claim_numbers.join(", ")}, le testate riportano ${r.source_numbers.slice(0, 6).join(", ")}.`;
      r.explanation = nums + (vague ? ` La notizia è questa: «${story.title}».` : ` ${r.explanation}`);
    }
  }
  r.headline = HEADLINES[r.verdict];
  return r;
}

// ------------------------------------------------------------------ domande
const QW = new Set("chi che cosa come quando dove perche quanti quante quanto quale quali ci sono stati state stato e ha hanno il lo la i gli le di a da in su per un una del della dei si sa sai dimmi mi".split(" "));
const core = (q) => fold(q).split(/[^a-z0-9]+/).filter((t) => t && !QW.has(t)).join(" ") || q;

function askStory(story, question) {
  const res = { question, answer: null, certainty: null, citations: [], method: "estrattivo", note: null };
  const seen = new Map();
  const pool = [];
  const arts = [...story.articles].sort((a, b) => Number(!!a.echo_of) - Number(!!b.echo_of));
  for (const a of arts) {
    for (const sent of (a.body || a.snippet || "").split(/(?<=[.!?])\s+|\n+/).map((x) => x.trim()).filter((x) => x.length >= 30 && x.length <= 400)) {
      const key = fold(sent).replace(/[^a-z0-9]/g, "").slice(0, 120);
      if (seen.has(key)) {
        const c = seen.get(key);
        if (c.source_name !== a.source_name && !c.also_in.includes(a.source_name)) c.also_in.push(a.source_name);
        continue;
      }
      const c = { text: sent, source_id: a.source_id, source_name: a.source_name, article_id: a.id, verified: true, also_in: [], fact_status: null };
      seen.set(key, c);
      pool.push(c);
    }
  }
  const sims = similarities(core(question), pool.map((c) => c.text));
  const order = sims.map((v, i) => [v, i]).filter((x) => x[0] >= 0.08).sort((a, b) => b[0] - a[0]).map((x) => x[1]);
  const facts = story.dossier?.facts || [];
  const ftexts = facts.map((f) => [f.text, ...f.evidence.filter((e) => e.verified).map((e) => e.quote)].join(" "));
  order.slice(0, 8).forEach((i) => {
    if (!facts.length) return;
    const fs = similarities(pool[i].text, ftexts);
    const j = fs.indexOf(Math.max(...fs));
    if (fs[j] >= 0.35) pool[i].fact_status = facts[j].status;
  });
  res.citations = order.slice(0, 5).map((i) => pool[i]);
  if (!res.citations.length) {
    res.certainty = "non_si_sa";
    res.note = "Gli articoli non contengono una risposta a questa domanda. Forse non si sa ancora: guarda «Cosa non sappiamo ancora».";
  } else {
    const st = res.citations.map((c) => c.fact_status).filter(Boolean);
    res.certainty = st.includes("contestato") ? "contestato" : st[0] || null;
  }
  return res;
}

// ------------------------------------------------------------------ feed
const kwHit = (text, kw) => {
  const k = fold(kw).trim();
  if (!k) return false;
  const esc = k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(k.length <= 3 ? `\\b${esc}\\b` : `\\b${esc}`).test(text);
};
const matchScore = (text, section, kws, secs) => {
  const hits = kws.filter((k) => kwHit(text, k)).length;
  let s = 1 - Math.exp(-0.6 * hits);
  if (section && secs.includes(section)) s = Math.min(1, s + 0.25);
  return s;
};

function personalize(profile) {
  const ed = data.edition;
  const pool = [...ed.stories, ...ed.blindspots.filter((b) => !ed.stories.some((s) => s.id === b.id))];
  const topics = (profile.topics || [])
    .map((t) => {
      const cat = data.topics.find((c) => c.id === t.id);
      if (cat) return { id: cat.id, label: cat.label, kws: cat.keywords, secs: cat.sections, w: t.weight || 1 };
      if (t.label) {
        const key = fold(t.label);
        const words = key.split(/[^a-z0-9]+/).filter((w) => w.length > 2).map((w) => (w.length > 5 ? w.slice(0, -1) : w));
        return { id: `custom:${key}`, label: t.label, kws: [key, ...words], secs: [], w: t.weight || 1 };
      }
      return null;
    })
    .filter(Boolean);
  const seen = new Set(profile.seen || []);
  const less = new Set(profile.less || []);
  const maxScore = Math.max(...pool.map((s) => s.score), 1);
  const rails = Object.fromEntries(topics.map((t) => [t.id, { id: t.id, label: t.label, stories: [] }]));
  const ranked = pool.map((s) => {
    const text = fold([s.title, s.summary || "", ...s.headlines.map((h) => h.title), ...s.key_facts.map((f) => f.text)].join(" "));
    let best = 0;
    let bestLabel = null;
    let total = 0;
    topics.forEach((t) => {
      const m = matchScore(text, s.section, t.kws, t.secs);
      if (m >= 0.45) rails[t.id].stories.push([m, s]);
      total += m * t.w;
      if (m * t.w > best) [best, bestLabel] = [m * t.w, t.label];
    });
    const imp = s.score / maxScore;
    let rank = 0.45 * Math.min(1, total) + 0.35 * imp + 0.1 + 0.1 * (profile.sections?.[s.section] || 0);
    if (seen.has(s.id)) rank *= 0.35;
    if (less.has(s.id)) rank *= 0.2;
    const reason = bestLabel && best >= 0.45 ? `Perché segui ${bestLabel}` : imp > 0.6 ? "Tra le più importanti di oggi" : null;
    return [rank, { ...s, reason }];
  });
  ranked.sort((a, b) => b[0] - a[0]);
  return {
    edition: { ...ed, stories: [] },
    for_you: ranked.map((x) => x[1]),
    rails: Object.values(rails).map((r) => ({ ...r, stories: r.stories.sort((a, b) => b[0] - a[0]).map(([, s]) => ({ ...s, reason: `Perché segui ${r.label}` })) })),
    blindspots: ed.blindspots,
  };
}

// ------------------------------------------------------------------ api
const unavailable = () => Promise.reject(new Error("Nella versione dimostrativa le edizioni non si aggiornano: servono il server e i feed delle testate."));
let lastSearch = null;

export const staticApi = {
  edition: () => delay(data.edition),
  story: (id) => (data.stories[id] ? delay(data.stories[id]) : Promise.reject(new Error("Storia non trovata"))),
  sources: () => delay(data.sources),
  topics: () => delay({ topics: data.topics.map(({ id, label, blurb }) => ({ id, label, blurb })) }),
  feed: (payload) => delay(personalize(payload || {})),
  refresh: unavailable,
  job: unavailable,
  status: unavailable,
  check: (claim) => {
    if ((claim || "").trim().length < 8) return Promise.reject(new Error("Scrivi una frase un po' più lunga: almeno qualche parola."));
    const pre = data.checks[claim.trim()];
    return delay(pre || checkClaim(claim), 450);
  },
  ask: (id, question) => {
    const pre = data.asks[id]?.[question];
    return delay(pre || askStory(data.stories[id], question), 350);
  },
  updates: (follow) =>
    delay({
      stories: Object.entries(follow || {})
        .map(([id, since]) => {
          const s = data.stories[id];
          if (!s) return { id, gone: true };
          const t = since ? new Date(since.endsWith("Z") ? since : `${since}Z`).getTime() : 0;
          const ups = s.updates.filter((u) => new Date(`${u.at}`.replace(" ", "T") + (/[zZ]|\+/.test(u.at) ? "" : "Z")).getTime() > t);
          return { id, title: s.title, section: s.section, status_counts: s.metrics?.status_counts || {}, new_updates: ups.slice(-5), latest_update_at: s.updates.at(-1)?.at || null };
        })
        .sort((a, b) => (b.new_updates?.length || 0) - (a.new_updates?.length || 0)),
    }),
  search: (query) => {
    const q = fold(query);
    lastSearch = data.edition.stories.filter((s) => fold([s.title, s.summary, ...s.headlines.map((h) => h.title)].join(" ")).includes(q.split(" ")[0]));
    return delay({ job_id: "static", status: "pending" });
  },
  searchStatus: () => delay({ status: "completed", stories: lastSearch || [] }),
};

export { STATUSES };
