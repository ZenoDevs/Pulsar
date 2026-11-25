"""Test dell'aggregatore senza rete: i feed sono simulati."""

from datetime import datetime, timedelta
from email.utils import format_datetime

import pytest

from app.aggregator import feeds as feeds_mod
from app.aggregator.normalize import canonical_url, normalize_and_dedupe
from app.aggregator.tracker import fact_changes
from app.analysis.dossier import parse_dossier
from app.analysis.grounding import verify
from app.schemas import Article, Dossier, Fact
from app.sources import SourceInfo, register_sources

T1 = SourceInfo("t_agenzia", "Agenzia Test", "agenzia", 0.0, "Coop Test", "t-coop", "#", feeds=["https://feed.test/agenzia.xml"])
T2 = SourceInfo("t_sinistra", "Quotidiano Rosso", "quotidiano", -0.5, "Gruppo A", "t-a", "#", feeds=["https://feed.test/rosso.xml"])
T3 = SourceInfo("t_destra", "Quotidiano Blu", "quotidiano", 0.6, "Gruppo B", "t-b", "#", feeds=["https://feed.test/blu.xml"])
register_sources([T1, T2, T3])


def rss(items):
    body = "".join(
        f"<item><title>{t}</title><link>{l}</link><description>{d}</description>"
        f"<pubDate>{format_datetime(datetime.utcnow() - timedelta(hours=h))}</pubDate></item>"
        for t, l, d, h in items
    )
    return f'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>{body}</channel></rss>'.encode()


class Resp:
    def __init__(self, status=200, content=b"", headers=None):
        self.status_code, self.content, self.headers = status, content, headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture
def fake_web(monkeypatch):
    pages = {}

    def get(url, headers=None, timeout=None):
        r = pages.get(url)
        if r is None:
            raise feeds_mod.requests.ConnectionError("irraggiungibile")
        return r(headers or {}) if callable(r) else r

    monkeypatch.setattr(feeds_mod.requests, "get", get)
    monkeypatch.setattr(feeds_mod.time, "sleep", lambda s: None)
    return pages


def test_canonical_url_strips_tracking():
    assert canonical_url("http://www.Example.it/a/b/?utm_source=x&id=3#top") == "https://example.it/a/b?id=3"
    assert canonical_url("https://m.example.it/news/amp/") == "https://example.it/news"


def test_dedupe_same_piece_two_urls():
    a = Article(id="1", source_id="t_agenzia", source_name="A", bias="center", title="Crolla il ponte sul fiume Serra a Borgo Alto", url="https://x.it/p?utm_medium=rss")
    b = Article(id="2", source_id="t_agenzia", source_name="A", bias="center", title="Crolla il ponte sul fiume Serra a Borgo Alto!", url="https://x.it/p2", snippet="più ricco")
    c = Article(id="3", source_id="t_agenzia", source_name="A", bias="center", title="Oroscopo di oggi per tutti i segni", url="https://x.it/o")
    out, dropped = normalize_and_dedupe([a, b, c])
    assert len(out) == 1 and out[0].snippet == "più ricco"
    assert dropped == {"duplicato": 1, "rubrica di servizio": 1}


def test_conditional_get_and_breaker(fake_web):
    url = "https://feed.test/fragile.xml"
    src = SourceInfo("t_fragile", "Fragile", "online", 0, "X", "t-x", "#", feeds=[url])
    seen_headers = {}

    def ok(headers):
        seen_headers.update(headers)
        if headers.get("If-None-Match") == '"v1"':
            return Resp(304)
        return Resp(200, rss([("Un titolo abbastanza lungo per passare", "https://f.it/1", "testo", 1)]), {"ETag": '"v1"'})

    fake_web[url] = ok
    assert feeds_mod.fetch_one(src, url).status == "ok"
    assert feeds_mod.fetch_one(src, url).status == "not_modified"
    assert seen_headers.get("If-None-Match") == '"v1"'

    fake_web[url] = Resp(500)
    for _ in range(3):
        assert feeds_mod.fetch_one(src, url).status == "error"
    r = feeds_mod.fetch_one(src, url)
    assert r.status == "skipped" and "pausa" in r.error


