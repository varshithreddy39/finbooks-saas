-- DATABASE SCHEMA FOR SUPERBASE (POSTGRESQL)

-- 1. Company Profile Table (Core SaaS Entity)
CREATE TABLE IF NOT EXISTS company_profile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES auth.users(id),
    gstin TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    address TEXT,
    state TEXT,
    state_code TEXT,
    primary_email TEXT NOT NULL,
    secondary_email TEXT,
    phone TEXT NOT NULL, -- Primary
    additional_phone TEXT,
    logo_url TEXT,
    signature_url TEXT,
    bank_details JSONB,
    invoice_settings JSONB,
    authorised_signatory TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES company_profile(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    gstin TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    state TEXT,
    state_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Vendors Table
CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES company_profile(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    gstin TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    state TEXT,
    state_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Products Table
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES company_profile(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sku TEXT,
    hsn_sac TEXT NOT NULL,
    default_gst_rate NUMERIC DEFAULT 18.0,
    sales_price NUMERIC NOT NULL,
    unit TEXT DEFAULT 'PCS',
    opening_stock NUMERIC DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Invoices Table
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES company_profile(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id),
    invoice_no TEXT NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    supply_type TEXT CHECK (supply_type IN ('Intra-state', 'Inter-state')),
    reverse_charge BOOLEAN DEFAULT FALSE,
    vehicle_no TEXT,
    eway_bill TEXT,
    purchase_order_no TEXT,
    bill_to_name TEXT,
    bill_to_address TEXT,
    bill_to_gstin TEXT,
    bill_to_state TEXT,
    bill_to_state_code TEXT,
    ship_to_name TEXT,
    ship_to_address TEXT,
    ship_to_gstin TEXT,
    ship_to_state TEXT,
    ship_to_state_code TEXT,
    terms_and_conditions TEXT,
    authorised_signatory TEXT,
    taxable_value NUMERIC DEFAULT 0,
    total_gst NUMERIC DEFAULT 0,
    total_amount NUMERIC DEFAULT 0,
    status TEXT DEFAULT 'Draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(company_id, invoice_no)
);

-- 6. Invoice Line Items
CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    qty NUMERIC NOT NULL,
    rate NUMERIC NOT NULL,
    gst_rate NUMERIC NOT NULL,
    taxable_amount NUMERIC NOT NULL,
    gst_amount NUMERIC NOT NULL,
    description TEXT DEFAULT ''
);

-- Row Level Security (RLS) Examples
-- ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can only see their own company" ON companies FOR ALL USING (auth.uid() = owner_id);
-- ... similar policies for other tables using company_id ...

-- 7. Quotations Table
CREATE TABLE IF NOT EXISTS quotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES company_profile(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id),
    quotation_no TEXT NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    valid_until DATE,
    bill_to_name TEXT,
    bill_to_address TEXT,
    bill_to_gstin TEXT,
    bill_to_state TEXT,
    bill_to_state_code TEXT,
    ship_to_name TEXT,
    ship_to_address TEXT,
    ship_to_gstin TEXT,
    ship_to_state TEXT,
    ship_to_state_code TEXT,
    terms_and_conditions TEXT,
    authorised_signatory TEXT,
    taxable_value NUMERIC DEFAULT 0,
    total_gst NUMERIC DEFAULT 0,
    total_amount NUMERIC DEFAULT 0,
    status TEXT DEFAULT 'Open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(company_id, quotation_no)
);

-- 8. Quotation Line Items
CREATE TABLE IF NOT EXISTS quotation_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quotation_id UUID REFERENCES quotations(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    qty NUMERIC NOT NULL,
    rate NUMERIC NOT NULL,
    gst_rate NUMERIC NOT NULL,
    taxable_amount NUMERIC NOT NULL,
    gst_amount NUMERIC NOT NULL,
    description TEXT DEFAULT ''
);

-- 9. Credit Notes Table
CREATE TABLE IF NOT EXISTS credit_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES company_profile(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id),
    credit_note_no TEXT NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    vehicle_no TEXT,
    eway_bill_no TEXT,
    dispatched_through TEXT,
    destination TEXT,
    reason TEXT,
    bill_to_name TEXT,
    bill_to_address TEXT,
    bill_to_gstin TEXT,
    bill_to_state TEXT,
    bill_to_state_code TEXT,
    authorised_signatory TEXT,
    taxable_value NUMERIC DEFAULT 0,
    total_gst NUMERIC DEFAULT 0,
    total_amount NUMERIC DEFAULT 0,
    status TEXT DEFAULT 'Issued',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(company_id, credit_note_no)
);

-- 10. Credit Note Line Items
CREATE TABLE IF NOT EXISTS credit_note_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    credit_note_id UUID REFERENCES credit_notes(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    qty NUMERIC NOT NULL,
    rate NUMERIC NOT NULL,
    gst_rate NUMERIC NOT NULL,
    taxable_amount NUMERIC NOT NULL,
    gst_amount NUMERIC NOT NULL
);

