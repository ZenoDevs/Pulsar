/* Schede da condividere (1080×1350, il formato verticale dei social).
   Disegnate nel browser con un canvas: nessun server, nessun tracciamento.

   La scheda di una storia mette affiancati i due titoli più distanti sullo
   spettro e, sotto, il fatto detto senza inquadramento. È l'immagine che
   spiega Pulsar da sola. */

import { STATUS_ORDER, VERDICT, toneOf } from "./format";

const W = 1080;
const H = 1350;
const DISPLAY = '"Bodoni Moda Variable", "Bodoni 72", Didot, Georgia, serif';
const SANS = '"Schibsted Grotesk Variable", "Helvetica Neue", Arial, sans-serif';
const STATUS_COLOR = {
  confermato: "#4cc08c",
  riportato: "#e8b43c",
  contestato: "#ff5f86",
  non_verificato: "#a7b0c0",
  interpretazione: "#a399ff",
  neutro: "#eef0ee",
};

async function fontsReady() {
  try {
    await Promise.all([
      document.fonts.load(`600 64px ${DISPLAY}`),
      document.fonts.load(`italic 500 48px ${DISPLAY}`),
      document.fonts.load(`600 28px ${SANS}`),
    ]);
  } catch {
    /* si disegna con i caratteri di riserva */
  }
}

function wrap(ctx, text, maxWidth, maxLines) {
  const words = (text || "").split(/\s+/);
  const lines = [];
  let line = "";
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
      if (lines.length === maxLines) break;
    } else line = test;
  }
  if (lines.length < maxLines && line) lines.push(line);
  if (lines.length === maxLines && words.join(" ") !== lines.join(" ")) {
    let last = lines[maxLines - 1];
    while (ctx.measureText(`${last}…`).width > maxWidth && last.length) last = last.slice(0, -1);
    lines[maxLines - 1] = `${last.trimEnd()}…`;
  }
  return lines;
}

function drawText(ctx, lines, x, y, lh) {
  lines.forEach((l, i) => ctx.fillText(l, x, y + i * lh));
  return y + lines.length * lh;
}

function background(ctx, section) {
  const [hi, lo] = toneOf(section);
  const g = ctx.createRadialGradient(W * 0.75, H * 0.95, 40, W * 0.75, H * 0.95, H);
  g.addColorStop(0, hi);
  g.addColorStop(0.75, lo);
  g.addColorStop(1, "#0b0f19");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = "rgba(255,255,255,0.10)";
  ctx.lineWidth = 2;
  for (let r = 160; r < 1400; r += 150) {
    ctx.beginPath();
    ctx.arc(W * 0.75, H * 0.95, r, Math.PI, 2 * Math.PI);
    ctx.stroke();
  }
}

function brand(ctx, label) {
  ctx.fillStyle = "#eef0ee";
  ctx.font = `600 52px ${DISPLAY}`;
  ctx.fillText("Pulsar", 80, 120);
  if (label) {
    ctx.font = `600 26px ${SANS}`;
    const w = ctx.measureText(label).width;
    ctx.strokeStyle = "rgba(255,255,255,0.7)";
    ctx.lineWidth = 2;
    roundRect(ctx, W - 80 - w - 40, 80, w + 40, 52, 26);
    ctx.stroke();
    ctx.fillText(label, W - 80 - w - 20, 116);
  }
}

