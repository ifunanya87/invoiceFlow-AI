import argparse
import os
from typing import Any, Dict

from src.models.models import OCRResult
from src.utils.logging_config import logger

from .factory import InvoiceExtractorFactory


def process_invoice(file_path: str) -> OCRResult:
    """
    Runs OCR on the invoice and returns an OCRResult
    """
    if not os.path.exists(file_path):
        logger.warning(f"File path does not exist: {file_path}")
        return {
            "error": f"File not found: {file_path}"
        }

    try:
        extractor = InvoiceExtractorFactory.get_extractor(file_path)
        logger.info(
            f"Using OCR provider: {extractor.__class__.__name__} for {file_path}"
        )

        ocr_result = InvoiceExtractorFactory.extract(extractor, file_path)

        if not isinstance(ocr_result, OCRResult):
            raise TypeError(
                f"OCR extractor returned invalid type: {type(ocr_result)}"
            )

        logger.info(
            f"OCR completed for {file_path} | "
            f"text={'yes' if ocr_result.text else 'no'} | "
            f"tables={'yes' if ocr_result.tables is not None else 'no'}"
        )

        return ocr_result

    except Exception as e:
        logger.error(
            f"FATAL ERROR during invoice processing for {file_path}: {e}",
            exc_info=True
        )
        return OCRResult(error="File not found")


def cli():
    parser = argparse.ArgumentParser(description="Process an invoice with OCR.")
    parser.add_argument("file_path", help="Path to the invoice file")
    args = parser.parse_args()

    result = process_invoice(args.file_path)

    if isinstance(result, OCRResult):
        print("=== OCR RESULT ===")
        print(f"Text present: {bool(result.text)}")
        print(f"Tables present: {result.tables is not None}")

        if result.text:
            print("\n--- TEXT ---")
            print(result.text)

        if result.tables is not None:
            print("\n--- TABLE PREVIEW ---")
            print(result.tables.head() if hasattr(result.tables, "head") else result.tables)

    else:
        print("ERROR:", result)



if __name__ == "__main__":
    cli()
