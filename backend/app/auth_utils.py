from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .database import get_supabase
from supabase import Client

security = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security), db: Client = Depends(get_supabase)):
    try:
        # Supabase get_user verifies the JWT automatically
        user_res = db.auth.get_user(token.credentials)
        if not user_res.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return user_res.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )
