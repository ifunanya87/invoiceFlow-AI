import argparse
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from src.services.ocr.main import process_invoice
from src.utils.logging_config import logger

from .factory import ParserFactory

# Project folders and timestamp
ROOT_FOLDER = Path(__file__).resolve().parent.parent.parent
RESULT_FOLDER = os.path.join(ROOT_FOLDER, "output")
os.makedirs(RESULT_FOLDER, exist_ok=True)

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Valid invoice file extensions
VALID_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}


# Single file parser
def run_parser(file_path: str, parser_name: str = "heuristic") -> Dict[str, Any]:
    logger.info(f"Processing file: {file_path} with parser: {parser_name}")

    ocr_output = process_invoice(file_path)

    # Handle OCR errors
    if ocr_output.error:
        logger.warning(f"OCR error for {file_path}: {ocr_output.error}")
        return {"error": ocr_output.error}

    # Ensure there is content
    if not ocr_output.text and not ocr_output.tables:
        logger.warning(f"OCR returned no content for {file_path}")
        return {"error": "OCR returned no text or tables."}

    parser = ParserFactory.get_parser(parser_name)
    structured = parser.parse(ocr_output)

    # Include raw OCR content length
    raw_length = len(ocr_output.text) if ocr_output.text else 0
    if ocr_output.tables is not None:
        raw_length = len(str(ocr_output.tables))  # crude estimate for table content

    logger.info(f"Parsed {file_path}: {raw_length} characters extracted")

    return {
        "ocr_result": ocr_output.model_dump(),
        "structured_data": structured.model_dump(),
        "raw_text_length": raw_length
    }



# Helper for JSON serialization
def _serialize(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


# Batch parser
def run_batch(path: str, parser_name: str = "heuristic", as_json: bool = True,
    output_file: str = None, save_file: bool = True):

    logger.info(f"Starting batch processing for path: {path}")

    file_paths: List[str] = []

    # Folder mode
    if os.path.isdir(path):
        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            ext = os.path.splitext(f)[1].lower()
            if os.path.isfile(full_path) and ext in VALID_EXTENSIONS:
                file_paths.append(full_path)
        logger.info(f"Found {len(file_paths)} invoice files in folder")

    # File mode
    elif os.path.isfile(path):
        file_paths = [path]

    # Invalid path
    else:
        error = {"error": f"Path does not exist: {path}"}
        logger.error(error["error"])
        return json.dumps(error, indent=4) if as_json else error

    results = []
    for fp in file_paths:
        parsed = run_parser(fp, parser_name)
        results.append({
            "file": os.path.basename(fp),
            "full_path": fp,
            "parser_used": parser_name,
            "ocr_result": parsed["ocr_result"],
            "structured_data": parsed["structured_data"],
            "raw_text_length": parsed.get("raw_text_length", 0)
        })

    # Save batch results to timestamped JSON
    if save_file:
        if output_file is None:
            output_file = os.path.join(RESULT_FOLDER, f"results_{TIMESTAMP}.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, default=_serialize)
        logger.info(f"Saved batch results to {output_file}")

    return results


# CLI
def cli():
    parser = argparse.ArgumentParser(description="Run invoice parser (single or batch mode).")
    parser.add_argument("path", help="Path to an invoice file or a folder of invoices.")
    parser.add_argument(
        "parser_name",
        nargs="?",
        default="heuristic",
        help="Parser to use: heuristic | llm"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Return output as formatted JSON"
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save results to file (useful for debugging)"
    )

    args = parser.parse_args()

    if not args.path:
        parser.error("You must provide a path to a file/folder")

    result = run_batch(
        args.path,
        args.parser_name,
        as_json=args.json,
        save_file=not args.no_save
    )


    if args.json:
        print(json.dumps(result, indent=4, default=_serialize))
    else:
        print(result)


# Entry point
if __name__ == "__main__":
    cli()
