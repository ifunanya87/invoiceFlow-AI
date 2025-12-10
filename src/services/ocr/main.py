import argparse
import os
from typing import Any, Dict

from src.utils.logging_config import logger

from .factory import InvoiceExtractorFactory


def process_invoice(file_path: str) -> Dict[str, Any]:
    """
    Returns a dictionary containing the raw text extracted from the invoice.
    Uses the InvoiceExtractorFactory to select the correct OCR provider.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File path does not exist: {file_path}")
        return {
            "error": f"File not found: {file_path}",
            "raw_text": None,
            "raw_text_length": 0
        }

    try:
        # Get the appropriate OCR provider instance
        extractor = InvoiceExtractorFactory.get_extractor(file_path)
        logger.info(f"Using OCR provider: {extractor.__class__.__name__} for {file_path}")

        # Extract raw text
        raw_text = InvoiceExtractorFactory.extract(extractor, file_path)

        logger.info(f"OCR extracted {len(raw_text) if raw_text else 0} characters from {file_path}")
        # Return dictionary with raw text and its length
        return {
            "raw_text": raw_text,
            "raw_text_length": len(raw_text) if raw_text else 0
        }

    except Exception as e:
        logger.error(f"FATAL ERROR during invoice processing for {file_path}: {e}", exc_info=True)
        return {
            "error": f"Service failure: {str(e)}",
            "raw_text": None,
            "raw_text_length": 0
        }


def cli():
    parser = argparse.ArgumentParser(description="Process an invoice with OCR.")
    parser.add_argument("file_path", help="Path to the invoice file")

    args = parser.parse_args()
    result = process_invoice(args.file_path)
    logger.info(f"OCR result for {args.file_path}: {result}")
    print(result)


if __name__ == "__main__":
    cli()
