from typing import List
from ..schemas import InvoiceCreate, InvoiceItemBase
from .gst_engine import GSTEngine

class InvoiceService:
    def __init__(self, db):
        self.db = db
        
    async def create_invoice(self, invoice_data: InvoiceCreate, company_id: str):
        # 1. Fetch Company details
        company = self.db.table("company_profile").select("state_code, invoice_settings").eq("id", company_id).execute()
        if not company.data:
            raise ValueError("Company profile not found or access denied.")
        seller_state_code = company.data[0].get("state_code", "")
        invoice_settings = company.data[0].get("invoice_settings") or {}
        
        # 2. Extract numbering sequence
        last_num = invoice_settings.get("last_num_used", 0)
        
        # 2b. Fetch Customer details for fallback
        customer = self.db.table("customers").select("*").eq("id", invoice_data.customer_id).execute()
        if not customer.data:
            raise ValueError("Please select a valid customer before saving the invoice.")
        
        # Priority: 1. Overrides from input, 2. Customer record
        buyer_state_code = invoice_data.bill_to_state_code or customer.data[0].get("state_code", "")
        
        # 3. Calculate Taxes
        calculation = GSTEngine.calculate_taxes(invoice_data.items, seller_state_code, buyer_state_code)
        
        # 4. Insert Invoice
        invoice_insert = {
            "company_id": company_id,
            "customer_id": invoice_data.customer_id,
            "invoice_no": invoice_data.invoice_no,
            "date": str(invoice_data.invoice_date),
            "supply_type": "Intra-state" if calculation["is_intra_state"] else "Inter-state",
            "reverse_charge": invoice_data.reverse_charge,
            "vehicle_no": invoice_data.vehicle_no,
            "eway_bill": invoice_data.eway_bill,
            "purchase_order_no": invoice_data.purchase_order_no,
            "trans_mode": invoice_data.trans_mode,
            "bill_to_name": invoice_data.bill_to_name or customer.data[0].get("name"),
            "bill_to_address": invoice_data.bill_to_address or customer.data[0].get("address"),
            "bill_to_gstin": invoice_data.bill_to_gstin or customer.data[0].get("gstin"),
            "bill_to_state": invoice_data.bill_to_state or customer.data[0].get("state"),
            "bill_to_state_code": invoice_data.bill_to_state_code or customer.data[0].get("state_code"),
            "ship_to_name": invoice_data.ship_to_name,
            "ship_to_gstin": invoice_data.ship_to_gstin,
            "ship_to_address": invoice_data.ship_to_address,
            "ship_to_state": invoice_data.ship_to_state,
            "ship_to_state_code": invoice_data.ship_to_state_code,
            "terms_and_conditions": invoice_data.terms_and_conditions,
            "authorised_signatory": invoice_data.authorised_signatory,
            "taxable_value": calculation["taxable_value"],
            "total_gst": calculation["total_gst"],
            "total_amount": calculation["total_amount"],
            "status": "Draft"
        }
        
        res = self.db.table("invoices").insert(invoice_insert).execute()
        invoice_id = res.data[0]["id"]
        
        # 5. Insert Items
        for item in calculation["items"]:
            item_insert = {
                "invoice_id": invoice_id,
                "product_id": item["product_id"],
                "qty": item["qty"],
                "rate": item["rate"],
                "gst_rate": item["gst_rate"],
                "taxable_amount": item["taxable_amount"],
                "gst_amount": item["gst_amount"],
                "description": item.get("description") or ""
            }
            self.db.table("invoice_items").insert(item_insert).execute()
            
        # 7. Update Company Settings (Increment Last Number)
        inv_settings = invoice_settings.copy()
        # Track the actual number used from the invoice_no if possible, else increment
        inv_settings["last_num_used"] = last_num + 1
        db_res = self.db.table("company_profile").update({
            "invoice_settings": inv_settings
        }).eq("id", company_id).execute()
        
        return res.data[0]

    async def get_invoice(self, invoice_id: str, company_id: str):
        inv = self.db.table("invoices").select("*").eq("id", invoice_id).eq("company_id", company_id).execute()
        if not inv.data:
            raise ValueError("Invoice not found")
        items = self.db.table("invoice_items").select("*").eq("invoice_id", invoice_id).execute()
        invoice = inv.data[0]
        invoice["items"] = items.data
        return invoice

    async def update_invoice(self, invoice_id: str, invoice_data: InvoiceCreate, company_id: str):
        # 1. Fetch seller and buyer state codes to recalculate GST if needed
        company = self.db.table("company_profile").select("state_code").eq("id", company_id).execute()
        if not company.data:
            raise ValueError("Company profile not found.")
        seller_state_code = company.data[0].get("state_code", "")

        customer = self.db.table("customers").select("*").eq("id", invoice_data.customer_id).execute()
        if not customer.data:
            raise ValueError("Invalid customer.")
        
        buyer_state_code = invoice_data.bill_to_state_code or customer.data[0].get("state_code", "")

        calculation = GSTEngine.calculate_taxes(invoice_data.items, seller_state_code, buyer_state_code)

        invoice_update = {
            "customer_id": invoice_data.customer_id,
            "invoice_no": invoice_data.invoice_no,
            "date": str(invoice_data.invoice_date),
            "supply_type": "Intra-state" if calculation["is_intra_state"] else "Inter-state",
            "reverse_charge": invoice_data.reverse_charge,
            "vehicle_no": invoice_data.vehicle_no,
            "eway_bill": invoice_data.eway_bill,
            "purchase_order_no": invoice_data.purchase_order_no,
            "trans_mode": invoice_data.trans_mode,
            "bill_to_name": invoice_data.bill_to_name or customer.data[0].get("name"),
            "bill_to_address": invoice_data.bill_to_address or customer.data[0].get("address"),
            "bill_to_gstin": invoice_data.bill_to_gstin or customer.data[0].get("gstin"),
            "bill_to_state": invoice_data.bill_to_state or customer.data[0].get("state"),
            "bill_to_state_code": invoice_data.bill_to_state_code or customer.data[0].get("state_code"),
            "ship_to_name": invoice_data.ship_to_name,
            "ship_to_gstin": invoice_data.ship_to_gstin,
            "ship_to_address": invoice_data.ship_to_address,
            "ship_to_state": invoice_data.ship_to_state,
            "ship_to_state_code": invoice_data.ship_to_state_code,
            "terms_and_conditions": invoice_data.terms_and_conditions,
            "authorised_signatory": invoice_data.authorised_signatory,
            "taxable_value": calculation["taxable_value"],
            "total_gst": calculation["total_gst"],
            "total_amount": calculation["total_amount"]
        }

        self.db.table("invoices").update(invoice_update).eq("id", invoice_id).eq("company_id", company_id).execute()
        
        # Completely replace line items
        self.db.table("invoice_items").delete().eq("invoice_id", invoice_id).execute()

        for item in calculation["items"]:
            item_insert = {
                "invoice_id": invoice_id,
                "product_id": item["product_id"],
                "qty": item["qty"],
                "rate": item["rate"],
                "gst_rate": item["gst_rate"],
                "taxable_amount": item["taxable_amount"],
                "gst_amount": item["gst_amount"],
                "description": item.get("description") or ""
            }
            self.db.table("invoice_items").insert(item_insert).execute()
            
        return await self.get_invoice(invoice_id, company_id)
