from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import shutil
import os
import uuid
from ..database import get_supabase
from ..schemas import CompanyCreate
from ..auth_utils import get_current_user

router = APIRouter()

@router.get("/profile")
async def get_profile(company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    res = db.table("company_profile").select("*").eq("id", company_id).eq("user_id", user.id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return res.data

@router.get("/profile/mine")
async def get_my_profile(user = Depends(get_current_user), db = Depends(get_supabase)):
    # 1. Try finding by user_id
    res = db.table("company_profile").select("*").eq("user_id", user.id).execute()
    
    if not res.data:
        # 2. Healing: Try finding by email if user_id is missing
        legacy = db.table("company_profile").select("*").eq("primary_email", user.email).execute()
        if legacy.data and legacy.data[0]["user_id"] is None:
            # Claim it
            db.table("company_profile").update({"user_id": user.id}).eq("id", legacy.data[0]["id"]).execute()
            return legacy.data[0]
        raise HTTPException(status_code=404, detail="Company profile not found")
    return res.data[0]

@router.post("/setup")
async def setup_company(company: CompanyCreate, user = Depends(get_current_user), db = Depends(get_supabase)):
    comp_dict = company.dict(exclude_unset=True)
    comp_dict["user_id"] = str(user.id)
    
    # 1. Try finding by user_id
    existing = db.table("company_profile").select("id, gstin, primary_email").eq("user_id", user.id).execute()
    
    if not existing.data:
        # 2. Healing: Try finding by email
        legacy = db.table("company_profile").select("id").eq("primary_email", company.primary_email or user.email).execute()
        if legacy.data:
            # LOCK: Do not allow changing GSTIN or Primary Email during setup if claiming legacy
            comp_dict.pop("gstin", None)
            comp_dict.pop("primary_email", None)
            res = db.table("company_profile").update(comp_dict).eq("id", legacy.data[0]["id"]).execute()
        else:
            res = db.table("company_profile").insert(comp_dict).execute()
    else:
        # 3. Regular Update - LOCK sensitive fields
        comp_dict.pop("gstin", None)
        comp_dict.pop("primary_email", None)
        res = db.table("company_profile").update(comp_dict).eq("user_id", user.id).execute()
        
    return res.data[0]

@router.post("/upload-logo")
async def upload_logo(company_id: str, file: UploadFile = File(...), db = Depends(get_supabase)):
    # 1. Create unique filename
    ext = os.path.splitext(file.filename)[1]
    filename = f"{company_id}_{uuid.uuid4()}{ext}"
    file_path = f"uploads/{filename}"
    
    # 2. Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 3. Update company record
    logo_url = f"http://localhost:8001/uploads/{filename}"
    db.table("company_profile").update({"logo_url": logo_url}).eq("id", company_id).execute()
    
    return {"logo_url": logo_url}
    
@router.post("/upload-signature")
async def upload_signature(company_id: str, file: UploadFile = File(...), db = Depends(get_supabase)):
    # 1. Create unique filename
    ext = os.path.splitext(file.filename)[1]
    filename = f"sig_{company_id}_{uuid.uuid4()}{ext}"
    file_path = f"uploads/{filename}"
    
    # 2. Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 3. Update company record
    signature_url = f"http://localhost:8001/uploads/{filename}"
    db.table("company_profile").update({"signature_url": signature_url}).eq("id", company_id).execute()
    
    return {"signature_url": signature_url}
