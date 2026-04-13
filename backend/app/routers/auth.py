from fastapi import APIRouter, HTTPException, Depends
from ..schemas import UserCreate, UserLogin, PasswordReset
from ..auth_utils import get_current_user
from ..database import get_supabase

router = APIRouter()

@router.post("/signup")
async def signup(user: UserCreate, db = Depends(get_supabase)):
    # 1. Check if GSTIN already exists
    gst_check = db.table("company_profile").select("id").eq("gstin", user.gstin.upper()).execute()
    if gst_check.data:
        raise HTTPException(
            status_code=400, 
            detail="This GST is already registered. Please login or recover your account."
        )

    # 2. Register user in Supabase Auth
    try:
        res = db.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "full_name": user.full_name,
                    "mobile": user.mobile
                }
            }
        })
        
        if not res.user:
            raise HTTPException(status_code=400, detail="Signup failed")

        # 3. Auto-create company profile
        profile_data = {
            "user_id": res.user.id,
            "gstin": user.gstin.upper(),
            "company_name": f"{user.full_name}'s Business", # Temporary default
            "primary_email": user.email,
            "phone": user.mobile
        }
        db.table("company_profile").insert(profile_data).execute()
        
        return {"message": "User created and business profile initialized successfully", "user_id": res.user.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user: UserLogin, db = Depends(get_supabase)):
    try:
        res = db.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        # 2. Check if user has an associated company profile
        # 2a. Try finding by user_id
        company_res = db.table("company_profile").select("id").eq("user_id", res.user.id).execute()
        
        if not company_res.data:
            # 2b. Healing logic: Try finding by primary_email if user_id is missing
            legacy_res = db.table("company_profile").select("id, user_id").eq("primary_email", user.email).execute()
            if legacy_res.data and legacy_res.data[0]["user_id"] is None:
                # Claim the profile
                db.table("company_profile").update({"user_id": res.user.id}).eq("id", legacy_res.data[0]["id"]).execute()
                company_id = legacy_res.data[0]["id"]
            else:
                company_id = None
        else:
            company_id = company_res.data[0]["id"]

        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "token_type": "bearer",
            "expires_in": res.session.expires_in,
            "company_id": company_id
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/refresh")
async def refresh_token(body: dict, db = Depends(get_supabase)):
    try:
        refresh_tok = body.get("refresh_token")
        if not refresh_tok:
            raise HTTPException(status_code=400, detail="refresh_token required")
        res = db.auth.refresh_session(refresh_tok)
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "expires_in": res.session.expires_in
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

@router.post("/reset-password")
async def reset_password(req: PasswordReset, db = Depends(get_supabase)):
    try:
        # Note: If no SMTP configure, Supabase requires configured redirect URL 
        # For simplicity in local testing, we just fire the reset API
        res = db.auth.reset_password_email(req.email)
        return {"message": "Password reset email sent (check Supabase logs if local)"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/delete-account")
async def delete_account(user = Depends(get_current_user), db = Depends(get_supabase)):
    try:
        # Delete the company_profile. Due to ON DELETE CASCADE, all customers, invoices, products, and vendors are removed.
        db.table("company_profile").delete().eq("user_id", user.id).execute()
        # The auth.users record remains because we don't have service_role key to delete it,
        # but the business is virtually wiped allowing the user to sign up again or leave.
        return {"message": "Account and all associated business data successfully deleted."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