function footer(ctx) {
  ctx.fillStyle = "rgba(238,240,238,0.7)";
  ctx.font = `500 24px ${SANS}`;
  ctx.fillText("Cosa è confermato, cosa è solo detto, chi lo racconta come.", 80, H - 70);
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function axis(ctx, x, y, w, orientation) {
  ctx.strokeStyle = "rgba(255,255,255,0.7)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + w, y);
  ctx.moveTo(x + w / 2, y - 8);
  ctx.lineTo(x + w / 2, y + 8);
  ctx.stroke();
  ctx.fillStyle = "#fff";
  ctx.beginPath();
  ctx.arc(x + ((orientation + 1) / 2) * w, y, 9, 0, 2 * Math.PI);
  ctx.fill();
}

function fingerprint(ctx, counts, x, y) {
  const cells = [...STATUS_ORDER.flatMap((s) => Array(counts?.[s] || 0).fill(s))];
  cells.forEach((s, i) => {
    ctx.fillStyle = STATUS_COLOR[s];
    ctx.fillRect(x + i * 30, y, 24, 36);
  });
  return x + cells.length * 30;
}

export async function storyCard(story) {
  await fontsReady();
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const ctx = c.getContext("2d");
  background(ctx, story.section);
  brand(ctx, story.section);

  const hl = story.headlines || [];
  const left = hl[0];
  const right = hl[hl.length - 1];
  let y = 230;

  ctx.fillStyle = "#eef0ee";
  ctx.font = `600 64px ${DISPLAY}`;
  y = drawText(ctx, ["Stesso fatto,", "due giornali."], 80, y, 70) + 30;

  const pair = hl.length >= 2 ? [left, right] : hl.slice(0, 1);
  for (const h of pair) {
    ctx.fillStyle = "rgba(255,255,255,0.08)";
    roundRect(ctx, 80, y, W - 160, 250, 14);
    ctx.fill();
    axis(ctx, 120, y + 50, 300, h.orientation);
    ctx.fillStyle = "#fff";
    ctx.font = `italic 500 42px ${DISPLAY}`;
    const lines = wrap(ctx, `«${h.title}»`, W - 240, 3);
    drawText(ctx, lines, 120, y + 115, 50);
    ctx.font = `650 26px ${SANS}`;
    ctx.fillText(h.source_name, 120, y + 225);
    y += 280;
  }

  ctx.fillStyle = "rgba(238,240,238,0.75)";
  ctx.font = `600 26px ${SANS}`;
  ctx.fillText("Detto senza inquadramento:", 80, y + 20);
  ctx.fillStyle = "#fff";
  ctx.font = `600 46px ${DISPLAY}`;
  y = drawText(ctx, wrap(ctx, story.title, W - 160, 3), 80, y + 80, 54);

  const end = fingerprint(ctx, story.metrics?.status_counts, 80, H - 170);
  ctx.fillStyle = "rgba(238,240,238,0.85)";
  ctx.font = `500 26px ${SANS}`;
  const ind = story.metrics?.independence;
  if (ind) ctx.fillText(`${ind.independent_voices} voci indipendenti`, end + 20, H - 142);
  footer(ctx);
  return new Promise((res) => c.toBlob(res, "image/png"));
}

export async function checkCard(result) {
  await fontsReady();
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const ctx = c.getContext("2d");
  background(ctx, null);
  brand(ctx, "Verifica");

  ctx.fillStyle = "rgba(238,240,238,0.75)";
  ctx.font = `600 28px ${SANS}`;
  ctx.fillText("Ho letto:", 80, 250);
  ctx.fillStyle = "#fff";
  ctx.font = `italic 500 54px ${DISPLAY}`;
  let y = drawText(ctx, wrap(ctx, `«${result.claim}»`, W - 160, 4), 80, 330, 64) + 40;

  const tone = VERDICT[result.verdict]?.tone || "neutro";
  ctx.fillStyle = STATUS_COLOR[tone];
  ctx.fillRect(80, y, 24, 120);
  ctx.fillStyle = "#fff";
  ctx.font = `600 72px ${DISPLAY}`;
  y = drawText(ctx, wrap(ctx, result.headline, W - 220, 2), 130, y + 64, 78) + 30;

  ctx.fillStyle = "rgba(238,240,238,0.9)";
  ctx.font = `400 32px ${SANS}`;
  drawText(ctx, wrap(ctx, result.explanation, W - 160, 7), 80, y + 30, 46);
  footer(ctx);
  return new Promise((res) => c.toBlob(res, "image/png"));
}

/** Condivide con il foglio nativo se c'è (telefono), altrimenti scarica. */
export async function shareBlob(blob, filename, text) {
  const file = new File([blob], filename, { type: "image/png" });
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], text });
      return "shared";
    } catch {
      /* annullato */
    }
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  return "downloaded";
}
