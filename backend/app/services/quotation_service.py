from typing import List
from ..schemas import QuotationCreate, QuotationItemBase
from .gst_engine import GSTEngine

class QuotationService:
    def __init__(self, db):
        self.db = db
        
    async def create_quotation(self, quotation_data: QuotationCreate, company_id: str):
        # 1. Fetch Company details
        company = self.db.table("company_profile").select("state_code").eq("id", company_id).execute()
        if not company.data:
            raise ValueError("Company profile not found.")
        seller_state_code = company.data[0].get("state_code", "")
        
        # 2. Fetch Customer details for fallback
        customer = self.db.table("customers").select("*").eq("id", quotation_data.customer_id).execute()
        if not customer.data:
            raise ValueError("Invalid customer.")
        
        # Priority: 1. Overrides from input, 2. Customer record
        buyer_state_code = quotation_data.bill_to_state_code or customer.data[0].get("state_code", "")
        
        # 3. Calculate Taxes
        calculation = GSTEngine.calculate_taxes(quotation_data.items, seller_state_code, buyer_state_code)
        
        # 4. Insert Quotation
        quotation_insert = {
            "company_id": company_id,
            "customer_id": quotation_data.customer_id,
            "quotation_no": quotation_data.quotation_no,
            "date": str(quotation_data.date),
            "valid_until": str(quotation_data.valid_until) if quotation_data.valid_until else None,
            "bill_to_name": quotation_data.bill_to_name or customer.data[0].get("name"),
            "bill_to_address": quotation_data.bill_to_address or customer.data[0].get("address"),
            "bill_to_gstin": quotation_data.bill_to_gstin or customer.data[0].get("gstin"),
            "bill_to_state": quotation_data.bill_to_state or customer.data[0].get("state"),
            "bill_to_state_code": quotation_data.bill_to_state_code or customer.data[0].get("state_code"),
            "ship_to_name": quotation_data.ship_to_name,
            "ship_to_gstin": quotation_data.ship_to_gstin,
            "ship_to_address": quotation_data.ship_to_address,
            "ship_to_state": quotation_data.ship_to_state,
            "ship_to_state_code": quotation_data.ship_to_state_code,
            "terms_and_conditions": quotation_data.terms_and_conditions,
            "authorised_signatory": quotation_data.authorised_signatory,
            "taxable_value": calculation["taxable_value"],
            "total_gst": calculation["total_gst"],
            "total_amount": calculation["total_amount"],
            "status": "Open"
        }
        
        res = self.db.table("quotations").insert(quotation_insert).execute()
        quotation_id = res.data[0]["id"]
        
        # 5. Insert Items
        for item in calculation["items"]:
            item_insert = {
                "quotation_id": quotation_id,
                "product_id": item["product_id"],
                "qty": item["qty"],
                "rate": item["rate"],
                "gst_rate": item["gst_rate"],
                "taxable_amount": item["taxable_amount"],
                "gst_amount": item["gst_amount"],
                "description": item.get("description") or ""
            }
            self.db.table("quotation_items").insert(item_insert).execute()
            
        # 6. Update Company Settings (Increment Last Number)
        comp_settings = self.db.table("company_profile").select("invoice_settings").eq("id", company_id).execute()
        if comp_settings.data:
            inv_settings = comp_settings.data[0].get("invoice_settings") or {}
            last_num = inv_settings.get("last_quo_used", 0)
            inv_settings["last_quo_used"] = last_num + 1
            self.db.table("company_profile").update({"invoice_settings": inv_settings}).eq("id", company_id).execute()
            
        return res.data[0]

    async def get_quotation(self, quotation_id: str, company_id: str):
        quo = self.db.table("quotations").select("*").eq("id", quotation_id).eq("company_id", company_id).execute()
        if not quo.data:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        items = self.db.table("quotation_items").select("*, products(*)").eq("quotation_id", quotation_id).execute()
        quotation = quo.data[0]
        
        item_list = []
        for it in items.data:
            it["product_name"] = it["products"]["name"] if it.get("products") else "Product"
            it["unit"] = it["products"]["unit"] if it.get("products") else "PCS"
            it["hsn_sac"] = it["products"]["hsn_sac"] if it.get("products") else "-"
            item_list.append(it)
            
        quotation["items"] = item_list
        return quotation

    async def list_quotations(self, company_id: str):
        res = self.db.table("quotations").select("*, customers(name)").eq("company_id", company_id).order("created_at", desc=True).execute()
        return res.data

    async def update_quotation(self, quotation_id: str, quotation_data: QuotationCreate, company_id: str):
        company = self.db.table("company_profile").select("state_code").eq("id", company_id).execute()
        seller_state_code = company.data[0].get("state_code", "")

        customer = self.db.table("customers").select("*").eq("id", quotation_data.customer_id).execute()
        buyer_state_code = quotation_data.bill_to_state_code or customer.data[0].get("state_code", "")

        calculation = GSTEngine.calculate_taxes(quotation_data.items, seller_state_code, buyer_state_code)

        quotation_update = {
            "customer_id": quotation_data.customer_id,
            "quotation_no": quotation_data.quotation_no,
            "date": str(quotation_data.date),
            "valid_until": str(quotation_data.valid_until) if quotation_data.valid_until else None,
            "bill_to_name": quotation_data.bill_to_name or customer.data[0].get("name"),
            "bill_to_address": quotation_data.bill_to_address or customer.data[0].get("address"),
            "bill_to_gstin": quotation_data.bill_to_gstin or customer.data[0].get("gstin"),
            "bill_to_state": quotation_data.bill_to_state or customer.data[0].get("state"),
            "bill_to_state_code": quotation_data.bill_to_state_code or customer.data[0].get("state_code"),
            "ship_to_name": quotation_data.ship_to_name,
            "ship_to_gstin": quotation_data.ship_to_gstin,
            "ship_to_address": quotation_data.ship_to_address,
            "ship_to_state": quotation_data.ship_to_state,
            "ship_to_state_code": quotation_data.ship_to_state_code,
            "terms_and_conditions": quotation_data.terms_and_conditions,
            "authorised_signatory": quotation_data.authorised_signatory,
            "taxable_value": calculation["taxable_value"],
            "total_gst": calculation["total_gst"],
            "total_amount": calculation["total_amount"]
        }

        self.db.table("quotations").update(quotation_update).eq("id", quotation_id).eq("company_id", company_id).execute()
        self.db.table("quotation_items").delete().eq("quotation_id", quotation_id).execute()

        for item in calculation["items"]:
            item_insert = {
                "quotation_id": quotation_id,
                "product_id": item["product_id"],
                "qty": item["qty"],
                "rate": item["rate"],
                "gst_rate": item["gst_rate"],
                "taxable_amount": item["taxable_amount"],
                "gst_amount": item["gst_amount"],
                "description": item.get("description") or ""
            }
            self.db.table("quotation_items").insert(item_insert).execute()
            
        return await self.get_quotation(quotation_id, company_id)
