# Document Vault

A personal file vault: register, log in, upload PDFs/images, list, download via presigned URLs, and delete files.

## Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy 2, JWT, bcrypt |
| Frontend | React 18, Vite, TypeScript, axios |
| Database | PostgreSQL 16 |
| Storage | MinIO (S3-compatible) / AWS S3 |
| Rate limiting | Redis (10 uploads/min per user) |
| Tests | pytest, httpx, moto |
| CI | GitHub Actions |

## Prerequisites

- Docker Desktop
- Git

Optional for local dev without Docker:

- Python 3.12
- Node.js 20+

## Quick start (Docker)

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd document-storage
   ```

2. Copy environment file:

   ```bash
   cp .env.example .env
   ```

3. Start all services:

   ```bash
   docker compose up --build
   ```

4. Open the app:

   - **Frontend:** http://localhost:3000
   - **API docs:** http://localhost:8000/docs
   - **MinIO console:** http://localhost:9001 (`minioadmin` / `minioadmin`)

5. Demo flow:

   - Register a new account
   - Log in
   - Upload a PDF or image
   - Download from the dashboard
   - Delete the file

## Environment variables

| Variable | Description | Default (local) |
|----------|-------------|-----------------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://vault:vault@postgres:5432/vault` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `S3_ENDPOINT` | MinIO URL for API uploads/deletes (Docker internal) | `http://minio:9000` |
| `S3_PUBLIC_ENDPOINT` | MinIO URL in presigned download links (browser) | `http://localhost:9000` |
| `S3_BUCKET` | S3 bucket name | `documents` |
| `AWS_ACCESS_KEY_ID` | S3 access key | `minioadmin` |
| `AWS_SECRET_ACCESS_KEY` | S3 secret key | `minioadmin` |
| `JWT_SECRET` | JWT signing secret | **Change in production** |
| `JWT_EXPIRE_MINUTES` | Access token lifetime | `15` |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:3000` |

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Liveness check |
| POST | `/api/v1/auth/register` | No | Create account |
| POST | `/api/v1/auth/login` | No | Get JWT access token |
| GET | `/api/v1/files` | JWT | List your files |
| POST | `/api/v1/files/upload` | JWT | Upload file (max 50 MB) |
| GET | `/api/v1/files/{id}/download` | JWT | Presigned download URL |
| DELETE | `/api/v1/files/{id}` | JWT | Delete file |

## Running tests

From the repo root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest tests/ -v
```

Tests use SQLite in-memory, moto (S3 mock), and fakeredis by default. CI runs against Postgres and Redis service containers.

## Local development (without full Docker UI)

Start infra only:

```bash
docker compose up -d postgres redis minio minio-init
```

Backend:

```bash
cd backend
pip install -r requirements.txt
# Set DATABASE_URL=postgresql://vault:vault@localhost:5432/vault in .env
# Set S3_ENDPOINT=http://localhost:9000 and S3_PUBLIC_ENDPOINT=http://localhost:9000
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Vite dev server proxies `/api` to `http://localhost:8000`.

## Project structure

```
document-storage/
├── backend/           # FastAPI API + pytest
├── frontend/          # React UI + nginx
├── scripts/           # MinIO bucket init
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

## Production notes

- Set a strong `JWT_SECRET`
- Use real AWS S3 (leave `S3_ENDPOINT` empty, set IAM credentials)
- Restrict `CORS_ORIGINS` to your domain
- Presigned download URLs expire after 5 minutes
