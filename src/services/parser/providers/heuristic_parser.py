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

    MIN_AMOUNT = 5

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
        forbidden = {
            "invoice", "invoice number", "invoice no", "inv",
            "number", "no", "id"
        }

        patterns = [
            # Same line:ABC-123
            r"(?:invoice|inv)[\s]*?(?:no\.?|number|num|#)?[\s:]*([A-Z0-9][A-Z0-9\-/]{3,40})",

            # Multi-line:ABC-123
            r"(?:invoice|inv)[\s]*?(?:no\.?|number|num|#)?\s*[:\n]+\s*([A-Z0-9][A-Z0-9\-/]{3,40})",

            # Same line Ref
            r"(?:ref|reference)[\s#:.]*([A-Z0-9][A-Z0-9\-/]{3,40})",

            # Multi-line Ref
            r"(?:ref|reference)[\s#:.]*\n\s*([A-Z0-9][A-Z0-9\-/]{3,40})",

            # ID
            r"\bid[\s#:.]+([A-Z0-9][A-Z0-9\-/]{3,40})",
            r"\bid\s*[:\n]+\s*([A-Z0-9][A-Z0-9\-/]{3,40})",
        ]

        for p in patterns:
            m = re.search(p, text, flags=re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()

                # Reject common header/garbage tokens
                if candidate.lower() in forbidden:
                    continue

                # Reject OCR fragments of "invoice"
                if candidate.lower() in ["voice", "oice", "nvoice"]:
                    continue

                # Must contain at least one digit to be an invoice number
                if not re.search(r"\d", candidate):
                    continue

                return candidate

        # Detect stand-alone invoice numbers on the next line after a label
        lines = [ln.strip() for ln in text.splitlines()]

        for i, line in enumerate(lines):
            if re.search(r"invoice\s*(number|no|#)?", line, re.IGNORECASE):
                # search forward only a few lines (avoid totals, items)
                for j in range(i+1, min(i+5, len(lines))):
                    candidate = lines[j]
                    # skip empty
                    if not candidate:
                        continue
                    # skip dates
                    if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b|\d{1,2}/\d{1,2}/\d{4}", candidate, re.IGNORECASE):
                        continue
                    # must contain a digit
                    if not re.search(r"\d", candidate):
                        continue
                    # skip money
                    if re.search(r"[$€£]", candidate):
                        continue
                    # avoid pure 2–3 digit numbers (likely item IDs)
                    if re.fullmatch(r"\d{1,3}", candidate):
                        continue
                    # allow typical invoice ID patterns
                    if re.fullmatch(r"[A-Z0-9\-/]{3,40}", candidate):
                        return candidate

        return None



    # Total Amount
    def extract_total_amount(self, text: str) -> Optional[float]:
        """
        Extract the single grand total amount by capturing the entire numerical summary block
        (Subtotal, Tax, Shipping, Grand Total) and returning the maximum valid amount found.
        """
        amounts: List[float] = []

        # Keywords to anchor the start of the total section (Subtotal is often the first)
        keywords = r"(?:subtotal|total|amount\s*due|grand\s*total|balance|summary|TOTAL\s*DUE)"

        # Find the first relevant keyword and capture everything that follows
        total_cluster_pattern = rf"({keywords}.*)"

        # Find the entire rest of the document after the first keyword
        match = re.search(total_cluster_pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            # group 1 contains the raw text of the entire summary block
            summary_block = match.group(1)

            # Extract and Normalize: Find all money-like numbers within the captured block
            numbers = re.findall(r"[\$€£]?\s*[0-9][0-9.,]*", summary_block)

            for raw in numbers:
                normalized = self._normalize_money(raw)

                if normalized is not None:
                    amounts.append(normalized)

        # Return the largest amount found
        if amounts:
            return max(amounts)

        return None

    def _normalize_money(self, raw: str) -> Optional[float]:
        """
        Normalize money strings into float, applying cleanup, conversion, and rejection logic.
        """
        # Remove all characters that are NOT a digit, comma, or period.
        cleaned = re.sub(r"[^\d,\.]", "", raw)

        # Reject if three or more commas or periods are used
        if cleaned.count(",") >= 3 or cleaned.count(".") >= 3:
            return None

        # Reject ambiguous US/EU mix: multiple commas/periods
        if cleaned.count(",") >= 1 and cleaned.count(".") > 1:
            if cleaned.rfind('.') > cleaned.rfind(','):
                return None


        # European Thousands Conversion: "1.234.567,89" -> "1234567.89"
        if cleaned.count(".") > 1 and cleaned.count(",") == 1:
            # Ensure comma appears AFTER the rightmost period
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace(".", "").replace(",", ".")

        # US Thousands Removal: "1,234.56" -> "1234.56"
        if cleaned.count(",") > 1:
            cleaned = cleaned.replace(",", "")

        # Only if there is exactly one comma and no periods: "194,82" -> "194.82"
        if cleaned.count(",") == 1 and cleaned.count(".") == 0:
            cleaned = cleaned.replace(",", ".")

        # Cast to Float
        try:
            return float(cleaned)
        except ValueError:
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
        Extracts the vendor name from invoice text.
        """

        forbidden_keywords = [
            r"invoice", r"date", r"total", r"amount", r"due", r"balance",
            r"id", r"ref", r"item", r"qty", r"net", r"vat",
            r"bill\s*to", r"bill\s*from"
        ]

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
                lines = [l.strip() for l in block.splitlines() if l.strip()]
                for line in lines:
                    # Skip numeric-only lines
                    if re.fullmatch(r"\d+", line):
                        continue
                    # Skip invoice ID patterns
                    if re.fullmatch(r"[A-Z0-9\-]{4,30}", line):
                        continue

                    if any(re.search(k, line, re.I) for k in forbidden_keywords):
                        continue
                    return line

        # Check for BILL FROM / FROM patterns
        bill_patterns = [
            r"BILL FROM\s*[:\n]*\s*(.*?)(?:BILL TO|Client:|Tax|IBAN|Items|ITEMS|\n\n|$)",
            r"FROM\s*[:\n]*\s*(.*?)(?:Client:|Tax|IBAN|Items|ITEMS|\n\n|$)",
        ]

        for p in bill_patterns:
            m = re.search(p, text, flags=re.IGNORECASE | re.DOTALL)
            if m:
                block = m.group(1)
                lines = [l.strip() for l in block.splitlines() if l.strip()]
                for line in lines:
                    if re.fullmatch(r"\d+", line):
                        continue
                    if re.fullmatch(r"[A-Z0-9\-]{4,30}", line):
                        continue
                    if any(re.search(k, line, re.I) for k in forbidden_keywords):
                        continue
                    return line

        # Fallback: scan first 20 lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:20]:
            if re.fullmatch(r"\d+", line):
                continue
            if re.fullmatch(r"[A-Z0-9\-]{4,30}", line):
                continue
            if any(re.search(k, line, re.I) for k in forbidden_keywords):
                continue
            return line


        return lines[0] if lines else None
