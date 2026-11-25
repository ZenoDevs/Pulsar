# Pulsar

**Informazione verificabile.** Pulsar legge le testate italiane di tutto lo spettro, raggruppa gli articoli per fatto e per ogni storia mostra:

- **cosa sappiamo**: ogni affermazione verificabile con il suo stato (*confermato*, *riportato*, *contestato*, *non verificato*) e le testate che la sostengono;
- **dove non concordano**: le versioni incompatibili, fianco a fianco;
- **come la raccontano**: le cornici narrative, ordinate da sinistra a destra;
- **opinioni e interpretazioni**: separate dai fatti, con chi le sostiene;
- **cosa manca, e a chi**: gli elementi che alcune testate omettono;
- **parole cariche**: termini di parte con un'alternativa neutra;
- **punti ciechi**: storie raccontate da una parte sola dello spettro;
- **chi l'ha detto e quando**: cronologia, con le riprese d'agenzia segnalate.

Il principio di design: **il colore indica solo la certezza, mai la politica.** Lo spettro è un asse in inchiostro neutro; verde, ocra, magenta e viola sono riservati agli stati dei fatti.

## L'esperienza

- **Prima apertura**: scegli gli argomenti che segui, dal catalogo o scritti con parole tue ("politica estera dell'Italia", "Formula 1").
- **Prima apertura del giorno**: il briefing a schermo intero, una storia per schermata, solo sui tuoi argomenti. Scorri in verticale per cambiare storia, di lato per vedere come l'ha titolata ogni testata.
- **La rivista**: storia di copertina, un binario per ogni argomento, la giornata, il gioco "Di chi è questo titolo?", i punti ciechi.
- **La storia**: una scena che si trasforma mentre scorri (chi ne parla, cosa è accertato, dove si dividono, come la raccontano), poi il dossier completo con le citazioni verificate e la cronologia dei cambi di stato.
- **Pulsar impara**: le sezioni che apri e i "di più / meno" affinano l'ordine. Il profilo resta nel browser; il server lo riceve a ogni apertura e non lo salva.

## L'aggregatore

