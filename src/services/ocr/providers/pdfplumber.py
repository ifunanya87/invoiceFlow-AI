from typing import Any, BinaryIO, TextIO, Union

import pdfplumber

from ..interface import BaseInvoiceExtractor

# Define a type hint for common PDF source inputs
PDFSource = Union[str, BinaryIO, TextIO]

class PDFPlumberExtractor(BaseInvoiceExtractor):
    """Extractor for PDF invoices using the pdfplumber library."""

    def extract_data(self, source: PDFSource) -> str:
        """
        Extracts raw text from PDF and then parses it into structured data.
        """
        all_text = []
        try:
            with pdfplumber.open(source) as pdf:
                for page in pdf.pages:
                    # Extract text from the current page
                    page_text = page.extract_text()
                    if page_text:
                        all_text.append(page_text)
        except Exception as e:
            print(f"Error extracting text with PDFPlumber: {e}")
            return {"error": f"PDFPlumber failed: {str(e)}", "total_amount": None, "invoice_id": None, "invoice_date": None, "vendor_name": None, "raw_text_length": 0}

        raw_text = "\n".join(all_text)
        return raw_text
