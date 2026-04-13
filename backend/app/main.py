from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .routers import auth, company, invoice, masters, quotation, credit_note

app = FastAPI(title="Finbooks API", version="1.0.0")

# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# CORS — allow all origins in dev; restrict via ALLOWED_ORIGINS env var in production
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = allowed_origins_env.split(",") if allowed_origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for uploaded logos
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return {"message": "Finbooks API is running"}

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(company.router, prefix="/api/company", tags=["Company"])
app.include_router(invoice.router, prefix="/api/invoices", tags=["Invoicing"])
app.include_router(masters.router, prefix="/api/masters", tags=["Master Data"])
app.include_router(quotation.router, prefix="/api/quotations", tags=["Quotations"])
app.include_router(credit_note.router, prefix="/api/credit-notes", tags=["Credit Notes"])
