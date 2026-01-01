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
