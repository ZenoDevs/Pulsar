const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function get(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error(detail.detail || `Errore ${r.status}`);
  }
  return r.json();
}

async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`Errore ${r.status}`);
  return r.json();
}

export const api = {
  edition: (demo) => get(`/api/edition${demo ? "?demo=1" : ""}`),
  story: (id) => get(`/api/story/${id}`),
  sources: (demo) => get(`/api/sources${demo ? "?demo=1" : ""}`),
  refresh: () => post("/api/edition/refresh"),
  job: (id) => get(`/api/jobs/${id}`),
  search: (query) => post("/api/search", { query }),
  searchStatus: (id) => get(`/api/search/status/${id}`),
};

/** Esegue un polling finché il job non termina. */
export function poll(fn, onUpdate, interval = 1200) {
  let stopped = false;
  const tick = async () => {
    if (stopped) return;
    try {
      const s = await fn();
      onUpdate(s);
      if (s.status === "completed" || s.status === "failed") return;
    } catch (e) {
      onUpdate({ status: "failed", message: e.message });
      return;
    }
    setTimeout(tick, interval);
  };
  tick();
  return () => {
    stopped = true;
  };
}
