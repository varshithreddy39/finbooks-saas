# Finbooks — Database Schema Design

All tables live in Supabase (PostgreSQL). Multi-tenancy is enforced via `company_id` foreign key on every data table.

---

## Tables Overview

| Table | Purpose |
|-------|---------|
| `company_profile` | One record per business (tenant) |
| `customers` | Client directory per company |
| `vendors` | Vendor directory per company |
| `products` | Product/service catalog per company |
| `invoices` | Tax invoice headers |
| `invoice_items` | Line items for each invoice |
| `quotations` | Quotation headers |
| `quotation_items` | Line items for each quotation |
| `credit_notes` | Credit note headers |
| `credit_note_items` | Line items for each credit note |

---

## Table Definitions

### company_profile
Stores one record per registered business. Linked to Supabase Auth user via `user_id`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Auto-generated |
| `user_id` | UUID | Links to Supabase auth.users |
| `company_name` | TEXT | Trade/display name |
| `gstin` | TEXT UNIQUE | Locked after signup |
| `address` | TEXT | Registered address |
| `state` | TEXT | Indian state name |
| `state_code` | TEXT | 2-digit GST state code |
| `primary_email` | TEXT NOT NULL | From signup, locked |
| `secondary_email` | TEXT | Optional |
| `phone` | TEXT NOT NULL | Primary mobile from signup |
| `additional_phone` | TEXT | Optional |
| `logo_url` | TEXT | Supabase Storage URL |
| `signature_url` | TEXT | Supabase Storage URL |
| `bank_details` | JSONB | `{acc_name, acc_no, ifsc, bank, branch}` |
| `invoice_settings` | JSONB | Numbering, FY, display prefs |
| `authorised_signatory` | TEXT | Name printed on docs |
| `created_at` | TIMESTAMPTZ | Auto |

**invoice_settings JSON structure:**
```json
{
  "numbering": { "prefix": "INV-", "start_no": 1, "padding": 4 },
  "financial_year": { "start": "2025-04-01", "end": "2026-03-31", "reset": true },
  "last_num_used": 12,
  "last_quo_used": 5,
  "display": {
    "show_logo": true, "show_bank": true,
    "show_transport": true, "show_reverse": true, "precision": 2
  }
}
```

---

### customers
Client directory. Each record belongs to one company.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `company_id` | UUID FK | → company_profile(id) CASCADE |
| `name` | TEXT NOT NULL | |
| `gstin` | TEXT | |
| `email` | TEXT | |
| `phone` | TEXT | |
| `address` | TEXT | |
| `state` | TEXT | |
| `state_code` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

---

### vendors
Same structure as customers, separate table.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `company_id` | UUID FK | → company_profile(id) CASCADE |
| `name` | TEXT NOT NULL | |
| `gstin` | TEXT | |
| `email` | TEXT | |
| `phone` | TEXT | |
| `address` | TEXT | |
| `state` | TEXT | |
| `state_code` | TEXT | |

---

### products
Product/service catalog per company.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `company_id` | UUID FK | → company_profile(id) CASCADE |
| `name` | TEXT NOT NULL | |
| `sku` | TEXT | Optional stock-keeping unit |
| `hsn_sac` | TEXT NOT NULL | HSN (goods) or SAC (services) code |
| `default_gst_rate` | NUMERIC | e.g. 18.0 |
| `sales_price` | NUMERIC NOT NULL | Default selling price |
| `unit` | TEXT | PCS, KGS, MTR, etc. |
| `opening_stock` | NUMERIC | Initial stock quantity |

---

### invoices
Tax invoice header. One row per invoice.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `company_id` | UUID FK | → company_profile(id) CASCADE |
| `customer_id` | UUID FK | → customers(id) |
| `invoice_no` | TEXT NOT NULL | e.g. INV-2025-0001 |
| `date` | DATE | Invoice date |
| `supply_type` | TEXT | `Intra-state` or `Inter-state` |
| `reverse_charge` | BOOLEAN | |
| `vehicle_no` | TEXT | Transport |
| `eway_bill` | TEXT | e-Way bill number |
| `purchase_order_no` | TEXT | Buyer's PO |
| `trans_mode` | TEXT | Road/Rail/Air/Ship |
| `bill_to_name` | TEXT | Override from customer |
| `bill_to_address` | TEXT | |
| `bill_to_gstin` | TEXT | |
| `bill_to_state` | TEXT | |
| `bill_to_state_code` | TEXT | |
| `ship_to_name` | TEXT | |
| `ship_to_address` | TEXT | |
| `ship_to_gstin` | TEXT | |
| `ship_to_state` | TEXT | |
| `ship_to_state_code` | TEXT | |
| `terms_and_conditions` | TEXT | |
| `authorised_signatory` | TEXT | |
| `taxable_value` | NUMERIC | Sum of all line taxable amounts |
| `total_gst` | NUMERIC | Sum of all GST |
| `total_amount` | NUMERIC | taxable_value + total_gst |
| `status` | TEXT | Draft / Issued |
| `created_at` | TIMESTAMPTZ | |

