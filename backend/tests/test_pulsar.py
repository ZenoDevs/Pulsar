from datetime import datetime, timedelta

import pytest

from app.analysis.dossier import apply_rules, parse_dossier
from app.analysis.independence import containment, detect_echoes, independent_voices, shingles
from app.analysis.metrics import detect_blindspot
from app.llm import extract_json
from app.schemas import Article, Fact
from app.sources import SOURCES, leaning_from_score


def art(sid, text, hours=0, title=None):
    src = SOURCES[sid]
    return Article(
        id=f"{sid}-{hours}-{hash(text) % 9999}",
        source_id=sid,
        source_name=src.name,
        bias=src.leaning,
        title=title or text[:40],
        snippet=text,
        body=text,
        published_at=datetime(2026, 11, 25, 12) - timedelta(hours=hours),
    )


LANCIO = (
    "Alle 6.40 di questa mattina e' crollata una campata del ponte sul fiume lungo la strada statale "
    "all'ingresso del paese. Una persona e' rimasta ferita in modo non grave ed e' stata portata in ospedale."
)


def test_leaning_bands():
    assert leaning_from_score(-0.6) == "left"
    assert leaning_from_score(0.1) == "center"
    assert leaning_from_score(0.3) == "right"
    assert leaning_from_score(None) == "unknown"


def test_registry_owner_groups_are_shared():
    # Giornale, Libero e Tempo hanno lo stesso editore: devono contare come una voce
    assert SOURCES["il_giornale"].owner_group == SOURCES["libero"].owner_group == SOURCES["il_tempo"].owner_group


def test_shingle_containment():
    a = shingles(LANCIO)
    assert containment(a, a) == 1.0
    assert containment(a, shingles("testo completamente diverso che non c'entra nulla con il resto")) == 0.0


def test_echo_detection_marks_copies_not_originals():
    original = art("ansa", LANCIO, hours=3)
    copy = art("corriere", LANCIO + " Sul posto la sindaca.", hours=2)
    own = art("la_repubblica", "Il crollo era stato segnalato da una relazione tecnica che chiedeva lavori urgenti sui piloni del ponte da anni.", hours=1)
    detect_echoes([original, copy, own])
    assert original.echo_of is None
    assert copy.echo_of == original.id
    assert own.echo_of is None
    assert independent_voices([original, copy, own]) == 2


def test_same_owner_counts_once():
    a = art("il_giornale", "Testo originale numero uno con parole sue e una ricostruzione autonoma dei fatti accaduti ieri.")
    b = art("libero", "Un altro testo, scritto in modo diverso, con dettagli propri e una diversa scelta delle fonti citate.")
    assert independent_voices([a, b]) == 1


def test_rules_downgrade_but_never_upgrade():
    a = art("il_giornale", "uno due tre quattro cinque sei sette otto nove dieci undici")
    b = art("libero", "alfa beta gamma delta epsilon zeta eta theta iota kappa lambda")
    f = apply_rules(Fact(id="F1", text="x", status="confermato"), [a, b], {})
    assert f.status == "riportato" and f.downgraded_from == "confermato"
    assert "stesso editore" in f.verification

    c = art("la_repubblica", "testo indipendente di repubblica con parole tutte sue per il fatto in questione oggi")
    g = apply_rules(Fact(id="F2", text="y", status="riportato"), [a, c], {})
    assert g.status == "riportato"  # due voci, ma il modello aveva detto riportato: resta tale


def test_parse_dossier_drops_invented_citations():
    arts = [art("ansa", LANCIO, 2), art("la_repubblica", "Altro testo indipendente sul crollo del ponte, con dettagli sulla relazione.", 1)]
    data = {
        "titolo_neutro": "Crolla un ponte",
        "sommario": "s",
        "fatti": [{"testo": "Crollo alle 6.40", "stato": "confermato", "fonti": [1, 2, 99]}],
        "divergenze": [{"tema": "feriti", "versioni": [{"racconto": "uno", "fonti": [1]}, {"racconto": "tre", "fonti": [42]}]}],
        "omissioni": [{"elemento": "e", "presente_in": [1], "assente_in": [2]}],
    }
    d = parse_dossier(data, arts, {a.id: a for a in arts})
    assert d.facts[0].source_ids == ["ansa", "la_repubblica"]
    assert d.facts[0].status == "confermato"
    assert d.divergences == []  # una versione senza fonti valide -> divergenza scartata
    assert d.omissions[0].absent_in == ["la_repubblica"]


def test_blindspot():
    left_only = [art("la_repubblica", "a b c"), art("manifesto", "d e f"), art("corriere", "g h i")]
    b = detect_blindspot(left_only)
    assert b is not None and b.side == "right"
    balanced = [art("la_repubblica", "a"), art("corriere", "b"), art("il_giornale", "c")]
    assert detect_blindspot(balanced) is None


@pytest.mark.parametrize("raw", ['{"a": 1}', '```json\n{"a": 1}\n```', 'Ecco: {"a": 1} fine'])
def test_extract_json(raw):
    assert extract_json(raw) == {"a": 1}


def test_api_demo_edition_and_story():
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    e = c.get("/api/edition?demo=1").json()
    assert e["demo"] is True and len(e["stories"]) >= 5
    assert any(s["metrics"]["blindspot"] for s in e["stories"])
    s = c.get(f"/api/story/{e['stories'][0]['id']}").json()
    assert s["dossier"]["facts"]
    assert "embedding" not in s["articles"][0]
    # La storia demo sul ponte: la relazione 2024 "confermata" da due testate dello stesso editore viene declassata
    ponte = c.get("/api/story/demo-1").json()
    f5 = next(f for f in ponte["dossier"]["facts"] if f["id"] == "F5")
    assert f5["status"] == "riportato" and f5["downgraded_from"] == "confermato"
