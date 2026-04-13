from fastapi import APIRouter, Depends, HTTPException
from ..database import get_supabase
from ..schemas import ProductCreate
from ..auth_utils import get_current_user

router = APIRouter()

async def verify_company_access(company_id: str, user, db):
    res = db.table("company_profile").select("id").eq("id", company_id).eq("user_id", user.id).execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Access to this business profile is denied")

@router.get("/customers")
async def get_customers(company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    res = db.table("customers").select("*").eq("company_id", company_id).execute()
    return res.data

@router.post("/customers")
async def add_customer(customer: dict, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    customer["company_id"] = company_id
    res = db.table("customers").insert(customer).execute()
    return res.data[0]

@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    db.table("customers").delete().eq("id", customer_id).eq("company_id", company_id).execute()
    return {"message": "Client deleted"}

@router.get("/products")
async def get_products(company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    res = db.table("products").select("*").eq("company_id", company_id).execute()
    return res.data

@router.post("/products")
async def add_product(product: ProductCreate, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    data = product.dict()
    data["company_id"] = company_id
    res = db.table("products").insert(data).execute()
    return res.data[0]

@router.delete("/products/{product_id}")
async def delete_product(product_id: str, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    db.table("products").delete().eq("id", product_id).eq("company_id", company_id).execute()
    return {"message": "Product deleted"}

@router.get("/vendors")
async def get_vendors(company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    res = db.table("vendors").select("*").eq("company_id", company_id).execute()
    return res.data

@router.post("/vendors")
async def add_vendor(vendor: dict, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    vendor["company_id"] = company_id
    res = db.table("vendors").insert(vendor).execute()
    return res.data[0]

@router.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: str, company_id: str, user = Depends(get_current_user), db = Depends(get_supabase)):
    await verify_company_access(company_id, user, db)
    db.table("vendors").delete().eq("id", vendor_id).eq("company_id", company_id).execute()
    return {"message": "Vendor deleted"}
