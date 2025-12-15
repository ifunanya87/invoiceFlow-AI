from typing import Any, Optional

from pydantic import BaseModel, Field


class InvoiceParseResult(BaseModel):
    error: Optional[str] = Field(None, description="Error message if parsing failed")

    invoice_id: Optional[str] = Field(None, description="Invoice ID or number")
    vendor_name: Optional[str] = Field(None, description="Vendor or company name")
    invoice_date: Optional[str] = Field(None, description="Invoice date")

    subtotal_amount: Optional[float] = Field(None, description="Subtotal before tax")
    tax_amount: Optional[float] = Field(None, description="Total tax/VAT amount")
    total_amount: Optional[float] = Field(None, description="Final total amount on the invoice")

    summary: Optional[str] = Field(None, description="Short summary of the invoice")
    raw_text_length: int = Field(0, description="Length of the input text")


class OCRResult(BaseModel):
    text: Optional[str] = None
    tables: Optional[Any] = None   # pd.DataFrame, list[dict], Arrow, etc
    raw: Optional[Any] = None      # original provider output
    error: Optional[str] = None