**Unique constraint:** `(company_id, invoice_no)`

---

### invoice_items
Line items for each invoice.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `invoice_id` | UUID FK | → invoices(id) CASCADE |
| `product_id` | UUID FK | → products(id) |
| `qty` | NUMERIC NOT NULL | |
| `rate` | NUMERIC NOT NULL | Per unit price |
| `gst_rate` | NUMERIC NOT NULL | e.g. 18.0 |
| `taxable_amount` | NUMERIC | qty × rate |
| `gst_amount` | NUMERIC | taxable_amount × gst_rate/100 |
| `description` | TEXT | Optional line description |

---

### quotations
Same structure as invoices with additional fields.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `company_id` | UUID FK | → company_profile(id) CASCADE |
| `customer_id` | UUID FK | → customers(id) |
| `quotation_no` | TEXT NOT NULL | |
| `date` | DATE | |
| `valid_until` | DATE | Expiry date |
| `bill_to_*` | TEXT | Same as invoices |
| `ship_to_*` | TEXT | Same as invoices |
| `terms_and_conditions` | TEXT | |
| `authorised_signatory` | TEXT | |
| `taxable_value` | NUMERIC | |
| `total_gst` | NUMERIC | |
| `total_amount` | NUMERIC | |
| `status` | TEXT | Open / Accepted / Expired |
| `created_at` | TIMESTAMPTZ | |

---

### quotation_items
Same structure as invoice_items with `quotation_id` instead of `invoice_id`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `quotation_id` | UUID FK | → quotations(id) CASCADE |
| `product_id` | UUID FK | → products(id) |
| `qty` | NUMERIC | |
| `rate` | NUMERIC | |
| `gst_rate` | NUMERIC | |
| `taxable_amount` | NUMERIC | |
| `gst_amount` | NUMERIC | |
| `description` | TEXT | |

---

### credit_notes

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `company_id` | UUID FK | → company_profile(id) CASCADE |
| `customer_id` | UUID FK | → customers(id) |
| `credit_note_no` | TEXT NOT NULL | |
| `date` | DATE | |
| `invoice_no` | TEXT | Reference invoice number |
| `reason` | TEXT | Return / Price correction / Damage |
| `vehicle_no` | TEXT | |
| `eway_bill_no` | TEXT | |
| `dispatched_through` | TEXT | |
| `destination` | TEXT | |
| `bill_to_name` | TEXT | |
| `bill_to_address` | TEXT | |
| `bill_to_gstin` | TEXT | |
| `bill_to_state` | TEXT | |
| `bill_to_state_code` | TEXT | |
| `authorised_signatory` | TEXT | |
| `taxable_value` | NUMERIC | |
| `total_gst` | NUMERIC | |
| `total_amount` | NUMERIC | |
| `status` | TEXT | Issued / Pending |
| `created_at` | TIMESTAMPTZ | |

---

### credit_note_items

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `credit_note_id` | UUID FK | → credit_notes(id) CASCADE |
| `product_id` | UUID FK | → products(id) |
| `qty` | NUMERIC | |
| `rate` | NUMERIC | |
| `gst_rate` | NUMERIC | |
| `taxable_amount` | NUMERIC | |
| `gst_amount` | NUMERIC | |
| `description` | TEXT | |

---

## GST Calculation Logic

```python
# Determine supply type
if seller_state_code == buyer_state_code:
    supply_type = "Intra-state"
    cgst = taxable_amount * (gst_rate / 2) / 100
    sgst = taxable_amount * (gst_rate / 2) / 100
    igst = 0
else:
    supply_type = "Inter-state"
    cgst = 0
    sgst = 0
    igst = taxable_amount * gst_rate / 100
```

---

## Cascade Deletes

All child tables use `ON DELETE CASCADE` from `company_profile`. Deleting a company removes all its invoices, quotations, credit notes, customers, vendors, and products automatically.

---

## Supabase Storage Buckets

| Bucket | Access | Contents |
|--------|--------|----------|
| `logos` | Public | Company logo images |
| `signatures` | Public | Authorised signatory images |
