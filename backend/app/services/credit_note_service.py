from typing import List, Dict, Any, Optional
from uuid import UUID
from ..database import supabase
from ..schemas import CreditNoteCreate

class CreditNoteService:
    def __init__(self, db):
        self.db = db

    async def create_credit_note(self, company_id: str, credit_note_data: CreditNoteCreate) -> Dict[str, Any]:
        # 1. Insert Credit Note
        items_data = credit_note_data.items
        cn_dict = credit_note_data.dict(exclude={'items'})
        cn_dict['company_id'] = company_id
        if 'date' in cn_dict and cn_dict['date']:
            cn_dict['date'] = str(cn_dict['date'])
        
        # Calculate totals
        taxable_value = 0
        total_gst = 0
        
        # We need to process items first to get totals
        processed_items = []
        for item in items_data:
            taxable_amount = item.qty * item.rate
            gst_amount = taxable_amount * (item.gst_rate / 100)
            taxable_value += taxable_amount
            total_gst += gst_amount
            processed_items.append({
                "product_id": item.product_id,
                "qty": item.qty,
                "rate": item.rate,
                "gst_rate": item.gst_rate,
                "taxable_amount": taxable_amount,
                "gst_amount": gst_amount,
                "description": getattr(item, "description", None) or ""
            })

        cn_dict['taxable_value'] = taxable_value
        cn_dict['total_gst'] = total_gst
        cn_dict['total_amount'] = taxable_value + total_gst

        response = self.db.table("credit_notes").insert(cn_dict).execute()
        if not response.data:
            raise Exception("Failed to create credit note")
        
        credit_note_id = response.data[0]['id']

        # 2. Insert Items
        for item in processed_items:
            item['credit_note_id'] = credit_note_id
            self.db.table("credit_note_items").insert(item).execute()

        return response.data[0]

    async def get_credit_notes(self, company_id: str) -> List[Dict[str, Any]]:
        response = self.db.table("credit_notes") \
            .select("*, customers(name)") \
            .eq("company_id", company_id) \
            .order("created_at", desc=True) \
            .execute()
        return response.data

    async def get_credit_note(self, credit_note_id: str, company_id: str = None) -> Dict[str, Any]:
        query = self.db.table("credit_notes").select("*, customers(*)").eq("id", credit_note_id)
        if company_id:
            query = query.eq("company_id", company_id)
        cn_response = query.execute()
        
        if not cn_response.data:
            return None
        
        credit_note = cn_response.data[0]
        
        # Get Items with Product info
        items_response = self.db.table("credit_note_items") \
            .select("*, products(name, hsn_sac, unit)") \
            .eq("credit_note_id", credit_note_id) \
            .execute()
            
        credit_note['items'] = items_response.data
        return credit_note

    async def update_credit_note(self, credit_note_id: str, company_id: str, credit_note_data: CreditNoteCreate) -> Dict[str, Any]:
        # 1. Update Credit Note
        items_data = credit_note_data.items
        cn_dict = credit_note_data.dict(exclude={'items'})
        cn_dict['company_id'] = company_id
        if 'date' in cn_dict and cn_dict['date']:
            cn_dict['date'] = str(cn_dict['date'])
        
        # Calculate totals
        taxable_value = 0
        total_gst = 0
        
        processed_items = []
        for item in items_data:
            taxable_amount = item.qty * item.rate
            gst_amount = taxable_amount * (item.gst_rate / 100)
            taxable_value += taxable_amount
            total_gst += gst_amount
            processed_items.append({
                "product_id": item.product_id,
                "qty": item.qty,
                "rate": item.rate,
                "gst_rate": item.gst_rate,
                "taxable_amount": taxable_amount,
                "gst_amount": gst_amount,
                "credit_note_id": credit_note_id,
                "description": getattr(item, "description", None) or ""
            })

        cn_dict['taxable_value'] = taxable_value
        cn_dict['total_gst'] = total_gst
        cn_dict['total_amount'] = taxable_value + total_gst

        self.db.table("credit_notes").update(cn_dict).eq("id", credit_note_id).execute()
        
        # 2. Update Items (Delete and Re-insert)
        self.db.table("credit_note_items").delete().eq("credit_note_id", credit_note_id).execute()
        for item in processed_items:
            self.db.table("credit_note_items").insert(item).execute()

        return await self.get_credit_note(credit_note_id)

    async def delete_credit_note(self, credit_note_id: str):
        self.db.table("credit_notes").delete().eq("id", credit_note_id).execute()
