# CoAct AI

This repository contains the source code for CoAct AI, structured as a monorepo with three main services.

## Project Structure

```
/
├── .github/workflows   # CI/CD pipelines
├── client/             # React Frontend (formerly inter-ai-frontend)
├── server/             # Node.js Backend (New orchestration layer)
├── ai-engine/          # Python AI Service (formerly inter-ai-backend)
└── docker-compose.yml  # Container orchestration
```

## Services

### 1. Client (`/client`)
- **Tech**: React, Vite, TypeScript
- **Port**: 3000
- **Description**: The user interface for the application.

### 2. Server (`/server`)
- **Tech**: Node.js, Express
- **Port**: 5000
- **Description**: The main application backend handling business logic and API orchestration.

### 3. AI Engine (`/ai-engine`)
- **Tech**: Python, Flask/FastAPI
- **Port**: 8000
- **Description**: Handles AI-specific tasks like RAG, Speech-to-Text, and Report Generation.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js (for local dev)
- Python 3.10+ (for local dev)

### Running with Docker

```bash
docker-compose up --build
```

### Running Locally

See individual README files in each directory for specific setup instructions.

## Deployment Guide (2026 Strategy)

This project uses a "Git-Integrated Hosting" strategy with a Monorepo structure.

### 1. GitHub Actions
A unified CI workflow is defined in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) that tests all three tiers (Client, Server, AI Engine) on every push.

### 2. Hosting (Render/Railway/Azure)
Connect your GitHub repo to your hosting provider of choice.

**Configuration for Node Server:**
- **Root Directory**: `server`
- **Build Command**: `npm install`
- **Start Command**: `node index.js`
- **Environment**: `NODE_ENV=production`, `PORT=5000`, `AI_ENGINE_URL=...`

**Configuration for AI Engine (Python):**
- **Root Directory**: `ai-engine`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py` (or uvicorn/gunicorn if updated)
- **Environment**: `PORT=8000`, `AZURE_...` keys.

**Configuration for Client:**
- Host as a Static Site (Vercel/Netlify/Render Static)
- **Root Directory**: `client`
- **Build Command**: `npm run build`
- **Publish Directory**: `dist`

