# INFLASI

Sistem Pemantauan Inflasi Pangan Berbasis AI — Membaca sinyal dini tekanan harga, menjelaskan penyebab awal, dan memprioritaskan wilayah/komoditas yang perlu diintervensi.

## Tech Stack

- **Frontend:** Next.js 14 (TypeScript, Tailwind CSS, Recharts)
- **Backend API:** Next.js API Routes + Python FastAPI (analytics)
- **Database:** PostgreSQL (Prisma ORM)
- **AI:** Claude API + Semantic Query Layer

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL database

### Setup

```bash
# Install dependencies
npm install

# Setup environment
cp .env.example .env.local
# Edit .env.local with your database URL

# Generate Prisma client
npx prisma generate

# Run migrations
npx prisma db push

# Seed dimension tables
npx prisma db seed

# Start development server
npm run dev
```

### Python Analytics Service

```bash
cd analytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Project Structure

```
├── src/
│   ├── app/
│   │   ├── (dashboard)/     # Dashboard pages (Overview, Komoditas, Wilayah, Alerts, AI)
│   │   └── api/             # Next.js API routes
│   ├── components/          # React components
│   ├── lib/                 # Utilities, DB client, types, constants
│   └── hooks/               # React Query hooks
├── analytics/               # Python FastAPI analytics service
│   └── app/
│       ├── api/             # Analytics API endpoints
│       ├── etl/             # Data pipelines (PIHPS BI, BPS, etc.)
│       └── services/        # Analytics logic (pricing, alerts, risk scoring)
├── prisma/                  # Database schema and seed
└── docs/                    # MVP Blueprint and documentation
```
