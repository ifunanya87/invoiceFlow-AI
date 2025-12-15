from typing import Any

import pytesseract
from PIL import Image

from ..interface import BaseInvoiceExtractor


class TesseractExtractor(BaseInvoiceExtractor):
    """Extractor for image invoices using Tesseract OCR."""

    def extract_data(self, source: Any) -> str:
        """
        Performs OCR on the image source and then parses the raw text.
        Source can be a file path or a PIL Image object.
        """
        try:
            # Tesseract usually requires a file path or an opened PIL Image
            if isinstance(source, str):
                image = Image.open(source)
            elif isinstance(source, Image.Image):
                image = source
            else:
                raise TypeError("Source must be a file path (str) or a PIL Image.")

            # Perform OCR
            raw_text = pytesseract.image_to_string(image)
        except Exception as e:
            print(f"Error extracting text with Tesseract: {e}")
            return {"error": f"Tesseract failed: {str(e)}", "total_amount": None, "invoice_id": None, "invoice_date": None, "vendor_name": None, "raw_text_length": 0}

        return raw_text
