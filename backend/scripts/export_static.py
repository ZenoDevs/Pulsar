"""Esporta l'edizione demo in un JSON per la versione statica del frontend.

    cd backend && python -m scripts.export_static

La versione statica (npm run build:static) gira senza server: serve per
mostrare Pulsar in una pagina condivisibile. Verifica e domande sulle frasi
d'esempio usano i risultati veri del motore Python, salvati qui; le frasi
libere usano la stessa logica riscritta in JavaScript (src/lib/static.js).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///./export-static.db")
for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(k, None)

from app.analysis.qa import ask_story, check_claim  # noqa: E402
from app.main import get_edition, sources  # noqa: E402
from app.store import current_stories  # noqa: E402
from app.topics import CATALOG  # noqa: E402

EXAMPLES = [
    "Sono morte tre persone nel crollo del ponte",
    "La missione navale è stata approvata con 250 voti",
    "Il governo ha abolito l'IMU sulla prima casa",
    "La legge sugli affitti è un esproprio della proprietà privata",
    "L'Italia avrà il comando della missione navale a Corvara",
    "Sciopero dei bus: ha aderito l'80 per cento dei lavoratori",
    "Ionica ha raccolto 40 milioni per le batterie al sodio",
]


def suggestions(story):
    d = story.dossier
    out = []
    if d and d.divergences:
        t = d.divergences[0].topic.strip()
        out.append(t if t.endswith("?") else f"{t}?")
    return out + ["Cosa è confermato?", "Chi ha detto cosa?"]


def main(out_path):
    edition = get_edition(demo=True)
    stories = current_stories(True)
    data = {
        "edition": json.loads(edition.model_dump_json()),
        "stories": {s.id: json.loads(s.model_dump_json()) for s in stories},
        "topics": [{"id": t.id, "label": t.label, "blurb": t.blurb, "keywords": t.keywords, "sections": t.sections} for t in CATALOG],
        "sources": sources(demo=True),
        "checks": {c: json.loads(check_claim(c, stories).model_dump_json()) for c in EXAMPLES},
        "asks": {
            s.id: {q: json.loads(ask_story(s, q).model_dump_json()) for q in suggestions(s)} for s in stories
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    print(f"Scritto {out_path}: {len(stories)} storie, {len(EXAMPLES)} verifiche")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "static", "demo.json"))
