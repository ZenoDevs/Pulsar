#!/bin/bash

#Run this from backend directory

# Check if we are in the correct directory
if [ ! -d "scripts" ]; then
    echo "❌ Error: Run this script from the backend directory"
    exit 1
fi

# Crea virtual environment se non esiste
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    sudo python3 -m venv .venv
fi

# Attiva virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Installa dipendenze Python
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Avvia il server di sviluppo
echo "🚀 Starting development server..."
python -m uvicorn pulsar.main:app --reload --host 0.0.0.0 --port 8000 --app-dir src
