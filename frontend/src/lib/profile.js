/* Profilo del lettore: vive solo nel browser. Il server riceve una copia a
   ogni apertura per ordinare l'edizione e non la conserva. */

const KEY = "pulsar.profile.v1";

const empty = () => ({
  onboarded: false,
  topics: [], // [{id} | {label}] con weight
  seen: {}, // { "YYYY-MM-DD": [storyId] }
  more: [],
  less: [],
  sections: {}, // affinità apprese: { Esteri: 0.4 }
  briefingDoneOn: null,
  follow: {}, // { storyId: ISO dell'ultima volta che l'hai vista }
  reads: [], // ultime letture: { id, at, mean, section, title }
  streak: { count: 0, last: null },
  depth: "tutto",
});

export function todayKey() {
  return new Date().toLocaleDateString("sv-SE"); // YYYY-MM-DD locale
}

export function loadProfile() {
  try {
    return { ...empty(), ...JSON.parse(localStorage.getItem(KEY) || "{}") };
  } catch {
    return empty();
  }
}

export function saveProfile(p) {
  try {
    localStorage.setItem(KEY, JSON.stringify(p));
  } catch {
    /* modalità privata: il profilo vale solo per questa sessione */
  }
  return p;
}

export function updateProfile(fn) {
  return saveProfile(fn(loadProfile()));
}

export const isBriefingDue = (p) => p.onboarded && p.briefingDoneOn !== todayKey();

function yesterdayKey() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toLocaleDateString("sv-SE");
}

/** Briefing completato: conta i giorni di fila. */
export const markBriefingDone = () =>
  updateProfile((p) => {
    const today = todayKey();
    if (p.briefingDoneOn === today) return p;
    const streak = p.streak?.last === yesterdayKey() ? { count: (p.streak.count || 0) + 1, last: today } : { count: 1, last: today };
    return { ...p, briefingDoneOn: today, streak };
  });

/** Segnale implicito: hai aperto una storia. L'affinità per la sezione cresce
 *  piano e decade per le altre, così il profilo segue i gusti che cambiano. */
export function recordOpen(story) {
  return updateProfile((p) => {
    const day = todayKey();
    const seenToday = new Set(p.seen[day] || []);
    seenToday.add(story.id);
    const sections = Object.fromEntries(Object.entries(p.sections).map(([k, v]) => [k, +(v * 0.97).toFixed(3)]));
    if (story.section) sections[story.section] = Math.min(1, +((sections[story.section] || 0) + 0.08).toFixed(3));
    const read = { id: story.id, at: new Date().toISOString(), mean: story.metrics?.mean_orientation ?? null, section: story.section, title: story.title };
    const reads = [read, ...(p.reads || []).filter((r) => r.id !== story.id)].slice(0, 80);
    const follow = p.follow?.[story.id] !== undefined ? { ...p.follow, [story.id]: new Date().toISOString() } : p.follow;
    return { ...p, seen: { [day]: [...seenToday] }, sections, reads, follow };
  });
}

export function recordFeedback(storyId, kind) {
  return updateProfile((p) => {
    const more = new Set(p.more);
    const less = new Set(p.less);
    if (kind === "more") {
      more.add(storyId);
      less.delete(storyId);
    } else {
      less.add(storyId);
      more.delete(storyId);
    }
    return { ...p, more: [...more].slice(-100), less: [...less].slice(-100) };
  });
}

export function feedPayload(p, demo) {
  return {
    demo,
    topics: p.topics,
    seen: p.seen[todayKey()] || [],
    more: p.more,
    less: p.less,
    sections: p.sections,
  };
}

export function markSeen(storyId) {
  return updateProfile((p) => {
    const day = todayKey();
    const seenToday = new Set(p.seen[day] || []);
    seenToday.add(storyId);
    return { ...p, seen: { [day]: [...seenToday] } };
  });
}

export function toggleFollow(storyId) {
  return updateProfile((p) => {
    const follow = { ...(p.follow || {}) };
    if (follow[storyId] !== undefined) delete follow[storyId];
    else follow[storyId] = new Date().toISOString();
    return { ...p, follow };
  });
}

export const isFollowing = (p, id) => p.follow?.[id] !== undefined;

export const setDepth = (depth) => updateProfile((p) => ({ ...p, depth }));
