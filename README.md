# Finbooks — GST Billing SaaS

> A full-stack Indian GST billing platform for SMEs, traders, and chartered accountants.

**Live Links**
- 🌐 Frontend: [https://finbooks-saas.vercel.app](https://finbooks-saas.vercel.app)
- ⚙️ Backend API: [https://finbooks-saas.onrender.com](https://finbooks-saas.onrender.com)
- 📖 API Docs: [https://finbooks-saas.onrender.com/docs](https://finbooks-saas.onrender.com/docs)
- 💾 GitHub: [https://github.com/varshithreddy39/finbooks-saas](https://github.com/varshithreddy39/finbooks-saas)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML + Tailwind CSS (17 pages) |
| Backend | FastAPI (Python 3.11) + Uvicorn |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase JWT with auto-refresh |
| PDF Generation | WeasyPrint + Jinja2 HTML templates |
| File Storage | Supabase Storage (logos, signatures) |
| Frontend Hosting | Vercel |
| Backend Hosting | Render (Docker) |

---

## Features

### Auth & Onboarding
- Signup with GSTIN, email, mobile — auto-creates company profile
- Login with JWT + refresh token (auto-renews on expiry)
- Password reset via email
- Account deletion with full data cascade
- Auth guards on every page

### Company Settings
- Company info, legal name, address, state/state code
- GSTIN locked after signup
- Bank details printed on invoices
- Logo upload with CropperJS (stored in Supabase Storage)
- Signature upload
- Invoice numbering (prefix, padding, starting number)
- Financial year settings with auto-reset
- Invoice display preferences

### Invoices
- GST-compliant tax invoices
- Auto CGST/SGST (intra-state) or IGST (inter-state)
- Per-line item description (size, spec, chemicals)
- HSN/SAC codes, quantity, unit, rate
- Bill To / Ship To with customer auto-fill
- Transport details, e-Way bill, reverse charge
- PDF generation (WeasyPrint)
- Edit, delete, view-only mode

### Quotations
- Full quotation creation
- Convert to Invoice in one click
- PDF export
- Status tracking (Open / Accepted / Expired)

### Credit Notes
- Issue against invoices
- GST-compliant PDF
- Status tracking (Issued / Pending)

### Master Data
- Clients — GSTIN, phone, email, address, state, CSV export
- Vendors — same fields, separate directory
- Products — SKU, HSN/SAC, GST rate, sales price, unit, stock

### Dashboard
- Revenue, invoices, GST collected, clients — stat cards
- Quick actions (New Invoice, Quotation, Credit Note, Add Client, Reports)
- Recent invoices table with customer avatars
- Company logo in top-right profile

### Reports
- Monthly GST summary (CGST/SGST/IGST breakdown)
- Revenue reports with CSV export

### Mobile Responsive
- Hamburger sidebar on mobile
- Bottom navigation bar (Home, Invoices, New, Clients, Settings)
- Responsive grids on all pages

### Security
- Every endpoint verifies `company_id` belongs to authenticated user
- No cross-tenant data leakage
- CORS restricted to Vercel frontend URL
- `.env` never committed

---

## Project Structure

```
finbooks-saas/
├── frontend/
│   ├── dashboard/
│   ├── invoice_list/
│   ├── create_invoice/
│   ├── quotations/
│   ├── create_quotation/
│   ├── credit_notes/
│   ├── create_credit_note/
│   ├── clients/
│   ├── vendors/
│   ├── products/
│   ├── company_setup/
│   ├── reports_settings/
│   ├── login_page/
│   ├── signup_page/
│   ├── landing/
│   └── js/
│       ├── api.js          # All API calls
│       ├── config.js       # Production API URL
│       └── constants.js    # Indian states & GST codes
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app entry
│   │   ├── schemas.py      # Pydantic models
│   │   ├── auth_utils.py   # JWT verification
│   │   ├── database.py     # Supabase client
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── company.py
│   │   │   ├── invoice.py
│   │   │   ├── quotation.py
│   │   │   ├── credit_note.py
│   │   │   └── masters.py
│   │   ├── services/
│   │   │   ├── invoice_service.py
│   │   │   ├── quotation_service.py
│   │   │   ├── credit_note_service.py
│   │   │   └── gst_engine.py
│   │   └── templates/
│   │       ├── invoices/gst_template.html
│   │       ├── quotations/quotation_template.html
│   │       └── credit_notes/credit_note_template.html
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── schema.sql
│   ├── migrate_add_description.sql
│   └── .env.example
├── vercel.json
├── DATABASE.md             # Database schema documentation
└── README.md
```

---

## Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in SUPABASE_URL and SUPABASE_KEY

DYLD_LIBRARY_PATH=/opt/homebrew/lib uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
python3 -m http.server 3000
# Open http://localhost:3000/landing/code.html
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (e.g. `https://finbooks-saas.vercel.app`) |

---

## Database Setup

Run in Supabase SQL Editor:

```sql
-- Full schema
-- See backend/schema.sql

-- Migration (add description to line items)
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';
ALTER TABLE quotation_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';
```

See [DATABASE.md](./DATABASE.md) for full table design.

---

## Deployment

### Frontend → Vercel
1. Import `finbooks-saas` repo on [vercel.com](https://vercel.com)
2. Framework: `Other`, Root: `/`, no build command
3. Deploy — uses `vercel.json` for routing

### Backend → Render
1. New Web Service on [render.com](https://render.com)
2. Root Directory: `backend`, Environment: `Docker`
3. Add env vars: `SUPABASE_URL`, `SUPABASE_KEY`, `ALLOWED_ORIGINS`
4. Health Check Path: `/`

### After deploying backend
Update `frontend/js/config.js`:
```js
window.API_BASE_URL = 'https://your-backend.onrender.com/api';
```
Then push — Vercel auto-redeploys.

---

## Supabase Storage Setup

Create two public buckets in Supabase Storage:
- `logos` — company logos
- `signatures` — authorised signatory images

Run in SQL Editor:
```sql
CREATE POLICY "Allow uploads to logos" ON storage.objects
FOR INSERT TO anon, authenticated WITH CHECK (bucket_id = 'logos');

CREATE POLICY "Allow reads from logos" ON storage.objects
FOR SELECT TO anon, authenticated USING (bucket_id = 'logos');

CREATE POLICY "Allow uploads to signatures" ON storage.objects
FOR INSERT TO anon, authenticated WITH CHECK (bucket_id = 'signatures');

CREATE POLICY "Allow reads from signatures" ON storage.objects
FOR SELECT TO anon, authenticated USING (bucket_id = 'signatures');
```

---

Made with ❤️ in India 🇮🇳
