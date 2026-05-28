# Test Deploy — Step by Step

Tujuan: deploy pertama kali ke K3s untuk validasi arsitektur. Dua jalur tersedia:

- **Jalur A (cepat — `kubectl apply -k` langsung)** — bypass Fleet, pakai manifest lokal. Untuk
  smoke-test pertama. Tetap perlu image di GHCR.
- **Jalur B (penuh GitOps via Fleet)** — proses produksi sesungguhnya. Pakai setelah Jalur A lulus.

Asumsi: `KUBECONFIG=~/Downloads/kubeth-kubeconfig.yaml`, cluster K3s siap dengan Longhorn,
Traefik, dan (opsional) Fleet/Rancher CD. Jalankan dari root repo.

---

## 0 · Pre-flight

```bash
export KUBECONFIG=~/Downloads/kubeth-kubeconfig.yaml

# Akses cluster
kubectl cluster-info
kubectl get nodes -o wide

# Prasyarat
kubectl get storageclass | grep longhorn         # → longhorn (default) ada
kubectl get pods -n kube-system | grep traefik   # → Traefik berjalan
kubectl get ns | grep -E 'fleet|cattle'          # → fleet-system / fleet-default (jika pakai Jalur B)
kubectl get nodes -o json | jq '.items[].metadata.labels' | grep -i accelerator || echo "(no GPU node)"
```

Kalau tidak ada GPU node, skip `inflasi-ml` di Jalur A, atau pakai variant CPU-only (hapus blok
GPU di `deployment.yaml` — `runtimeClassName`, `nodeSelector`, `tolerations`, `nvidia.com/gpu`).

---

## 1 · Commit & push branch

Semua kerja masih di `monorepo-consolidation`, belum di-commit.

```bash
git status
git add -A && git commit -m "feat: monorepo consolidation + firebase + phases 1-7"
git push -u origin monorepo-consolidation
```

---

## 2 · Siapkan image di GHCR

CI/CD workflow ada di `.github/workflows/cd.yaml` (sekarang juga bisa di-trigger manual via
**workflow_dispatch**). Setelah branch ada di GitHub:

1. Di GitHub repo Settings → Secrets and variables → Actions, tambahkan **repo secrets**:
   - `NEXT_PUBLIC_FIREBASE_API_KEY`, `…AUTH_DOMAIN`, `…PROJECT_ID`, `…STORAGE_BUCKET`,
     `…MESSAGING_SENDER_ID`, `…APP_ID` — dari Firebase Console (Project settings → SDK setup → Web).
2. Actions → CD → **Run workflow** → branch `monorepo-consolidation`.
3. Workflow akan: build/push 3 image ke `ghcr.io/wahyurendra/inflasi-{web,api,ml}:<SHA>` dan
   **commit bump tag** ke `deployment.yaml` + `cronjobs.yaml` (di branch itu).

Verifikasi: `https://github.com/wahyurendra/inflasi/pkgs/container/inflasi-api` → tag baru muncul.

> **Tanpa CI** (mode lokal): `docker login ghcr.io`, lalu build/push manual:
> ```bash
> SHA=$(git rev-parse --short=12 HEAD)
> docker build -t ghcr.io/wahyurendra/inflasi-api:$SHA apps/api-gateway && docker push ghcr.io/wahyurendra/inflasi-api:$SHA
> docker build --build-arg NEXT_PUBLIC_FIREBASE_API_KEY=… …(dst) -t ghcr.io/wahyurendra/inflasi-web:$SHA apps/web && docker push ghcr.io/wahyurendra/inflasi-web:$SHA
> # update infra/k8s/projects/*/deployment.yaml `image:` tag manual ke $SHA
> ```

---

## 3 · Buat secrets di cluster (sekali, manual — tidak pernah di-commit)

```bash
# (a) GHCR image pull secret
kubectl create secret docker-registry ghcr-secret -n default \
  --docker-server=ghcr.io --docker-username=<gh-user> --docker-password=<GHCR_PAT>

# (b) Data layer
kubectl create secret generic inflasi-pg-secret -n default \
  --from-literal=POSTGRES_USER=inflasi --from-literal=POSTGRES_PASSWORD='<pw>' --from-literal=POSTGRES_DB=inflasi
kubectl create secret generic inflasi-minio-secret -n default \
  --from-literal=MINIO_ROOT_USER=inflasi --from-literal=MINIO_ROOT_PASSWORD='<pw>'

# (c) api-gateway env + Firebase service-account JSON (mounted ke /secrets/firebase-sa.json)
kubectl create secret generic inflasi-secret -n default \
  --from-literal=ANALYTICS_DATABASE_URL='postgresql+asyncpg://inflasi:<pw>@inflasi-pg:5432/inflasi' \
  --from-literal=REDIS_URL='redis://inflasi-redis:6379/0' \
  --from-literal=BPS_API_KEY='' --from-literal=EIA_API_KEY=''
kubectl create secret generic inflasi-firebase-sa -n default \
  --from-file=firebase-sa.json=./firebase-service-account.json   # download dari Firebase → Service accounts

# (d) Web + Grafana
kubectl create secret generic inflasi-web-secret    -n default --from-literal=AUTH_SECRET=unused
kubectl create secret generic inflasi-grafana-secret -n default --from-literal=admin-password='<pw>'

# Verifikasi
kubectl get secrets -n default | grep -E 'ghcr|inflasi'
```

