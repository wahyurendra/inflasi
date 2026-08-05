# Swagger / OpenAPI

API Gateway menerbitkan kontrak OpenAPI 3.1 yang sama untuk dokumentasi interaktif dan integrasi
client.

## Membuka dokumentasi

Jalankan service dari direktori `apps/api-gateway`:

```bash
uvicorn app.main:app --reload --port 8000
```

Kemudian buka:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

Semua endpoint aplikasi memiliki prefix `/api`, kecuali `/health` dan `/metrics`.

## Autentikasi Firebase

Endpoint yang menampilkan ikon gembok membutuhkan Firebase ID token. Klik **Authorize**, lalu
masukkan token JWT tanpa menulis prefix `Bearer`. Swagger UI akan menambahkan prefix tersebut.

Contoh request di luar Swagger UI:

```bash
curl http://localhost:8000/api/auth/me \
  -H 'Authorization: Bearer <FIREBASE_ID_TOKEN>'
```

Respons umum untuk endpoint terproteksi:

- `401`: token tidak ada, tidak valid, kedaluwarsa, atau user nonaktif.
- `403`: token valid, tetapi role user tidak diizinkan.
- `422`: path, query, atau request body tidak lolos validasi FastAPI/Pydantic.

Endpoint bertag `internal` tidak memakai autentikasi aplikasi dan hanya boleh diekspos melalui
jaringan internal/ClusterIP. Pengecualian untuk operasi tulis registrasi model:
`POST /api/internal/models` wajib menerima `X-Training-Token` yang sama dengan
Kubernetes Secret `inflasi-training-service-secret`.

## Menghasilkan kontrak statis

File [`openapi.json`](openapi.json) dapat dipakai oleh Postman, Insomnia, Swagger Editor, atau
OpenAPI Generator. Perbarui setelah route atau schema berubah:

```bash
python scripts/export_openapi.py
```

Validasi bahwa artifact masih sama dengan schema aplikasi:

```bash
python scripts/export_openapi.py --check
```

Contoh membuat TypeScript client dengan OpenAPI Generator:

```bash
npx @openapitools/openapi-generator-cli generate \
  -i docs/openapi.json \
  -g typescript-fetch \
  -o /tmp/inflasi-api-client
```
