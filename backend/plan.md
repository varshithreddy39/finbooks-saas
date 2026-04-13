# Backend Plan: Precision Ledger (FastAPI + Supabase)

## 🎯 1. High-Level Architecture
- **Frontend**: Standard HTML/Tailwind (Stitch)
- **Backend**: FastAPI (Python 3.10+)
- **Database**: Supabase (PostgreSQL)
- **Auth**: JWT-based Authentication
- **Multi-tenancy**: All data filtered by `company_id`

## 🗄️ 2. Database Schema (Supabase)

### Users & Auth
- `users`: `id`, `email`, `password_hash`, `full_name`, `created_at`

### Multi-Tenant Core
- `companies`: `id`, `owner_id`, `trade_name`, `gstin`, `address`, `state`, `state_code`, `phone`, `email`, `logo_url`
- `bank_details`: `id`, `company_id`, `bank_name`, `account_no`, `ifsc`, `branch`

### Master Data
- `customers`: `id`, `company_id`, `name`, `gstin`, `email`, `phone`, `address`, `state`, `state_code`
- `vendors`: `id`, `company_id`, `name`, `gstin`, `email`, `phone`, `address`, `state`, `state_code`
- `products`: `id`, `company_id`, `name`, `sku`, `hsn_sac`, `default_gst_rate`, `sales_price`, `unit`, `opening_stock`

### Transactions
- `invoices`: `id`, `company_id`, `customer_id`, `invoice_no`, `date`, `supply_type`, `reverse_charge`, `vehicle_no`, `eway_bill`, `taxable_value`, `total_gst`, `total_amount`, `status`, `created_at`
- `invoice_items`: `id`, `invoice_id`, `product_id`, `qty`, `rate`, `gst_rate`, `taxable_amount`, `gst_amount`
- `quotations`: (Similar to invoices) + `expiry_date`
- `credit_notes`: `id`, `company_id`, `invoice_id`, `reason`, `total_amount`, `status`

## 🚀 3. API Endpoints (FastAPI)

### 🔐 Auth
- `POST /auth/signup`: Create user
- `POST /auth/login`: Return JWT token

### 🏢 Company
- `GET /company/profile`: Fetch active company
- `PUT /company/profile`: Update details

### 📦 Masters
- `GET/POST /customers`: Manage customers
- `GET/POST /products`: Manage inventory

### 🧾 Invoice Engine
- `POST /invoice/create`: 
  1. Validate input
  2. Calculate Taxes (CGST/SGST/IGST)
  3. Store in DB
- `GET /invoice/{id}/pdf`: Generate PDF using template logic

### 📊 Dashboard
- `GET /dashboard/stats`: Aggregated summary

## 📄 4. Core Logic: GST Calculation
```python
if seller_state_code == buyer_state_code:
    # Intra-state
    cgst = total_taxable * (gst_rate / 2)
    sgst = total_taxable * (gst_rate / 2)
    igst = 0
else:
    # Inter-state
    cgst = 0
    sgst = 0
    igst = total_taxable * gst_rate
```

## 🛠️ 5. Scalability
- **Relational Integrity**: Foreign keys enforce data consistency between invoices and items.
- **Indexing**: Optimized queries on `company_id` and `invoice_no`.
- **Modular Code**: Separate routers for Auth, Sales, and Masters.