Firebase Console (sekali): Authentication → Sign-in method → enable **Google** & **Email/Password**.
Authorized domains → tambahkan host web (mis. `inflasi.th` atau domain produksi).

---

## 4 · Deploy — Jalur A (cepat, langsung kubectl)

Urutan **WAJIB**: infra → api → web (→ ml → monitoring opsional).

```bash
# 1) Data layer (StatefulSets — tunggu Ready sebelum lanjut, ~1 menit)
kubectl apply -k infra/k8s/projects/inflasi-infra
kubectl wait --for=condition=Ready pod -l app=inflasi-pg    -n default --timeout=180s
kubectl wait --for=condition=Ready pod -l app=inflasi-redis -n default --timeout=180s
kubectl wait --for=condition=Ready pod -l app=inflasi-minio -n default --timeout=180s

# 2) api-gateway (init-container alembic upgrade head berjalan dulu)
kubectl apply -k infra/k8s/projects/inflasi-api
kubectl get pods -n default -l app=inflasi-api -w   # tunggu init "Completed" lalu container Running

# 3) web (Traefik Ingress + rate-limit middleware)
kubectl apply -k infra/k8s/projects/inflasi-web
kubectl get ingress -n default inflasi-web

# 4) (opsional, hanya jika GPU node ada) ml-gateway
kubectl apply -k infra/k8s/projects/inflasi-ml

# 5) (opsional) monitoring
kubectl apply -k infra/k8s/projects/inflasi-monitoring
```

---

## 4-alt · Deploy — Jalur B (Fleet GitOps end-to-end)

```bash
# Fleet harus bisa pull repo. Jika private, buat github-repo-secret dulu:
kubectl create secret generic github-repo-secret -n fleet-default \
  --type=kubernetes.io/basic-auth --from-literal=username=<gh-user> --from-literal=password=<GH_PAT>

# Arahkan GitRepo ke branch test:
sed -i.bak 's#branch: main#branch: monorepo-consolidation#' infra/k8s/fleet/gitrepo.yaml

# Daftarkan (sekali). Fleet akan reconcile semua bundle di infra/k8s/projects/.
kubectl apply -f infra/k8s/fleet/gitrepo.yaml

# Pantau
kubectl -n fleet-default get gitrepo inflasi
kubectl -n fleet-default get bundles | grep inflasi
```

---

## 5 · Verifikasi sehat (Jalur A atau B)

```bash
# Semua pod
kubectl get pods -n default -o wide

# Init Alembic sukses?
kubectl logs -n default deploy/inflasi-api -c migrate --tail=20

# Health endpoints (in-cluster)
kubectl exec -n default deploy/inflasi-web -- wget -qO- http://inflasi-api:8001/health
kubectl exec -n default deploy/inflasi-api -- wget -qO- http://inflasi-ml:8080/health  # jika ml di-deploy

# Database hidup, tabel ke-create?
kubectl exec -n default sts/inflasi-pg -- psql -U inflasi -d inflasi -c "\dt" | head -20

# Redis stream consumer group sudah dibuat oleh validation pipeline?
kubectl exec -n default sts/inflasi-redis -- redis-cli XINFO GROUPS stream:price_reports
```

---

## 6 · Smoke test FE

```bash
# Port-forward web kalau ingress belum siap publik
kubectl port-forward -n default svc/inflasi-web 3000:80

# Browser → http://localhost:3000
#   - Login dengan Google / Email-Password (akun di Firebase project yang sama)
#   - Buka beberapa halaman dashboard — pastikan ada data (tidak fallback ke "source: mock")
#   - /lapor → submit harga → cek notifikasi muncul (validation pipeline)
```

End-to-end check stream:
```bash
kubectl exec -n default sts/inflasi-redis -- redis-cli XLEN stream:price_reports
kubectl exec -n default sts/inflasi-redis -- redis-cli XLEN stream:validation_done
kubectl logs -n default deploy/inflasi-api --tail=50 | grep validation_pipeline
```

---

## 7 · Troubleshooting cepat

| Gejala | Cek |
|---|---|
| `ImagePullBackOff` | `ghcr-secret` belum dibuat / PAT salah; tag image tidak ada di GHCR |
| Init-container `Error` | `inflasi-pg` belum Ready; cek `inflasi-secret.ANALYTICS_DATABASE_URL` |
| api 401 di semua endpoint terautentikasi | Firebase service-account JSON salah / mount gagal — `kubectl describe pod` |
| Web prerender error `auth/invalid-api-key` | Build CI tidak menerima Firebase build-args; cek repo secrets |
| `inflasi-ml` `0/1 nodes` | Node GPU belum di-label `accelerator=nvidia-a100` / NVIDIA device plugin tidak ada |
| Longhorn PVC stuck `Pending` | StorageClass `longhorn` tidak ada / replica node insufficient |

---

## 8 · Rollback

```bash
# Jalur A
kubectl delete -k infra/k8s/projects/inflasi-web
kubectl delete -k infra/k8s/projects/inflasi-api
# infra terakhir karena ada PVC yang menyimpan data:
kubectl delete -k infra/k8s/projects/inflasi-infra
# (PVC tidak ikut terhapus by default; hapus manual jika perlu)
kubectl get pvc -n default | grep -E 'inflasi|ml-models'

# Jalur B
kubectl delete -f infra/k8s/fleet/gitrepo.yaml
```
