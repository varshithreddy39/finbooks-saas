from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date as dt_date

# Auth
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str
    mobile: str
    gstin: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordReset(BaseModel):
    email: EmailStr

# Company (now company_profile)
class CompanyBase(BaseModel):
    company_name: str
    gstin: str
    address: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    primary_email: EmailStr
    secondary_email: Optional[str] = None
    phone: str # Primary Mobile
    additional_phone: Optional[str] = None
    bank_details: Optional[dict] = None
    invoice_settings: Optional[dict] = None
    logo_url: Optional[str] = None
    signature_url: Optional[str] = None
    authorised_signatory: Optional[str] = None
    user_id: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

# Product
class ProductBase(BaseModel):
    name: str
    sku: Optional[str] = None
    hsn_sac: str
    default_gst_rate: float = 18.0
    sales_price: float
    unit: str = "PCS"
    opening_stock: float = 0

class ProductCreate(ProductBase):
    pass

# Invoice
class InvoiceItemBase(BaseModel):
    product_id: str
    qty: float
    rate: float
    gst_rate: float
    description: Optional[str] = None

class InvoiceBase(BaseModel):
    customer_id: str
    invoice_no: str
    invoice_date: dt_date = dt_date.today()
    supply_type: str
    reverse_charge: bool = False
    vehicle_no: Optional[str] = None
    eway_bill: Optional[str] = None
    purchase_order_no: Optional[str] = None
    trans_mode: Optional[str] = None
    bill_to_name: Optional[str] = None
    bill_to_address: Optional[str] = None
    bill_to_gstin: Optional[str] = None
    bill_to_state: Optional[str] = None
    bill_to_state_code: Optional[str] = None
    ship_to_name: Optional[str] = None
    ship_to_gstin: Optional[str] = None
    ship_to_address: Optional[str] = None
    ship_to_state: Optional[str] = None
    ship_to_state_code: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    authorised_signatory: Optional[str] = None
    items: List[InvoiceItemBase]

class InvoiceCreate(InvoiceBase):
    pass

# Quotation
class QuotationItemBase(BaseModel):
    product_id: str
    qty: float
    rate: float
    gst_rate: float
    description: Optional[str] = None

class QuotationBase(BaseModel):
    customer_id: str
    quotation_no: str
    date: dt_date = dt_date.today()
    valid_until: Optional[dt_date] = None
    bill_to_name: Optional[str] = None
    bill_to_address: Optional[str] = None
    bill_to_gstin: Optional[str] = None
    bill_to_state: Optional[str] = None
    bill_to_state_code: Optional[str] = None
    ship_to_name: Optional[str] = None
    ship_to_gstin: Optional[str] = None
    ship_to_address: Optional[str] = None
    ship_to_state: Optional[str] = None
    ship_to_state_code: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    authorised_signatory: Optional[str] = None
    items: List[QuotationItemBase]

class QuotationCreate(QuotationBase):
    pass

# Credit Note
class CreditNoteItemBase(BaseModel):
    product_id: str
    qty: float
    rate: float
    gst_rate: float
    description: Optional[str] = None

class CreditNoteBase(BaseModel):
    customer_id: str
    credit_note_no: str
    date: dt_date = dt_date.today()
    vehicle_no: Optional[str] = None
    eway_bill_no: Optional[str] = None
    dispatched_through: Optional[str] = None
    destination: Optional[str] = None
    reason: Optional[str] = None
    invoice_no: Optional[str] = None
    status: Optional[str] = "Issued"
    bill_to_name: Optional[str] = None
    bill_to_address: Optional[str] = None
    bill_to_gstin: Optional[str] = None
    bill_to_state: Optional[str] = None
    bill_to_state_code: Optional[str] = None
    authorised_signatory: Optional[str] = None
    items: List[CreditNoteItemBase]

class CreditNoteCreate(CreditNoteBase):
    pass
