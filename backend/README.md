# Pulsar Backend

Backend API per Pulsar - aggregatore di notizie con analisi del bias.

## Struttura del Progetto

```
backend/
├── src/pulsar/
│   ├── api/              # Endpoints REST (FastAPI routers)
│   │   └── v1/endpoints/ # Versioned endpoints (health, search, cluster, chat)
│   │
│   ├── core/             # Business logic
│   │   ├── clustering.py # Algoritmo di clustering articoli
│   │   ├── config.py     # Configurazione app (da config.yaml)
│   │   └── state.py      # Stato in-memory (cache clusters, jobs)
│   │
│   ├── db/               # Database layer
│   │   └── orm.py        # SQLAlchemy models e queries
│   │
│   ├── domain/           # Entità di dominio (dataclasses)
│   │   ├── articles.py   # Article model
│   │   ├── clusters.py   # Cluster model
│   │   └── jobs.py       # Job model
│   │
│   ├── infrastructure/   # Integrazioni esterne
│   │   ├── clients/      # API clients (OpenAI per bias/embeddings)
│   │   └── scrapers/     # News scrapers (ANSA, Repubblica, Il Giornale)
│   │
│   ├── jobs/             # Background jobs
│   │   └── search_job.py # Job di ricerca asincrona
│   │
│   ├── app.py            # FastAPI app factory
│   └── main.py           # Entrypoint
│
├── scripts/
│   └── run_dev.sh        # Script avvio sviluppo (Linux/Mac)
│
├── config.yaml           # Configurazione applicazione
└── requirements.txt      # Dipendenze Python
```

## Avvio

### Variabili d'ambiente

E' fornito un .env.example di esempio.

### File di configurazione

E' fornito un config.yaml compilabile.

### Con script (Linux/Mac)

```bash
cd backend
./scripts/run_dev.sh
```

Lo script crea automaticamente il venv, installa le dipendenze e avvia il server.

### Manuale (Windows/Linux/Mac)

```bash
cd backend

# Crea virtual environment
python -m venv .venv

# Attiva venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Avvia server
python -m uvicorn pulsar.main:app --reload --host 0.0.0.0 --port 8000 --app-dir src
```

