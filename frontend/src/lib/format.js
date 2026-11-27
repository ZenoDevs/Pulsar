export const STATUS = {
  confermato: {
    label: "Confermato",
    many: "confermati",
    hint: "Lo riportano almeno due voci indipendenti, con versioni concordi.",
  },
  riportato: {
    label: "Riportato",
    many: "riportati",
    hint: "Lo dice una sola voce, o più testate che riprendono la stessa fonte.",
  },
  contestato: {
    label: "Contestato",
    many: "contestati",
    hint: "Le testate danno versioni incompatibili.",
  },
  non_verificato: {
    label: "Non verificato",
    many: "non verificati",
    hint: "Indiscrezioni, fonti anonime, affermazioni non verificabili.",
  },
  interpretazione: {
    label: "Interpretazione",
    many: "interpretazioni",
    hint: "Opinioni, previsioni, attribuzioni di colpa: non sono fatti.",
  },
};

export const STATUS_ORDER = ["confermato", "riportato", "contestato", "non_verificato"];

export const INTERP_KIND = {
  opinione: "Opinione",
  previsione: "Previsione",
  causa: "Spiegazione causale",
  giudizio: "Giudizio",
  attribuzione: "Attribuzione di colpa",
};

const rtf = new Intl.RelativeTimeFormat("it", { numeric: "auto" });

/** Le date dal backend sono UTC senza fuso: le marchiamo come tali. */
export function toDate(v) {
  if (!v) return null;
  const s = typeof v === "string" && !/[zZ]|[+-]\d\d:?\d\d$/.test(v) ? `${v}Z` : v;
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function ago(v) {
  const d = toDate(v);
  if (!d) return "";
  const mins = Math.round((d.getTime() - Date.now()) / 60000);
  if (Math.abs(mins) < 60) return rtf.format(mins, "minute");
  const hours = Math.round(mins / 60);
  if (Math.abs(hours) < 36) return rtf.format(hours, "hour");
  return rtf.format(Math.round(hours / 24), "day");
}

export function clock(v) {
  const d = toDate(v);
  if (!d) return "ora n.d.";
  const day = d.toLocaleDateString("it-IT", { day: "numeric", month: "short" });
  const time = d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
  return `${day}, ore ${time}`;
}

export function today() {
  return new Date().toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}

export function pct(x) {
  return x == null ? "n.d." : `${Math.round(x * 100)}%`;
}

export function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`;
}

/** Mappa source_id -> nome a partire dagli articoli o dallo spettro. */
export function sourceNames(story) {
  const map = {};
  (story?.articles || []).forEach((a) => (map[a.source_id] = a.source_name));
  (story?.metrics?.spectrum || []).forEach((p) => (map[p.source_id] = p.source_name));
  return map;
}

/** Tinta profonda per sezione: dà ritmo alla rivista senza toccare i colori
 *  degli stati (che restano riservati alla certezza dei fatti). */
export const SECTION_TONE = {
  Esteri: ["#1d3557", "#0c1a2e"],
  Politica: ["#3b2552", "#170f24"],
  Economia: ["#14443b", "#08201c"],
  Cronaca: ["#5a2229", "#1c0b0e"],
  Società: ["#3f3c18", "#1a1908"],
  Cultura: ["#4c1d35", "#1f0b16"],
  Scienza: ["#123f4c", "#071b21"],
  Sport: ["#2f3d14", "#131a07"],
};
export const toneOf = (section) => SECTION_TONE[section] || ["#232b3d", "#0e1320"];

/** Verdetti della verifica: stesso vocabolario degli stati, più tre casi. */
export const VERDICT = {
  confermato: { tone: "confermato", short: "Confermato" },
  riportato: { tone: "riportato", short: "Solo riportato" },
  contestato: { tone: "contestato", short: "Contestato" },
  non_verificato: { tone: "non_verificato", short: "Non verificato" },
  opinione: { tone: "interpretazione", short: "Opinione" },
  contraddetto: { tone: "contestato", short: "Le fonti dicono altro" },
  se_ne_parla: { tone: "neutro", short: "Se ne parla" },
  non_trovata: { tone: "neutro", short: "Non trovata" },
};
