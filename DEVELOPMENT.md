# Pulsar Development Setup

## 🚀 Super Easy Setup

### One-time setup:
```bash
./setup.sh
```

### Daily Development:

#### Option 1: Using VS Code Tasks (Recommended)
1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Tasks: Run Task"
3. Choose:
   - **Start Full Application** - Starts both backend and frontend
   - **Start Backend Server** - Only backend
   - **Start Frontend** - Only frontend

#### Option 2: Manual Commands
```bash
# Backend
cd backend
source ../.venv/bin/activate
python -m uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm run dev
```

### 🔗 URLs
- **Frontend**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs

### 🛠️ VS Code Features Configured
- ✅ Python interpreter auto-detection
- ✅ PYTHONPATH automatically set
- ✅ Debug configurations ready
- ✅ One-click server start
- ✅ Integrated terminal with correct environment

### 📁 Project Structure
```
Pulsar/
├── .vscode/          # VS Code configurations
├── backend/          # FastAPI application
├── frontend/         # React + Vite application
├── .venv/           # Python virtual environment
└── setup.sh         # One-time setup script
```

### 🔧 Troubleshooting
If you encounter issues:
1. Run `./setup.sh` again
2. Check that `.venv` folder exists in project root
3. Verify VS Code is using the correct Python interpreter (bottom-left corner)