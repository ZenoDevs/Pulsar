#!/bin/bash

# Setup script per Pulsar
echo "🚀 Setting up Pulsar development environment..."

# Controlla se siamo nella directory corretta
if [ ! -f "package.json" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Run this script from the Pulsar project root directory"
    exit 1
fi

# Crea virtual environment se non esiste
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Attiva virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Installa dipendenze Python
echo "📚 Installing Python dependencies..."
pip install -r backend/requirements.txt

# Vai nella directory frontend e installa dipendenze Node
echo "📚 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Quick start commands:"
echo "  • Start backend: Cmd+Shift+P → 'Tasks: Run Task' → 'Start Backend Server'"
echo "  • Start frontend: Cmd+Shift+P → 'Tasks: Run Task' → 'Start Frontend'"
echo "  • Start both: Cmd+Shift+P → 'Tasks: Run Task' → 'Start Full Application'"
echo ""
echo "🔗 URLs after starting:"
echo "  • Backend API: http://127.0.0.1:8000"
echo "  • Frontend: http://localhost:5173"
echo "  • API Docs: http://127.0.0.1:8000/docs"