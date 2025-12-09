import re
from typing import Dict, Optional

from ..interface import BaseParser, InvoiceData


class HeuristicParser(BaseParser):
    """
    Handles:
    - Invoice ID
    - Total amount
    - Vendor block extraction
    - Date
    """


    # Main Parse
    def parse(self, raw_text: str) -> InvoiceData:
        if not raw_text:
            return {
                "error": "No text provided for parsing",
                "invoice_id": None,
                "total_amount": None,
                "invoice_date": None,
                "vendor_name": None,
                "raw_text_length": 0,
            }

        return {
            "error": None,
            "invoice_id": self.extract_invoice_id(raw_text),
            "total_amount": self.extract_total_amount(raw_text),
            "invoice_date": self.extract_invoice_date(raw_text),
            "vendor_name": self.extract_vendor(raw_text),
            "raw_text_length": len(raw_text),
        }


    # Invoice ID
    def extract_invoice_id(self, text: str) -> Optional[str]:
        """
        Avoid false positives like "Invoice" -> "oice".
        Extracts IDs following: Invoice No:, Invoice #, INV:, Ref:, ID:
        """
        patterns = [
            r"(?:invoice|inv)[\s]*?(?:no\.?|number|num|#)?[\s:]*([A-Z0-9][A-Z0-9\-/]{3,30})",
            r"(?:ref|reference)[\s#:.]*([A-Z0-9][A-Z0-9\-/]{3,30})",
            r"\bid[\s#:.]+([A-Z0-9][A-Z0-9\-/]{3,30})",
        ]

        for p in patterns:
            m = re.search(p, text, flags=re.IGNORECASE)
            if m:
                candidate = m.group(1)
                # Reject substrings of 'invoice'
                if candidate.lower() in ["voice", "oice", "nvoice"]:
                    continue
                return candidate
        return None


    # Total Amount
    def extract_total_amount(self, text: str) -> Optional[float]:
        """
        Extract total amount with support for:
        - $194.82
        - €194,82
        - 1,234.56
        - 1.234,56
        Uses the LAST matching total-like value.
        """

        total_patterns = [
            r"(?:total|amount\s*due|grand\s*total|balance)[^\n]*?([\$€£]?\s*[0-9.,]+)",
        ]

        amounts = []

        for p in total_patterns:
            for match in re.finditer(p, text, flags=re.IGNORECASE):
                raw = match.group(1)
                cleaned = re.sub(r"[^\d,\.]", "", raw)

                # Convert comma-decimal formats
                if cleaned.count(",") == 1 and cleaned.count(".") == 0:
                    cleaned = cleaned.replace(",", ".")

                # Remove thousand separators
                if cleaned.count(",") > 1:
                    cleaned = cleaned.replace(",", "")

                try:
                    amounts.append(float(cleaned))
                except:
                    pass

        if amounts:
            return amounts[-1]  # take last occurrence

        # Fallback: capture all currency-like numbers in entire document
        fallback = re.findall(r"[\$€£]?\s*[0-9][0-9.,]+", text)
        for raw in reversed(fallback):
            cleaned = re.sub(r"[^\d,\.]", "", raw)
            if cleaned.count(",") == 1 and cleaned.count(".") == 0:
                cleaned = cleaned.replace(",", ".")
            try:
                return float(cleaned)
            except:
                continue

        return None


    # Invoice Date
    def extract_invoice_date(self, text: str) -> Optional[str]:
        patterns = [
            r"\b\d{4}[-/]\d{2}[-/]\d{2}\b",
            r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4}\b",
        ]
        for p in patterns:
            m = re.search(p, text, flags=re.IGNORECASE)
            if m:
                return m.group(0)
        return None


    # Vendor Extraction
    def extract_vendor(self, text: str) -> Optional[str]:
        """
        Look for labelled blocks: Seller:, Vendor:, From:, Client:
        Capture the first non-empty line inside that block.
        If nothing found, fall back to non-keyword lines.
        """

        block_patterns = [
            r"Seller:\s*(.*?)(?:Client:|Tax|IBAN|Items|ITEMS|\n\n|$)",
            r"Vendor:\s*(.*?)(?:Client:|Tax|IBAN|Items|ITEMS|\n\n|$)",
            r"From:\s*(.*?)(?:Client:|Tax|IBAN|Items|ITEMS|\n\n|$)",
            r"Client:\s*(.*?)(?:Tax|IBAN|Items|ITEMS|\n\n|$)",
        ]

        for p in block_patterns:
            m = re.search(p, text, flags=re.IGNORECASE | re.DOTALL)
            if m:
                block = m.group(1)
                lines = [l.strip() for l in block.split("\n") if l.strip()]
                if lines:
                    return lines[0]

        # Fallback: pick first useful line among first 8 lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:8]:
            if not re.search(
                r"(invoice|date|total|amount|due|balance|id|ref|item|qty|net|vat)",
                line,
                re.I,
            ):
                return line

        return lines[0] if lines else None