`python -m app.aggregator.worker --every 20` (oppure `PULSAR_SCHEDULE_MINUTES=20` per farlo girare dentro l'API). Ogni giro:

1. **Fetch**: GET condizionali (ETag/Last-Modified), retry con backoff, circuit breaker per feed salvato su DB. Una testata rotta va in pausa da sola e non rallenta il giro.
2. **Normalizza**: URL canonici, deduplica per URL e per titolo, scarto delle rubriche.
3. **Arricchisci**: testo completo, bias del testo, embedding (con cache).
4. **Aggancia**: gli articoli nuovi entrano nella storia aperta più simile (ID stabili, finestra di 72 ore); il resto forma storie nuove.
5. **Verifica**: il dossier viene rigenerato solo se cambiano le testate o arrivano almeno due articoli. I cambi di stato dei fatti finiscono nella cronologia della storia.
6. **Pubblica**: nuova edizione. Se il giro fallisce, resta online quella precedente.

Ogni giro è registrato con tempi per fase, conteggi ed errori: `GET /api/status`.

## Perché ci si può fidare (e dove no)

1. **Si contano le voci, non gli articoli.** Testate dello stesso editore contano come una voce sola (es. Il Giornale, Libero e Il Tempo fanno capo agli Angelucci). Un testo che riprende quasi alla lettera un lancio d'agenzia conta come l'agenzia: lo misuriamo con sovrapposizione di 5-grammi, senza AI (`backend/app/analysis/independence.py`).
2. **Il modello lavora solo sugli articoli.** Il dossier è generato da un LLM a partire dai soli testi della storia, con citazioni numerate; le citazioni inesistenti vengono scartate.
3. **Ogni fatto porta citazioni letterali.** Il modello deve copiare una frase da ogni articolo che cita; Pulsar la cerca nel testo. Una citazione che non si trova (il segno più affidabile di un'allucinazione) esclude quella fonte, e un fatto senza citazioni valide diventa "non verificato" (`backend/app/analysis/grounding.py`).
4. **Le regole correggono il modello, mai il contrario.** Se il modello dice "confermato" ma ci sono meno di due voci indipendenti, lo stato scende a "riportato" e l'interfaccia spiega perché. Nessuna regola può alzare uno stato (`backend/app/analysis/dossier.py`).
5. **Ogni dossier è riproducibile**: versione del prompt, modello e hash degli articoli in ingresso sono salvati con il dossier.
6. **Limiti dichiarati.** L'orientamento delle testate è una stima editoriale di partenza, contestabile, e l'asse sinistra-destra semplifica. Gli assetti proprietari sono aggiornati a novembre 2026: quelli verificati hanno un link alla fonte, gli altri sono marcati "da verificare" (`backend/app/sources.py`).

## Avvio rapido

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env        # aggiungi almeno una chiave
uvicorn app.main:app --reload  # http://127.0.0.1:8000/docs

# Frontend
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

Senza edizioni nel database, la prima pagina mostra un'**edizione dimostrativa** con testate e fatti inventati (dichiarati come tali). Per generare la prima edizione reale:

```bash
cd backend
python -m app.cli check-feeds   # controlla che i feed RSS rispondano, correggi quelli rotti in app/sources.py
python -m app.cli edition       # legge i feed, raggruppa, genera i dossier
```

oppure il pulsante *Aggiorna l'edizione* in prima pagina (`POST /api/edition/refresh`). Conviene schedularlo ogni 1-2 ore.

### Variabili d'ambiente

| Variabile | A cosa serve |
|---|---|
| `ANTHROPIC_API_KEY` | Dossier e classificazioni con Claude (consigliato) |
| `OPENAI_API_KEY` | In alternativa per i dossier; unico provider per gli embedding |
| `PULSAR_LLM_PROVIDER` | Forza `anthropic` o `openai` |
| `PULSAR_MODEL_DEEP` / `PULSAR_MODEL_FAST` | Modelli per dossier / per-articolo |
| `DATABASE_URL` | Postgres (Supabase) o SQLite (default `sqlite:///./cache.db`) |
| `PULSAR_DEMO` | `auto` (default: demo finché non c'è un'edizione), `1` sempre demo, `0` mai |
| `PULSAR_TFIDF_THRESHOLD` | Soglia del clustering senza embedding (default 0.88) |
| `VITE_API_URL` | URL del backend per il frontend |

Senza nessuna chiave Pulsar funziona lo stesso: clustering TF-IDF, bias dalla testata, indipendenza, spettro, punti ciechi e cronologia. Mancano solo i dossier.

## Struttura

```
backend/app/
  sources.py            registro testate: orientamento, editore, feed
  ingest/rss.py         feed RSS + estrazione testo (trafilatura)
  scrapers/             ricerca per argomento sugli archivi (ANSA, Giornale, Repubblica)
  clustering.py         HAC su embedding o TF-IDF + fusione cluster via LLM
  analysis/
    independence.py     riprese d'agenzia e voci indipendenti
    dossier.py          fatti, interpretazioni, divergenze… + regole
    metrics.py          spettro, punti ciechi, cronologia, solidità
  pipeline.py           articoli -> storie
  edition.py            prima pagina
  demo.py               edizione dimostrativa (dati inventati)
  main.py               API
frontend/src/
  pages/                Prima pagina, Storia (dossier), Ricerca, Fonti e metodo
  components/           Impronta dei fatti, Spettro, Testata
```

## Test

```bash
cd backend && python -m pytest -q
```

## Prossimi passi

- Verificare i feed RSS al primo avvio (non raggiungibili dall'ambiente in cui è stato scritto questo codice).
- Completare la verifica degli assetti proprietari marcati "da verificare".
- Storico di una storia nel tempo: come cambia lo stato di un fatto da "riportato" a "confermato".
- Segnalazioni dei lettori su fatti e stati, con revisione pubblica.
