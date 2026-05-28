# INFLASI

Sistem Pemantauan Inflasi Pangan Berbasis AI — membaca sinyal dini tekanan harga, menjelaskan
penyebab awal, dan memprioritaskan wilayah/komoditas yang perlu diintervensi.

Monorepo: a Next.js frontend, a consolidated FastAPI backend, an ML gateway, and K3s/Fleet infra.

## Architecture

```
apps/web          Next.js 14 BFF (Tailwind, Recharts, CopilotKit). Firebase auth (client SDK).
apps/api-gateway  FastAPI: prices/reports/alerts/intelligence/gamification/users, Alembic,
                  in-process validation pipeline (Redis Streams), ETL + analytics CronJobs.
ml/ml-gateway     FastAPI ML service (forecast/anomaly/OCR/trust/surplus-deficit) on 1×A100,
                  CPU-fallback. Stateless — callers pass the data series.
infra/k8s         Fleet-style kustomize per service (Traefik, Longhorn, GHCR). No Helm.
```

- **Auth:** Firebase (Google + Email/Password). Web uses the client SDK; the api-gateway verifies
  ID tokens via firebase-admin. Same Firebase project will back the Android app.
- **Data:** PostgreSQL + TimescaleDB, Redis (cache + Streams), MinIO (report photos). No Supabase.
- **AI:** Claude API (assistant) + the ML gateway (forecasting/anomaly).

## Tech Stack
Next.js 14 · FastAPI (Python 3.11/3.12) · PostgreSQL/TimescaleDB · Redis · MinIO · Firebase Auth ·
PyTorch/Prophet · K3s + Rancher Fleet + Traefik + Longhorn · Prometheus + Grafana.

## Local development
```bash
docker compose up        # web :3000 -> api :8001 -> postgres / redis / minio
```
Set `apps/web/.env` (`NEXT_PUBLIC_FIREBASE_*`, `NEXT_PUBLIC_API_URL`) and `apps/api-gateway/.env`
(`ANALYTICS_DATABASE_URL`, `REDIS_URL`). See each app's `.env.example`.

Run a single app:
```bash
npm --prefix apps/web run dev
cd apps/api-gateway && uvicorn app.main:app --reload --port 8001
```

## Deploy
Production bring-up (secrets, GitOps order, Firebase, GPU, verification): **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.
CI/CD: `.github/workflows/` builds & pushes GHCR images and bumps Fleet image tags.

## Docs
- [docs/MVP_BLUEPRINT.md](docs/MVP_BLUEPRINT.md) — product spec
- [INFLASI_ID_Production_Plan_Revised.md](INFLASI_ID_Production_Plan_Revised.md) — production plan
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — deployment runbook

## Repo layout
```
apps/{web,api-gateway}/   ml/ml-gateway/   workers/   infra/k8s/{projects,fleet}/   docs/
```
