import pandas as pd

from src.models.models import InvoiceParseResult
from src.services.parser.interface import BaseParser


class HeuristicTableParser(BaseParser):
    """
    Parses OCR table DataFrame (with bounding boxes).
    """

    def parse(self, table_df: pd.DataFrame) -> InvoiceParseResult:
        if table_df is None or table_df.empty:
            return InvoiceParseResult(
                error="Empty OCR table",
                raw_text_length=0
            )

        # Placeholder logic
        return InvoiceParseResult(
            error=None,
            invoice_id=None,
            vendor_name=None,
            invoice_date=None,
            subtotal_amount=None,
            tax_amount=None,
            total_amount=None,
            summary={
                "num_cells": len(table_df),
                "columns": list(table_df.columns),
            },
            raw_text_length=len(table_df)
        )
