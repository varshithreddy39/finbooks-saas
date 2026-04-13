-- Run this in your Supabase SQL editor to add description column to existing tables
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';
ALTER TABLE quotation_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';
