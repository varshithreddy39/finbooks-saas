from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from ..schemas import InvoiceCreate
from ..database import get_supabase
from ..services.invoice_service import InvoiceService
from ..auth_utils import get_current_user
import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from num2words import num2words
from datetime import datetime

router = APIRouter()

async def verify_company_access(company_id: str, user, db):
    res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", user.id).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Access to this business profile is denied")

@router.get("/")
async def get_invoices(company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    res = db.table("invoices").select("*, customers(name)").eq("company_id", company_id).execute()
    return res.data

@router.post("/create")
async def create_invoice(invoice: InvoiceCreate, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    service = InvoiceService(db)
    try:
        new_invoice = await service.create_invoice(invoice, company_id)
        return new_invoice
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{invoice_id}")
async def get_invoice_by_id(invoice_id: str, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    service = InvoiceService(db)
    try:
        return await service.get_invoice(invoice_id, company_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{invoice_id}")
async def update_invoice(invoice_id: str, invoice: InvoiceCreate, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    service = InvoiceService(db)
    try:
        updated = await service.update_invoice(invoice_id, invoice, company_id)
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    service = InvoiceService(db)
    try:
        invoice = await service.get_invoice(invoice_id, company_id)
        
        comp_res = db.table("company_profile").select("*").eq("id", company_id).execute()
        company = comp_res.data[0]
        
        cust_res = db.table("customers").select("*").eq("id", invoice["customer_id"]).execute()
        customer = cust_res.data[0] if cust_res.data else {}
        
        # Prepare billing details (overrides on invoice take precedence)
        billing_details = {
            "name": invoice.get("bill_to_name") or customer.get("name"),
            "address": invoice.get("bill_to_address") or customer.get("address"),
            "gstin": invoice.get("bill_to_gstin") or customer.get("gstin"),
            "state": invoice.get("bill_to_state") or customer.get("state"),
            "state_code": invoice.get("bill_to_state_code") or customer.get("state_code")
        }
        
        items = invoice["items"]
        for item in items:
            prod_res = db.table("products").select("name, sku, unit, hsn_sac").eq("id", item["product_id"]).execute()
            if prod_res.data:
                item["product_name"] = prod_res.data[0].get("name", "")
                item["product_sku"] = prod_res.data[0].get("sku", "")
                item["unit"] = prod_res.data[0].get("unit", "")
                item["hsn_sac"] = prod_res.data[0].get("hsn_sac", "")
                # description is already on the item from invoice_items table
                
        total_qty = sum(item.get("qty", 0) for item in items)
        is_intra_state = invoice.get("supply_type") == "Intra-state"
        raw_amount = invoice.get("total_amount", 0)
        decimal_part = raw_amount - int(raw_amount)
        rounded_amount = int(raw_amount) + (1 if decimal_part >= 0.5 else 0)
        round_off = round(rounded_amount - raw_amount, 2)
        amount_words = num2words(rounded_amount, lang='en_IN').replace(',', '').title() + " Rupees Only"
        
        if invoice.get("date"):
            invoice["date"] = datetime.strptime(invoice["date"], "%Y-%m-%d")
            
        # Get backend root directory
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        templates_dir = os.path.join(backend_root, "app", "templates", "invoices")
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template("gst_template.html")
        
        pan = ""
        if company.get("gstin") and len(company["gstin"]) == 15:
            pan = company["gstin"][2:12]
            
        # Resolve logo and signature paths for WeasyPrint
        uploads_dir = os.path.join(backend_root, "uploads")
        for key in ["logo_url", "signature_url"]:
            if company.get(key) and "localhost" in company[key]:
                filename = company[key].split("/")[-1]
                local_path = os.path.join(uploads_dir, filename)
                if os.path.exists(local_path):
                    company[key] = f"file://{local_path}"

        html_content = template.render(
            company=company,
            customer=customer,
            billing=billing_details,
            invoice=invoice,
            items=items,
            is_intra_state=is_intra_state,
            total_qty=total_qty,
            amount_in_words=amount_words,
            round_off=round_off,
            rounded_amount=rounded_amount,
            PAN_NUMBER=pan
        )
        
        # Specify base_url so WeasyPrint can resolve file:// links
        pdf_bytes = HTML(string=html_content, base_url=backend_root).write_pdf()
        return Response(content=pdf_bytes, media_type="application/pdf")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate PDF: {str(e)}")

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    
    # Check if it is the latest invoice to safely decrement the last_num_used counter
    latest = db.table("invoices").select("id").eq("company_id", company_id).order("created_at", desc=True).limit(1).execute()
    if latest.data and latest.data[0]["id"] == invoice_id:
        comp = db.table("company_profile").select("invoice_settings").eq("id", company_id).execute()
        if comp.data:
            settings = comp.data[0].get("invoice_settings") or {}
            if settings.get("last_num_used", 0) > 0:
                settings["last_num_used"] -= 1
                db.table("company_profile").update({"invoice_settings": settings}).eq("id", company_id).execute()
                
    db.table("invoice_items").delete().eq("invoice_id", invoice_id).execute()
    db.table("invoices").delete().eq("id", invoice_id).eq("company_id", company_id).execute()
    return {"message": "Invoice deleted"}
