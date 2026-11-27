/* Lettura ad alta voce del briefing.
   Prima prova la voce di ElevenLabs tramite il backend (se configurata),
   altrimenti usa la sintesi vocale del browser in italiano. */

import { postBlob } from "./api";

let useServer = import.meta.env.VITE_STATIC !== "1";
let current = null;

function browserSpeak(text) {
  return new Promise((resolve) => {
    const synth = window.speechSynthesis;
    if (!synth) return resolve();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "it-IT";
    const it = synth.getVoices().find((v) => v.lang?.startsWith("it"));
    if (it) u.voice = it;
    u.rate = 1.02;
    u.onend = resolve;
    u.onerror = resolve;
    current = { stop: () => synth.cancel() };
    synth.speak(u);
  });
}

async function serverSpeak(text) {
  const blob = await postBlob("/api/tts", { text });
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  current = { stop: () => audio.pause() };
  await new Promise((resolve) => {
    audio.onended = resolve;
    audio.onerror = resolve;
    audio.play().catch(resolve);
  });
  URL.revokeObjectURL(url);
}

export async function speak(text) {
  if (useServer) {
    try {
      return await serverSpeak(text);
    } catch {
      useServer = false; // niente chiave sul server: d'ora in poi voce del browser
    }
  }
  return browserSpeak(text);
}

export function stopSpeaking() {
  current?.stop();
  current = null;
  window.speechSynthesis?.cancel();
}

export const canSpeak = () => typeof window !== "undefined" && ("speechSynthesis" in window || useServer);

export function scriptFor(story) {
  const fact = story.key_facts?.find((f) => f.status === "confermato");
  const parts = [story.title + "."];
  if (fact) parts.push(`Confermato: ${fact.text}`);
  if (story.top_divergence) parts.push(`Le testate non concordano su: ${story.top_divergence.topic}.`);
  const ind = story.metrics?.independence;
  if (ind) parts.push(`Ne parlano ${ind.independent_voices} voci indipendenti.`);
  return parts.join(" ");
}
