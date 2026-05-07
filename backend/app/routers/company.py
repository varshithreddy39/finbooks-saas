from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import os
import uuid
import httpx
from ..database import get_supabase
from ..schemas import CompanyCreate
from ..auth_utils import get_current_user

router = APIRouter()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def get_public_url(bucket: str, path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"

async def upload_to_supabase(bucket: str, filename: str, contents: bytes, content_type: str) -> str:
    """Upload file to Supabase Storage using REST API directly — more reliable than SDK."""
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{filename}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": content_type,
        "x-upsert": "true"  # overwrite if exists
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, content=contents, headers=headers)
        if resp.status_code not in (200, 201):
            raise Exception(f"Storage upload failed: {resp.status_code} {resp.text}")
    return get_public_url(bucket, filename)

@router.get("/profile")
async def get_profile(company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    res = db.table("company_profile").select("*").eq("id", company_id).eq("user_id", user.id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return res.data

@router.get("/profile/mine")
async def get_my_profile(user = Depends(get_current_user), db = Depends(get_supabase)):
    res = db.table("company_profile").select("*").eq("user_id", user.id).execute()
    if not res.data:
        legacy = db.table("company_profile").select("*").eq("primary_email", user.email).execute()
        if legacy.data and legacy.data[0]["user_id"] is None:
            db.table("company_profile").update({"user_id": user.id}).eq("id", legacy.data[0]["id"]).execute()
            return legacy.data[0]
        raise HTTPException(status_code=404, detail="Company profile not found")
    return res.data[0]

@router.post("/setup")
async def setup_company(company: CompanyCreate, user = Depends(get_current_user), db = Depends(get_supabase)):
    comp_dict = company.dict(exclude_unset=True)
    comp_dict["user_id"] = str(user.id)

    existing = db.table("company_profile").select("id, gstin, primary_email").eq("user_id", user.id).execute()

    if not existing.data:
        legacy = db.table("company_profile").select("id").eq("primary_email", company.primary_email or user.email).execute()
        if legacy.data:
            comp_dict.pop("gstin", None)
            comp_dict.pop("primary_email", None)
            res = db.table("company_profile").update(comp_dict).eq("id", legacy.data[0]["id"]).execute()
        else:
            res = db.table("company_profile").insert(comp_dict).execute()
    else:
        comp_dict.pop("gstin", None)
        comp_dict.pop("primary_email", None)
        res = db.table("company_profile").update(comp_dict).eq("user_id", user.id).execute()

    return res.data[0]

@router.post("/upload-logo")
async def upload_logo(company_id: str, file: UploadFile = File(...), db = Depends(get_supabase)):
    ext = os.path.splitext(file.filename or "logo.png")[1] or ".png"
    filename = f"{company_id}_{uuid.uuid4()}{ext}"
    contents = await file.read()
    content_type = file.content_type or "image/png"

    try:
        logo_url = await upload_to_supabase("logos", filename, contents, content_type)
        print(f"Logo uploaded to Supabase: {logo_url}")
    except Exception as e:
        print(f"Supabase storage upload failed for logo: {e}")
        raise HTTPException(status_code=500, detail=f"Logo upload failed: {str(e)}")

    db.table("company_profile").update({"logo_url": logo_url}).eq("id", company_id).execute()
    return {"logo_url": logo_url}

@router.post("/upload-signature")
async def upload_signature(company_id: str, file: UploadFile = File(...), db = Depends(get_supabase)):
    ext = os.path.splitext(file.filename or "sig.png")[1] or ".png"
    filename = f"sig_{company_id}_{uuid.uuid4()}{ext}"
    contents = await file.read()
    content_type = file.content_type or "image/png"

    try:
        signature_url = await upload_to_supabase("signatures", filename, contents, content_type)
        print(f"Signature uploaded to Supabase: {signature_url}")
    except Exception as e:
        print(f"Supabase storage upload failed for signature: {e}")
        raise HTTPException(status_code=500, detail=f"Signature upload failed: {str(e)}")

    db.table("company_profile").update({"signature_url": signature_url}).eq("id", company_id).execute()
    return {"signature_url": signature_url}
