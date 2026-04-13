from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from ..schemas import QuotationCreate
from ..database import get_supabase
from ..services.quotation_service import QuotationService
from ..auth_utils import get_current_user
from jinja2 import Environment, FileSystemLoader
import os
import tempfile
from num2words import num2words

router = APIRouter()

async def verify_company_access(company_id: str, user, db):
    res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", user.id).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Access to this business profile is denied")

@router.post("/create")
async def create_quotation(quotation_data: QuotationCreate, company_id: str, db=Depends(get_supabase), current_user=Depends(get_current_user)):
    await verify_company_access(company_id, current_user, db)
    service = QuotationService(db)
    return await service.create_quotation(quotation_data, company_id)

@router.get("/")
async def list_quotations(company_id: str, db=Depends(get_supabase), current_user=Depends(get_current_user)):
    await verify_company_access(company_id, current_user, db)
    service = QuotationService(db)
    return await service.list_quotations(company_id)

@router.get("/{quotation_id}")
async def get_quotation(quotation_id: str, company_id: str, db=Depends(get_supabase), current_user=Depends(get_current_user)):
    await verify_company_access(company_id, current_user, db)
    service = QuotationService(db)
    return await service.get_quotation(quotation_id, company_id)

@router.put("/{quotation_id}")
async def update_quotation(quotation_id: str, quotation_data: QuotationCreate, company_id: str, db=Depends(get_supabase), current_user=Depends(get_current_user)):
    await verify_company_access(company_id, current_user, db)
    service = QuotationService(db)
    return await service.update_quotation(quotation_id, quotation_data, company_id)

@router.get("/{quotation_id}/pdf")
async def generate_quotation_pdf(quotation_id: str, company_id: str, db=Depends(get_supabase), current_user=Depends(get_current_user)):
    await verify_company_access(company_id, current_user, db)
    try:
        service = QuotationService(db)
        quotation = await service.get_quotation(quotation_id, company_id)
        
        company_res = db.table("company_profile").select("*").eq("id", company_id).execute()
        if not company_res.data:
            raise HTTPException(status_code=404, detail="Company profile not found")
        company = company_res.data[0]
        
        items = quotation["items"]
        
        def format_currency_words(amount):
            try:
                whole = int(amount)
                fraction = int(round((amount - whole) * 100))
                words = num2words(whole, lang='en_IN').title() + " Rupees"
                if fraction > 0:
                    words += " And " + num2words(fraction, lang='en_IN').title() + " Paise"
                return words + " Only"
            except:
                return num2words(amount, lang='en_IN').title() + " Only"
                
        amount_words = format_currency_words(quotation["total_amount"])
        
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        templates_dir = os.path.join(backend_root, "app", "templates", "quotations")
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template("quotation_template.html")
        
        uploads_dir = os.path.join(backend_root, "uploads")
        import base64, mimetypes
        for key in ["logo_url", "signature_url"]:
            if company.get(key) and "localhost" in company[key]:
                filename = company[key].split("/")[-1]
                local_path = os.path.join(uploads_dir, filename)
                if os.path.exists(local_path):
                    mime = mimetypes.guess_type(local_path)[0] or "image/png"
                    with open(local_path, "rb") as img_f:
                        b64 = base64.b64encode(img_f.read()).decode()
                    company[key] = f"data:{mime};base64,{b64}"

        pan = ""
        if company.get("gstin") and len(company["gstin"]) == 15:
            pan = company["gstin"][2:12]

        seller_state_code = company.get("state_code", "")
        buyer_state_code = quotation.get("bill_to_state_code", "")
        supply_type = "Intra-state" if seller_state_code == buyer_state_code else "Inter-state"

        html_content = template.render(
            company=company,
            quotation=quotation,
            items=items,
            amount_in_words=amount_words,
            PAN_NUMBER=pan,
            supply_type=supply_type
        )

        # Use Playwright (Chromium) for pixel-perfect PDF rendering
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="networkidle")
            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
            )
            await browser.close()

        return Response(content=pdf_bytes, media_type="application/pdf")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate PDF: {str(e)}")

@router.delete("/{quotation_id}")
async def delete_quotation(quotation_id: str, company_id: str, db=Depends(get_supabase), current_user=Depends(get_current_user)):
    await verify_company_access(company_id, current_user, db)

    latest = db.table("quotations").select("id").eq("company_id", company_id).order("created_at", desc=True).limit(1).execute()
    if latest.data and latest.data[0]["id"] == quotation_id:
        comp = db.table("company_profile").select("invoice_settings").eq("id", company_id).execute()
        if comp.data:
            settings = comp.data[0].get("invoice_settings") or {}
            if settings.get("last_quo_used", 0) > 0:
                settings["last_quo_used"] -= 1
                db.table("company_profile").update({"invoice_settings": settings}).eq("id", company_id).execute()

    db.table("quotation_items").delete().eq("quotation_id", quotation_id).execute()
    db.table("quotations").delete().eq("id", quotation_id).eq("company_id", company_id).execute()
    return {"message": "Quotation deleted"}
