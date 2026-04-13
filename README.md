# Finbooks — GST Billing SaaS

A full-stack Indian GST billing application with invoice generation, quotations, credit notes, and PDF export.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Vanilla HTML + Tailwind CSS |
| Backend | FastAPI (Python 3.11) |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase JWT |
| PDF | WeasyPrint + Jinja2 |

---

## Local Development

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in SUPABASE_URL and SUPABASE_KEY in .env

uvicorn app.main:app --reload --port 8001
```

API runs at `http://localhost:8001`  
Swagger docs at `http://localhost:8001/docs`

### 2. Frontend

Open any HTML file directly in a browser, or serve with:

```bash
cd frontend
npx serve .        # or: python -m http.server 3000
```

---

## Deployment

### Backend → Railway (recommended) or Render

1. Push to GitHub
2. Create new project on [Railway](https://railway.app) → Deploy from GitHub
3. Set environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `ALLOWED_ORIGINS` → your Vercel frontend URL (e.g. `https://finbooks.vercel.app`)
4. Railway auto-detects the `Procfile` and deploys

### Frontend → Vercel

1. Push to GitHub
2. Import repo on [Vercel](https://vercel.com)
3. Set **Root Directory** to `/` (uses `vercel.json` at root)
4. After backend is deployed, update `frontend/js/config.js`:
   ```js
   window.API_BASE_URL = 'https://your-backend.railway.app/api';
   ```
5. Redeploy

---

## Database Setup

Run the migration in your Supabase SQL editor:

```sql
-- Add description column to line items (if not already present)
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';
ALTER TABLE quotation_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';
```

Full schema is in `backend/schema.sql`.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/service key |
| `ALLOWED_ORIGINS` | Comma-separated allowed CORS origins (or `*`) |
