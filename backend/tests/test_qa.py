"""Verifica di affermazioni, domande sulle storie, storie seguite, limiti."""

import pytest
from fastapi.testclient import TestClient

from app.analysis.qa import numbers_in
from app.main import app

c = TestClient(app)


def check(claim):
    r = c.post("/api/check", json={"claim": claim, "demo": True})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize(
    "claim,verdict",
    [
        ("La Camera ha approvato la missione navale con 312 voti", "confermato"),
        ("La Camera ha approvato la missione con 250 voti favorevoli", "contraddetto"),
        ("L'Italia avrà il comando della missione navale a Corvara", "non_verificato"),
        ("Il ponte è crollato per colpa dei tagli della giunta regionale", "opinione"),
        ("Sono morte tre persone nel crollo del ponte di Borgo Alto", "contestato"),
        ("Il governo ha abolito l'IMU sulla prima casa", "non_trovata"),
    ],
)
def test_check_verdicts(claim, verdict):
    r = check(claim)
    assert r["verdict"] == verdict, (claim, r["verdict"], r["explanation"])
    assert r["headline"] and r["explanation"]


def test_check_numbers_reported():
    r = check("La Camera ha approvato la missione con 250 voti favorevoli")
    assert r["numbers_mismatch"] and 312 in r["source_numbers"]


def test_numbers_in_words_and_digits():
    assert numbers_in("tre feriti e 2,1 milioni") >= {3, 2.1}
    assert 1 in numbers_in("una persona ferita")
    assert 1 not in numbers_in("una legge regionale")


def test_check_rejects_short():
    assert c.post("/api/check", json={"claim": "ciao", "demo": True}).status_code == 400


def test_ask_story_extractive_and_contested():
    c.get("/api/edition?demo=1")
    r = c.post("/api/story/demo-1/ask", json={"question": "Quanti feriti ci sono stati?"}).json()
    assert r["certainty"] == "contestato"
    sources = {x["source_name"] for x in r["citations"]}
    assert "Il Megafono" in sources and "Agenzia Lince" in sources


def test_ask_unknown_says_so():
    r = c.post("/api/story/demo-1/ask", json={"question": "Chi ha vinto il campionato di calcio?"}).json()
    assert r["citations"] == [] and r["certainty"] == "non_si_sa"


def test_followed_story_updates_since():
    r = c.post("/api/stories/updates", json={"follow": {"demo-1": None, "nope": None}, "demo": True}).json()
    by = {s["id"]: s for s in r["stories"]}
    assert len(by["demo-1"]["new_updates"]) == 5
    assert by["nope"]["gone"]
    latest = by["demo-1"]["latest_update_at"]
    r2 = c.post("/api/stories/updates", json={"follow": {"demo-1": latest}}).json()
    assert r2["stories"][0]["new_updates"] == []


def test_tts_without_key_is_404():
    assert c.post("/api/tts", json={"text": "ciao"}).status_code == 404


def test_rate_limit():
    from app import ratelimit

    ratelimit._hits.clear()
    codes = [c.post("/api/story/demo-1/ask", json={"question": "Quando è crollato?"}).status_code for _ in range(22)]
    assert codes.count(429) == 2
    ratelimit._hits.clear()