def test_grounding_rejects_invented_quotes():
    a = Article(id="g1", source_id="t_agenzia", source_name="A", bias="center", title="t",
                body="Alle 6.40 è crollata una campata del ponte sul fiume Serra, lungo la statale 14.")
    assert verify("è crollata una campata del ponte sul fiume Serra", a)[0]
    assert not verify("il sindaco ha annunciato le dimissioni immediate", a)[0]

    b = Article(id="g2", source_id="t_sinistra", source_name="B", bias="left", title="t",
                body="Una relazione del 2024 chiedeva lavori urgenti sui piloni del ponte.")
    data = {"titolo_neutro": "x", "fatti": [{
        "testo": "Il ponte è crollato alle 6.40", "stato": "confermato", "fonti": [1, 2],
        "evidenze": [{"fonte": 1, "citazione": "Alle 6.40 è crollata una campata del ponte"},
                     {"fonte": 2, "citazione": "il ponte è crollato all'alba di stamattina"}],
    }]}
    d = parse_dossier(data, [a, b], {"g1": a, "g2": b})
    f = d.facts[0]
    assert f.source_ids == ["t_agenzia"]  # la fonte con citazione inventata viene tolta
    assert f.status == "riportato"  # e con una sola voce non è più confermato
    assert d.grounding == {"verified": 1, "total": 2}


def test_fact_changes_detects_status_change():
    old = Dossier(neutral_title="x", summary="", facts=[Fact(id="F1", text="La Procura di Valdora ha aperto un fascicolo", status="riportato")])
    new = Dossier(neutral_title="x", summary="", facts=[
        Fact(id="F1", text="La Procura di Valdora ha aperto un fascicolo sul crollo", status="confermato"),
        Fact(id="F2", text="Tre persone sono rimaste ferite", status="contestato"),
    ])
    ch = fact_changes(old, new)
    assert [c.kind for c in ch] == ["cambio_stato", "nuovo_fatto"]
    assert ch[0].from_status == "riportato" and ch[0].to_status == "confermato"


def test_worker_tracks_story_across_runs(fake_web):
    from app.aggregator.worker import run_once

    lancio = "Crollata una campata del ponte sul fiume Serra a Borgo Alto, statale chiusa e un ferito portato in ospedale"
    fake_web["https://feed.test/agenzia.xml"] = Resp(200, rss([("Crolla il ponte sul fiume Serra a Borgo Alto", "https://ag.it/1", lancio, 3)]))
    fake_web["https://feed.test/rosso.xml"] = Resp(200, rss([("Ponte sul Serra crollato a Borgo Alto: anni di incuria", "https://ro.it/1", "Il ponte sul fiume Serra a Borgo Alto è crollato, la relazione chiedeva lavori", 2)]))
    fake_web["https://feed.test/blu.xml"] = Resp(200, rss([]))

    e1 = run_once(sources=[T1, T2, T3], fetch_bodies=False)
    assert e1 is not None
    ponte = [s for s in e1.stories if "ponte" in s.title.lower()]
    assert len(ponte) == 1
    sid = ponte[0].id

    fake_web["https://feed.test/blu.xml"] = Resp(200, rss([("Ponte del Serra a Borgo Alto, colpa dei vincoli", "https://bl.it/1", "Il crollo del ponte sul fiume Serra a Borgo Alto: lavori bloccati dai vincoli", 1)]))
    e2 = run_once(sources=[T1, T2, T3], fetch_bodies=False)
    again = next(s for s in e2.stories if s.id == sid)
    assert again.stats.total_articles == 3  # stesso ID, articolo agganciato
    assert any(u.kind == "nuove_testate" for u in again.updates)
    assert e2.sources_ok == 3


def test_personalize_orders_by_topics():
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    r = c.post("/api/feed", json={"demo": True, "topics": [{"id": "lavoro", "weight": 1}]}).json()
    assert r["for_you"][0]["reason"].startswith("Perché segui")
    rail = next(x for x in r["rails"] if x["id"] == "lavoro")
    assert any("sciopero" in s["title"].lower() or "braccian" in s["title"].lower() for s in rail["stories"])

    custom = c.post("/api/feed", json={"demo": True, "topics": [{"label": "affitti brevi", "weight": 1}]}).json()
    assert "affitti" in custom["for_you"][0]["title"].lower()
