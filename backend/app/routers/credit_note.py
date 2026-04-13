from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from ..schemas import CreditNoteCreate
from ..services.credit_note_service import CreditNoteService
from ..database import get_supabase
from ..auth_utils import get_current_user
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from weasyprint import HTML
import os
from num2words import num2words

router = APIRouter()

def format_currency_words(amount):
    try:
        whole = int(amount)
        fraction = int(round((amount - whole) * 100))
        
        parts = []
        if whole > 0:
            parts.append(num2words(whole, lang='en_IN').title() + " Rupees")
        
        if fraction > 0:
            if whole > 0:
                parts.append(num2words(fraction, lang='en_IN').title() + " Paise")
            else:
                parts.append(num2words(fraction, lang='en_IN').title() + " Paise")
        
        if not parts:
            return "Zero Rupees Only"
            
        if len(parts) > 1:
            return parts[0] + " And " + parts[1] + " Only"
        return parts[0] + " Only"
    except:
        return num2words(amount, lang='en_IN').title() + " Only"

@router.post("/create")
async def create_credit_note(cn_data: CreditNoteCreate, company_id: str, db=Depends(get_supabase), current_user: dict = Depends(get_current_user)):
    comp_res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", current_user.id).execute()
    if not comp_res.data:
        raise HTTPException(status_code=403, detail="Access denied")
    service = CreditNoteService(db)
    return await service.create_credit_note(company_id, cn_data)

@router.put("/{cn_id}")
async def update_credit_note(cn_id: str, cn_data: CreditNoteCreate, company_id: str, db=Depends(get_supabase), current_user: dict = Depends(get_current_user)):
    comp_res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", current_user.id).execute()
    if not comp_res.data:
        raise HTTPException(status_code=403, detail="Access denied")
    service = CreditNoteService(db)
    return await service.update_credit_note(cn_id, company_id, cn_data)

# NOTE: /list must be defined BEFORE /{cn_id} to avoid FastAPI matching "list" as a cn_id
@router.get("/list")
async def list_credit_notes(company_id: str, db=Depends(get_supabase), current_user: dict = Depends(get_current_user)):
    comp_res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", current_user.id).execute()
    if not comp_res.data:
        raise HTTPException(status_code=403, detail="Access denied")
    service = CreditNoteService(db)
    return await service.get_credit_notes(company_id)

@router.get("/{cn_id}")
async def get_credit_note(cn_id: str, company_id: str, db=Depends(get_supabase), current_user: dict = Depends(get_current_user)):
    comp_res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", current_user.id).execute()
    if not comp_res.data:
        raise HTTPException(status_code=403, detail="Access denied")
    service = CreditNoteService(db)
    return await service.get_credit_note(cn_id, company_id)

@router.get("/{cn_id}/pdf")
async def generate_credit_note_pdf(cn_id: str, company_id: str, db=Depends(get_supabase), current_user: dict = Depends(get_current_user)):
    comp_res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", current_user.id).execute()
    if not comp_res.data:
        raise HTTPException(status_code=403, detail="Access denied")
    service = CreditNoteService(db)
    credit_note = await service.get_credit_note(cn_id, company_id)
    if not credit_note:
        raise HTTPException(status_code=404, detail="Credit note not found")

    company_res = db.table("company_profile").select("*").eq("id", company_id).execute()
    if not company_res.data:
        raise HTTPException(status_code=404, detail="Company profile not found")
    company = company_res.data[0]

    # Determine supply type
    company_state_code = company.get('state_code', '')
    customer_state_code = credit_note.get('bill_to_state_code') or credit_note.get('customers', {}).get('state_code', '')
    supply_type = "Intra-state" if company_state_code == customer_state_code else "Inter-state"

    amount_in_words = format_currency_words(credit_note['total_amount'])
    total_tax_words = format_currency_words(credit_note['total_gst'])

    pan = ""
    if company.get("gstin") and len(company["gstin"]) == 15:
        pan = company["gstin"][2:12]

    # Prepare template
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    templates_dir = os.path.join(backend_root, "app", "templates", "credit_notes")
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("credit_note_template.html")

    # Resolve logo and signature paths
    uploads_dir = os.path.join(backend_root, "uploads")
    for key in ["logo_url", "signature_url"]:
        if company.get(key) and "localhost" in company[key]:
            filename = company[key].split("/")[-1]
            local_path = os.path.join(uploads_dir, filename)
            if os.path.exists(local_path):
                company[key] = f"file://{local_path}"

    html_content = template.render(
        company=company,
        credit_note=credit_note,
        items=credit_note['items'],
        supply_type=supply_type,
        amount_in_words=amount_in_words,
        total_tax_words=total_tax_words,
        PAN_NUMBER=pan,
        css="""
        .item-table { border: 1px solid #000; }
        .item-table th { background: #fff; font-size: 10px; font-weight: bold; }
        .item-table td { border-top: none; border-bottom: none; min-height: 25px; }
        .item-table tr.last-row td { border-bottom: 1px solid #000; }
        .item-table tr.total-row td { border-top: 1.5px solid #000; border-bottom: 1.5px solid #000; }
        """
    )

    pdf_bytes = HTML(string=html_content, base_url=backend_root).write_pdf()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=credit_note_{credit_note['credit_note_no']}.pdf"}
    )

@router.delete("/{cn_id}")
async def delete_credit_note(cn_id: str, company_id: str, db=Depends(get_supabase), current_user: dict = Depends(get_current_user)):
    comp_res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", current_user.id).execute()
    if not comp_res.data:
        raise HTTPException(status_code=403, detail="Access denied")
    service = CreditNoteService(db)
    await service.delete_credit_note(cn_id)
    return {"status": "success"}
