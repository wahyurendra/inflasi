# INFLASI — Deployment Runbook

Production target: **K3s** + **Rancher Fleet** (GitOps), **Longhorn** storage, **Traefik**
ingress. No Helm/operators — plain manifests under `infra/k8s/projects/`, deployed by the
Fleet `GitRepo` in `infra/k8s/fleet/gitrepo.yaml`. CI builds images to **GHCR** and bumps the
`image:` tag in each `deployment.yaml`; Fleet rolls the change.

## Services
| Bundle | Workload | Exposure |
|---|---|---|
| `inflasi-infra` | Postgres+TimescaleDB, Redis, MinIO (StatefulSets) | ClusterIP |
| `inflasi-api` | FastAPI api-gateway (+ Alembic init, ETL/analytics CronJobs) | ClusterIP `:8001` |
| `inflasi-ml` | ML gateway (forecast/anomaly/OCR/trust/SD) on A100 | ClusterIP `:8080` |
| `inflasi-web` | Next.js BFF | **Traefik Ingress** (`inflasi.th`) |
| `inflasi-monitoring` | Prometheus + Grafana | ClusterIP |

## 1. Prerequisites
- K3s cluster with Longhorn (`storageClassName: longhorn`) and Traefik (default).
- Rancher Continuous Delivery / Fleet installed.
- GHCR access for `ghcr.io/wahyurendra/inflasi-*` images.
- (Optional) A100 node with the **NVIDIA device plugin** + a `nvidia` RuntimeClass; label it
  `kubectl label node <gpu-node> accelerator=nvidia-a100`. Without it, remove the GPU bits from
  `inflasi-ml/deployment.yaml` to run ML CPU-only.
- Firebase project (Auth: enable **Google** + **Email/Password**).

## 2. Secrets (create manually in-cluster — never committed)
```bash
# GHCR pull + Fleet git credential
kubectl create secret docker-registry ghcr-secret -n default \
  --docker-server=ghcr.io --docker-username=<user> --docker-password=<PAT>
kubectl create secret generic github-repo-secret -n fleet-default \
  --type=kubernetes.io/basic-auth --from-literal=username=<user> --from-literal=password=<PAT>

# Data layer
kubectl create secret generic inflasi-pg-secret -n default \
  --from-literal=POSTGRES_USER=inflasi --from-literal=POSTGRES_PASSWORD=<pw> --from-literal=POSTGRES_DB=inflasi
kubectl create secret generic inflasi-minio-secret -n default \
  --from-literal=MINIO_ROOT_USER=inflasi --from-literal=MINIO_ROOT_PASSWORD=<pw>

# api-gateway (DB/Redis/keys) + Firebase Admin service account (mounted at /secrets/firebase-sa.json)
kubectl create secret generic inflasi-secret -n default \
  --from-literal=ANALYTICS_DATABASE_URL='postgresql+asyncpg://inflasi:<pw>@inflasi-pg:5432/inflasi' \
  --from-literal=REDIS_URL='redis://inflasi-redis:6379/0' \
  --from-literal=BPS_API_KEY='' --from-literal=EIA_API_KEY='' \
  --from-literal=OPENAI_API_KEY=''   # daily blog generator (blank → template fallback)
kubectl create secret generic inflasi-firebase-sa -n default \
  --from-file=firebase-sa.json=./firebase-service-account.json

# web (NextAuth removed; only AUTH not needed) + grafana
kubectl create secret generic inflasi-web-secret -n default --from-literal=AUTH_SECRET=unused
kubectl create secret generic inflasi-grafana-secret -n default --from-literal=admin-password=<pw>
```

## 3. Deploy (GitOps)
```bash
kubectl apply -f infra/k8s/fleet/gitrepo.yaml      # or create the GitRepo in Rancher CD
```
Fleet reconciles the bundles. Recommended first reconcile order is automatic, but `inflasi-infra`
should be Ready before `inflasi-api` (the Alembic init-container needs `inflasi-pg`). The init-
container runs `alembic upgrade head` (idempotent) on every roll.

## 4. Firebase (web)
Web is **pure Firebase client SDK**. The public web config is baked into the image at build time —
set these as CI repo secrets (used as `--build-arg` in `.github/workflows/cd.yaml`):
`NEXT_PUBLIC_FIREBASE_{API_KEY,AUTH_DOMAIN,PROJECT_ID,STORAGE_BUCKET,MESSAGING_SENDER_ID,APP_ID}`.
The api-gateway verifies the resulting ID tokens via `inflasi-firebase-sa`. Android will use the
same Firebase project.

## 5. Verify
```bash
kubectl get pods -n default                  # all Running; alembic init Completed; longhorn PVCs Bound
kubectl exec deploy/inflasi-web -- wget -qO- http://inflasi-api:8001/health
kubectl exec deploy/inflasi-api -- wget -qO- http://inflasi-ml:8080/health   # gpu:true|false
# Browse the Traefik host (inflasi.th / real domain): sign in (Google or email/pw),
# submit a price report -> validation pipeline scores it -> notification appears.
```
CronJobs: `kubectl get cronjobs` (ETL + analytics). Grafana: port-forward `inflasi-grafana:3000`.

## Local dev (no cluster)
```bash
docker compose up            # web :3000 -> api :8001 -> postgres/redis/minio
```
Set `apps/web/.env` Firebase vars + `apps/api-gateway/.env` `ANALYTICS_DATABASE_URL`/`REDIS_URL`.
