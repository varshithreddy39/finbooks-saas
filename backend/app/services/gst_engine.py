from typing import List
from ..schemas import InvoiceItemBase, QuotationItemBase

class GSTEngine:
    @staticmethod
    def calculate_taxes(items: List, seller_state_code: str, buyer_state_code: str):
        taxable_value = 0
        total_gst = 0
        
        calculated_items = []
        
        is_intra_state = (seller_state_code == buyer_state_code)
        
        for item in items:
            # item can be InvoiceItemBase or QuotationItemBase
            taxable_amount = item.qty * item.rate
            gst_amount = taxable_amount * (item.gst_rate / 100)
            
            taxable_value += taxable_amount
            total_gst += gst_amount
            
            calculated_items.append({
                "product_id": item.product_id,
                "qty": item.qty,
                "rate": item.rate,
                "gst_rate": item.gst_rate,
                "taxable_amount": taxable_amount,
                "gst_amount": gst_amount,
                "cgst": gst_amount / 2 if is_intra_state else 0,
                "sgst": gst_amount / 2 if is_intra_state else 0,
                "igst": gst_amount if not is_intra_state else 0,
                "description": getattr(item, "description", None) or ""
            })
            
        return {
            "taxable_value": taxable_value,
            "total_gst": total_gst,
            "total_amount": taxable_value + total_gst,
            "is_intra_state": is_intra_state,
            "items": calculated_items
        }
