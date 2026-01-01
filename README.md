# CoAct AI

CoAct AI is a monorepo containing the Frontend and Backend for the CoAct AI coaching platform.

## Project Structure

```
/
├── inter-ai-frontend/     # React Frontend (Vite + TS)
├── inter-ai-backend/      # Python Backend (Flask/FastAPI + AI)
└── docker-compose.yml     # Container orchestration
```

## Services

### 1. Inter AI Frontend (`/inter-ai-frontend`)
- **Tech Stack**: React, Vite, TypeScript, Tailwind CSS
- **Port**: 3000 (Local), 80 (Docker)
- **Description**: The main user interface.

### 2. Inter AI Backend (`/inter-ai-backend`)
- **Tech Stack**: Python, Azure OpenAI
- **Port**: 8000
- **Description**: Handles API requests, session management, and AI interactions.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Running with Docker (Recommended)

To run the entire stack:

```bash
docker-compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

### Running Locally (Manual)

**Backend:**
```bash
cd inter-ai-backend
python -m venv .venv
# Activate venv (Windows: .venv\Scripts\activate, Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python app.py
```

**Frontend:**
```bash
cd inter-ai-frontend
npm install
npm run dev
```

## Deployment

### Configuration
- **Frontend**: Ensure `VITE_API_URL` environment variable points to your deployed backend URL.
- **Backend**: Requires `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` environment variables.
